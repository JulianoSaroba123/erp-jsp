"""Servicos da nova fundacao NFS-e.

Nenhuma funcao deste modulo transmite NFS-e.
"""

from sqlalchemy.exc import IntegrityError

from app.extensoes import db
from app.fiscal.nfse_documento_model import (
    AMBIENTES_NFSE,
    NfseDocumento,
)


class ConflitoIdempotencia(ValueError):
    """A mesma chave foi reutilizada para outro contexto fiscal."""


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
    """Retorna a intencao existente ou cria um unico rascunho.

    Returns:
        (documento, criado_agora)
    """

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
        # SAVEPOINT protege a transacao externa caso outra
        # requisicao grave a mesma chave simultaneamente.
        with db.session.begin_nested():
            db.session.add(documento)
            db.session.flush()

        return documento, True

    except IntegrityError:
        # Em concorrencia, outra requisicao pode vencer o INSERT.
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
