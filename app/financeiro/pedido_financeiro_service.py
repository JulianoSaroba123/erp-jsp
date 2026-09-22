# -*- coding: utf-8 -*-
"""Integracao financeira dos pedidos de venda.

D26F01-A2

Responsabilidades:
- gerar recebivel para pedido de venda direta concluido;
- manter rastreabilidade Pedido -> Financeiro;
- garantir idempotencia;
- preservar recebiveis ja quitados;
- impedir duplicidade quando o pedido nasceu de proposta;
- nao realizar commit proprio.
"""

from datetime import date
from decimal import Decimal, ROUND_HALF_UP

from app.extensoes import db
from app.financeiro.financeiro_model import LancamentoFinanceiro


CENTAVO = Decimal("0.01")
_STATUS_QUITADOS = {"pago", "recebido"}


def _decimal(valor):
    return Decimal(str(valor or 0)).quantize(
        CENTAVO,
        rounding=ROUND_HALF_UP,
    )


def _pedido_concluido(pedido):
    return (
        str(getattr(pedido, "status", "") or "")
        .strip()
        .upper()
        == "CONCLUIDO"
    )


def _pedido_originado_de_proposta(pedido):
    return getattr(pedido, "proposta_id", None) is not None


def _forma_pagamento(pedido):
    texto = str(
        getattr(pedido, "condicoes_pagamento", "")
        or ""
    ).strip()

    if not texto:
        return None

    return texto[:50]


def sincronizar_lancamentos_pedido(pedido):
    """Sincroniza recebivel de pedido de venda direta concluido.

    Nao executa commit.
    O chamador controla a transacao.
    """

    if not _pedido_concluido(pedido):
        return []

    if _pedido_originado_de_proposta(pedido):
        return []

    if getattr(pedido, "id", None) is None:
        raise ValueError(
            "Pedido precisa estar persistido antes da geracao financeira."
        )

    valor = _decimal(
        getattr(pedido, "valor_total", 0)
    )

    if valor <= 0:
        return []

    lancamento = (
        LancamentoFinanceiro.query
        .filter(
            LancamentoFinanceiro.pedido_id == pedido.id,
        )
        .first()
    )

    novo_lancamento = lancamento is None

    if novo_lancamento:
        lancamento = LancamentoFinanceiro(
            origem="PEDIDO",
            pedido_id=pedido.id,
        )

    if (
        lancamento.id is not None
        and lancamento.status in _STATUS_QUITADOS
        and lancamento.data_pagamento is not None
    ):
        return [lancamento]

    numero = (
        getattr(pedido, "numero", None)
        or f"PED-{pedido.id}"
    )

    cliente = getattr(
        pedido,
        "cliente",
        None,
    )

    cliente_nome = (
        getattr(cliente, "nome", None)
        or "Cliente"
    )

    lancamento.descricao = (
        f"Pedido {numero} - {cliente_nome}"
    )

    lancamento.valor = valor
    lancamento.valor_original = valor

    lancamento.tipo = "conta_receber"
    lancamento.status = "pendente"

    lancamento.categoria = "Vendas"
    lancamento.subcategoria = "Pedido de Venda"

    lancamento.data_lancamento = (
        getattr(pedido, "data_pedido", None)
        or date.today()
    )

    lancamento.data_vencimento = None

    lancamento.numero_documento = numero

    lancamento.forma_pagamento = (
        _forma_pagamento(pedido)
    )

    lancamento.cliente_id = pedido.cliente_id
    lancamento.pedido_id = pedido.id

    lancamento.numero_parcela = "1/1"

    lancamento.observacoes = (
        f"Lancamento automatico do pedido {numero}."
    )

    lancamento.origem = "PEDIDO"
    lancamento.ativo = True

    # Um lancamento novo so entra na sessao depois
    # de possuir todos os campos obrigatorios.
    # Isso evita autoflush prematuro durante lazy-load
    # de relacionamentos do Pedido.
    if novo_lancamento:
        db.session.add(lancamento)

    db.session.flush()

    return [lancamento]
