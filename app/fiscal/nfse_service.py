"""Servicos da nova fundacao NFS-e.

Nenhuma funcao deste modulo transmite NFS-e.
Nenhuma funcao deste modulo gera lancamento financeiro.
"""

from sqlalchemy.exc import IntegrityError

from app.extensoes import db
from app.fiscal.configuracao_fiscal_model import ConfiguracaoFiscal
from app.fiscal.nfse_documento_model import (
    AMBIENTES_NFSE,
    NfseDocumento,
)
from app.ordem_servico.ordem_servico_model import OrdemServico


class ConflitoIdempotencia(ValueError):
    """A mesma chave foi reutilizada para outro contexto fiscal."""


class PreparacaoNfseInvalida(ValueError):
    """A OS ou a configuracao nao permite preparar a NFS-e."""


def gerar_chave_emissao_original(ordem_servico_id: int) -> str:
    """Chave deterministica para a primeira intencao NFS-e de uma OS."""
    return f"nfse:os:{ordem_servico_id}:emissao:original"


def _normalizar_provider(provider):
    if provider is None:
        return None

    valor = str(provider).strip()
    return valor or None


def _validar_documento_existente(
    documento: NfseDocumento,
    *,
    ordem_servico_id: int,
    configuracao_fiscal_id: int,
    ambiente: str,
    provider,
) -> None:
    """Impede reutilizacao da chave para outra intencao fiscal."""

    provider_normalizado = _normalizar_provider(provider)

    mesmo_contexto = (
        documento.ordem_servico_id == ordem_servico_id
        and documento.configuracao_fiscal_id == configuracao_fiscal_id
        and documento.ambiente == ambiente
        and documento.provider == provider_normalizado
    )

    if not mesmo_contexto:
        raise ConflitoIdempotencia(
            "chave_idempotencia ja associada "
            "a contexto fiscal diferente"
        )


def obter_ou_criar_rascunho(
    *,
    ordem_servico_id: int,
    configuracao_fiscal_id: int,
    chave_idempotencia: str,
    ambiente: str = "HOMOLOGACAO",
    provider: str | None = None,
) -> tuple[NfseDocumento, bool]:
    """Retorna a intencao existente ou cria um unico rascunho."""

    chave = (chave_idempotencia or "").strip()

    if not chave:
        raise ValueError("chave_idempotencia e obrigatoria")

    if len(chave) > 160:
        raise ValueError(
            "chave_idempotencia excede 160 caracteres"
        )

    ambiente_normalizado = (ambiente or "").strip().upper()

    if ambiente_normalizado not in AMBIENTES_NFSE:
        raise ValueError("ambiente fiscal invalido")

    provider_normalizado = _normalizar_provider(provider)

    existente = NfseDocumento.query.filter_by(
        chave_idempotencia=chave
    ).first()

    if existente is not None:
        _validar_documento_existente(
            existente,
            ordem_servico_id=ordem_servico_id,
            configuracao_fiscal_id=configuracao_fiscal_id,
            ambiente=ambiente_normalizado,
            provider=provider_normalizado,
        )
        return existente, False

    documento = NfseDocumento(
        ordem_servico_id=ordem_servico_id,
        configuracao_fiscal_id=configuracao_fiscal_id,
        status="RASCUNHO",
        ambiente=ambiente_normalizado,
        provider=provider_normalizado,
        chave_idempotencia=chave,
        mensagem_status=(
            "Rascunho criado pela camada idempotente "
            "da fundacao fiscal."
        ),
    )

    try:
        with db.session.begin_nested():
            db.session.add(documento)
            db.session.flush()

        return documento, True

    except IntegrityError:
        existente = NfseDocumento.query.filter_by(
            chave_idempotencia=chave
        ).first()

        if existente is not None:
            _validar_documento_existente(
                existente,
                ordem_servico_id=ordem_servico_id,
                configuracao_fiscal_id=configuracao_fiscal_id,
                ambiente=ambiente_normalizado,
                provider=provider_normalizado,
            )
            return existente, False

        raise


def preparar_nfse_da_os(
    ordem_servico_id: int,
) -> tuple[NfseDocumento, bool]:
    """Prepara localmente a NFS-e de uma OS concluida.

    Tambem adota, de forma segura, um unico RASCUNHO legado
    da fundacao fiscal criado antes da chave de idempotencia.

    Esta funcao NAO:
    - transmite NFS-e;
    - gera ou consome RPS;
    - incrementa proximo_rps;
    - cria lancamento financeiro;
    - usa o modulo legado NotaFiscalServico.
    """

    ordem = db.session.get(
        OrdemServico,
        ordem_servico_id,
    )

    if ordem is None:
        raise PreparacaoNfseInvalida(
            f"Ordem de servico {ordem_servico_id} nao encontrada."
        )

    if ordem.status != "concluida":
        raise PreparacaoNfseInvalida(
            "A NFS-e somente pode ser preparada para OS concluida."
        )

    if ordem.situacao_fiscal != "EMITIR_NFSE":
        raise PreparacaoNfseInvalida(
            "A OS nao possui decisao fiscal EMITIR_NFSE."
        )

    configuracoes = ConfiguracaoFiscal.query.filter_by(
        ativo=True
    ).all()

    if len(configuracoes) != 1:
        raise PreparacaoNfseInvalida(
            "Deve existir exatamente uma configuracao fiscal ativa."
        )

    configuracao = configuracoes[0]

    ambiente = (
        configuracao.ambiente or "HOMOLOGACAO"
    ).strip().upper()

    if ambiente not in AMBIENTES_NFSE:
        raise PreparacaoNfseInvalida(
            "Ambiente da configuracao fiscal e invalido."
        )

    provider = _normalizar_provider(
        configuracao.provider
    )

    chave = gerar_chave_emissao_original(
        ordem_servico_id
    )

    # 1. Caminho normal: intencao ja possui chave idempotente.
    existente = NfseDocumento.query.filter_by(
        chave_idempotencia=chave
    ).first()

    if existente is not None:
        _validar_documento_existente(
            existente,
            ordem_servico_id=ordem_servico_id,
            configuracao_fiscal_id=configuracao.id,
            ambiente=ambiente,
            provider=provider,
        )
        return existente, False

    # 2. Compatibilidade com rascunhos criados antes do C7.
    rascunhos_sem_chave = NfseDocumento.query.filter_by(
        ordem_servico_id=ordem_servico_id,
        configuracao_fiscal_id=configuracao.id,
        status="RASCUNHO",
        ambiente=ambiente,
        provider=provider,
        chave_idempotencia=None,
        ativo=True,
    ).all()

    if len(rascunhos_sem_chave) > 1:
        raise PreparacaoNfseInvalida(
            "Existem multiplos rascunhos sem chave de idempotencia "
            "para a mesma intencao fiscal."
        )

    if len(rascunhos_sem_chave) == 1:
        documento = rascunhos_sem_chave[0]

        documento.chave_idempotencia = chave
        documento.mensagem_status = (
            "Rascunho preexistente adotado pela camada "
            "idempotente da fundacao fiscal."
        )

        try:
            db.session.commit()
            return documento, False

        except Exception:
            db.session.rollback()
            raise

    # 3. Nenhum documento anterior: cria de forma idempotente.
    try:
        documento, criado = obter_ou_criar_rascunho(
            ordem_servico_id=ordem_servico_id,
            configuracao_fiscal_id=configuracao.id,
            chave_idempotencia=chave,
            ambiente=ambiente,
            provider=provider,
        )

        db.session.commit()

        return documento, criado

    except Exception:
        db.session.rollback()
        raise
