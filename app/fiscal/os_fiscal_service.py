"""Regras de decisao fiscal vinculadas a Ordem de Servico.

Esta camada nao emite NFS-e e nao cria lancamentos financeiros.
Responsabilidade atual:
- registrar a decisao fiscal da OS;
- validar a decisao;
- manter auditoria;
- garantir atualizacao da OS + historico na mesma transacao.
"""

from datetime import datetime

from app.extensoes import db
from app.ordem_servico.ordem_servico_model import (
    OrdemServico,
    OrdemServicoFiscalHistorico,
)


SITUACAO_FISCAL_PENDENTE = "PENDENTE"
SITUACAO_FISCAL_EMITIR_NFSE = "EMITIR_NFSE"
SITUACAO_FISCAL_NAO_EMITIR = "NAO_EMITIR"

SITUACOES_FISCAIS_VALIDAS = {
    SITUACAO_FISCAL_PENDENTE,
    SITUACAO_FISCAL_EMITIR_NFSE,
    SITUACAO_FISCAL_NAO_EMITIR,
}


class DecisaoFiscalInvalida(ValueError):
    """Decisao fiscal recusada pelas regras de dominio."""


class OrdemServicoNaoEncontrada(LookupError):
    """OS informada nao existe."""


def _normalizar_texto(valor):
    if valor is None:
        return None

    valor = str(valor).strip()
    return valor or None


def registrar_decisao_fiscal(
    ordem_servico_id,
    situacao,
    usuario_id,
    motivo=None,
    observacao=None,
):
    """Registra uma decisao fiscal e seu historico atomicamente.

    Situacoes atuais:
    - PENDENTE: decidir depois;
    - EMITIR_NFSE: preparar emissao de NFS-e posteriormente;
    - NAO_EMITIR: nao emitir, obrigatoriamente com motivo.

    Esta funcao nao:
    - conclui a OS;
    - emite nota;
    - cria contas a receber;
    - altera lancamentos financeiros.
    """

    situacao = (situacao or "").strip().upper()
    motivo = _normalizar_texto(motivo)
    observacao = _normalizar_texto(observacao)

    if situacao not in SITUACOES_FISCAIS_VALIDAS:
        raise DecisaoFiscalInvalida(
            f"Situacao fiscal invalida: {situacao!r}"
        )

    if usuario_id is None:
        raise DecisaoFiscalInvalida(
            "Usuario responsavel pela decisao fiscal e obrigatorio."
        )

    if situacao == SITUACAO_FISCAL_NAO_EMITIR and not motivo:
        raise DecisaoFiscalInvalida(
            "Motivo e obrigatorio para a decisao NAO_EMITIR."
        )

    ordem = db.session.get(OrdemServico, ordem_servico_id)

    if ordem is None:
        raise OrdemServicoNaoEncontrada(
            f"Ordem de servico {ordem_servico_id} nao encontrada."
        )

    situacao_anterior = (
        ordem.situacao_fiscal or SITUACAO_FISCAL_PENDENTE
    )

    agora = datetime.utcnow()

    ordem.situacao_fiscal = situacao
    ordem.motivo_nao_emissao = (
        motivo
        if situacao == SITUACAO_FISCAL_NAO_EMITIR
        else None
    )
    ordem.observacao_fiscal = observacao
    ordem.decisao_fiscal_em = agora
    ordem.decisao_fiscal_usuario_id = usuario_id

    historico = OrdemServicoFiscalHistorico(
        ordem_servico_id=ordem.id,
        situacao_anterior=situacao_anterior,
        situacao_nova=situacao,
        motivo=motivo,
        observacao=observacao,
        usuario_id=usuario_id,
        criado_em=agora,
    )

    db.session.add(ordem)
    db.session.add(historico)

    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise

    return ordem, historico
