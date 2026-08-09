# -*- coding: utf-8 -*-

from __future__ import annotations

from datetime import date
from decimal import Decimal

from app.extensoes import db
from app.financeiro.financeiro_compat import status_eh_pago
from app.financeiro.financeiro_model import HistoricoFinanceiro, LancamentoFinanceiro
from app.pedido_compra.pedido_compra_model import PedidoCompra


ORIGEM_PEDIDO_COMPRA = "PEDIDO_COMPRA"
STATUS_GERAM_OBRIGACAO = {
    PedidoCompra.STATUS_APROVADO,
    PedidoCompra.STATUS_ENVIADO_FORNECEDOR,
    PedidoCompra.STATUS_RECEBIDO_PARCIAL,
    PedidoCompra.STATUS_RECEBIDO,
}


def _nome_usuario(usuario: str | None) -> str:
    texto = (usuario or "").strip()
    return texto or "sistema"


def _status_gera_obrigacao(status: str | None) -> bool:
    return (status or "").strip().upper() in STATUS_GERAM_OBRIGACAO


def _vencimento_pedido(pedido_compra: PedidoCompra) -> date:
    if pedido_compra.previsao_entrega:
        return pedido_compra.previsao_entrega

    raise ValueError(
        "Pedido sem previsao de entrega nao pode gerar conta a pagar automaticamente. "
        "Defina previsao de entrega para usar como vencimento desta obrigacao."
    )


def _descricao_lancamento(pedido_compra: PedidoCompra) -> str:
    fornecedor_nome = pedido_compra.fornecedor.nome if pedido_compra.fornecedor else "Fornecedor sem nome"
    return f"Pedido de Compra {pedido_compra.numero} - {fornecedor_nome}"


def _registrar_historico(lancamento: LancamentoFinanceiro, usuario: str | None, acao: str, motivo: str) -> None:
    db.session.add(
        HistoricoFinanceiro(
            lancamento_id=lancamento.id,
            campo_alterado="origem",
            valor_anterior=lancamento.origem,
            valor_novo=ORIGEM_PEDIDO_COMPRA,
            usuario=_nome_usuario(usuario),
            acao=acao,
            motivo=motivo,
        )
    )


def _lancamento_por_pedido(pedido_compra_id: int) -> LancamentoFinanceiro | None:
    return (
        LancamentoFinanceiro.query.filter(LancamentoFinanceiro.pedido_compra_id == pedido_compra_id)
        .order_by(LancamentoFinanceiro.id.desc())
        .first()
    )


def _cancelar_obrigacao_pendente(lancamento: LancamentoFinanceiro, usuario: str | None, motivo: str) -> None:
    if status_eh_pago(lancamento.status) and lancamento.data_pagamento is not None:
        return

    if lancamento.status != "cancelado" or lancamento.ativo:
        _registrar_historico(
            lancamento,
            usuario,
            acao="edicao",
            motivo=motivo,
        )

    lancamento.status = "cancelado"
    lancamento.ativo = False
    lancamento.usuario_editor = _nome_usuario(usuario)


def sincronizar_obrigacao_financeira_pedido_compra(
    pedido_compra: PedidoCompra,
    usuario: str | None = None,
) -> LancamentoFinanceiro | None:
    """Gera/sincroniza conta a pagar do pedido sem movimentar caixa."""
    lancamento = _lancamento_por_pedido(pedido_compra.id)

    if pedido_compra.status == PedidoCompra.STATUS_CANCELADO:
        if lancamento is not None:
            _cancelar_obrigacao_pendente(
                lancamento,
                usuario,
                motivo=f"Pedido de compra {pedido_compra.numero} cancelado.",
            )
        return lancamento

    if not _status_gera_obrigacao(pedido_compra.status):
        return lancamento

    valor_total = Decimal(str(pedido_compra.total or 0)).quantize(Decimal("0.01"))
    data_vencimento = _vencimento_pedido(pedido_compra)
    data_lancamento = pedido_compra.data_emissao or date.today()

    if lancamento is None:
        lancamento = LancamentoFinanceiro(
            descricao=_descricao_lancamento(pedido_compra),
            valor=valor_total,
            tipo="conta_pagar",
            status="pendente",
            data_lancamento=data_lancamento,
            data_vencimento=data_vencimento,
            data_pagamento=None,
            fornecedor_id=pedido_compra.fornecedor_id,
            pedido_compra_id=pedido_compra.id,
            numero_documento=pedido_compra.numero,
            origem=ORIGEM_PEDIDO_COMPRA,
            usuario_criador=_nome_usuario(usuario),
            usuario_editor=_nome_usuario(usuario),
            ativo=True,
        )
        db.session.add(lancamento)
        db.session.flush()
        _registrar_historico(
            lancamento,
            usuario,
            acao="criacao",
            motivo=f"Obrigacao criada automaticamente a partir do pedido {pedido_compra.numero}.",
        )
        return lancamento

    if status_eh_pago(lancamento.status) and lancamento.data_pagamento is not None:
        if (
            Decimal(str(lancamento.valor or 0)).quantize(Decimal("0.01")) != valor_total
            or lancamento.data_vencimento != data_vencimento
            or lancamento.fornecedor_id != pedido_compra.fornecedor_id
        ):
            _registrar_historico(
                lancamento,
                usuario,
                acao="edicao",
                motivo=(
                    "Pedido alterado apos quitacao do lancamento. "
                    "Sincronizacao automatica bloqueada para preservar historico financeiro."
                ),
            )
        return lancamento

    campos_alterados = []

    if Decimal(str(lancamento.valor or 0)).quantize(Decimal("0.01")) != valor_total:
        lancamento.valor = valor_total
        campos_alterados.append("valor")

    if lancamento.data_vencimento != data_vencimento:
        lancamento.data_vencimento = data_vencimento
        campos_alterados.append("data_vencimento")

    if lancamento.data_lancamento != data_lancamento:
        lancamento.data_lancamento = data_lancamento
        campos_alterados.append("data_lancamento")

    if lancamento.fornecedor_id != pedido_compra.fornecedor_id:
        lancamento.fornecedor_id = pedido_compra.fornecedor_id
        campos_alterados.append("fornecedor_id")

    descricao = _descricao_lancamento(pedido_compra)
    if lancamento.descricao != descricao:
        lancamento.descricao = descricao
        campos_alterados.append("descricao")

    if lancamento.numero_documento != pedido_compra.numero:
        lancamento.numero_documento = pedido_compra.numero
        campos_alterados.append("numero_documento")

    if lancamento.tipo != "conta_pagar":
        lancamento.tipo = "conta_pagar"
        campos_alterados.append("tipo")

    if lancamento.status != "pendente":
        lancamento.status = "pendente"
        campos_alterados.append("status")

    if lancamento.origem != ORIGEM_PEDIDO_COMPRA:
        lancamento.origem = ORIGEM_PEDIDO_COMPRA
        campos_alterados.append("origem")

    if not lancamento.ativo:
        lancamento.ativo = True
        campos_alterados.append("ativo")

    lancamento.pedido_compra_id = pedido_compra.id
    lancamento.usuario_editor = _nome_usuario(usuario)

    if campos_alterados:
        _registrar_historico(
            lancamento,
            usuario,
            acao="edicao",
            motivo=(
                f"Sincronizacao automatica do pedido {pedido_compra.numero}. "
                f"Campos atualizados: {', '.join(campos_alterados)}"
            ),
        )

    return lancamento
