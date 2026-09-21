# -*- coding: utf-8 -*-
"""Integracao Pedido de Venda -> Estoque.

D26F03

Responsabilidades:
- movimentar apenas pedido concluido;
- considerar apenas produtos que controlam estoque;
- agregar linhas repetidas do mesmo produto;
- bloquear saldo insuficiente;
- manter historico auditavel;
- garantir idempotencia;
- nao realizar commit proprio.
"""

from collections import defaultdict
from decimal import Decimal, ROUND_HALF_UP

from app.extensoes import db
from app.estoque.estoque_model import MovimentacaoEstoque
from app.pedido.pedido_model import PedidoItem
from app.produto.produto_model import Produto


MIL = Decimal("0.001")


def _decimal_quantidade(valor):
    return Decimal(
        str(valor or 0)
    ).quantize(
        MIL,
        rounding=ROUND_HALF_UP,
    )


def _pedido_concluido(pedido):
    return (
        str(
            getattr(
                pedido,
                "status",
                "",
            )
            or ""
        )
        .strip()
        .upper()
        == "CONCLUIDO"
    )


def _agrupar_produtos_pedido(pedido):
    """Agrupa quantidades por produto_id."""

    totais = defaultdict(
        lambda: Decimal("0.000")
    )

    itens = (
        pedido.itens
        .filter(
            PedidoItem.ativo.is_(True),
        )
        .order_by(
            PedidoItem.ordem.asc(),
            PedidoItem.id.asc(),
        )
        .all()
    )

    for item in itens:
        if item.tipo_item != PedidoItem.TIPO_PRODUTO:
            continue

        if item.produto_id is None:
            continue

        quantidade = _decimal_quantidade(
            item.quantidade
        )

        if quantidade <= Decimal("0.000"):
            continue

        totais[item.produto_id] += quantidade

    return {
        produto_id: _decimal_quantidade(
            quantidade
        )
        for produto_id, quantidade in totais.items()
    }


def _obter_movimento_existente(
    pedido_id,
    produto_id,
):
    """Busca movimento inclusive se estiver inativo.

    Uma movimentacao historica existente significa que
    aquele Pedido/Produto ja foi processado e nao pode
    baixar estoque novamente.
    """

    return (
        MovimentacaoEstoque.query
        .filter_by(
            pedido_id=pedido_id,
            produto_id=produto_id,
            tipo=MovimentacaoEstoque.TIPO_SAIDA,
            origem=MovimentacaoEstoque.ORIGEM_PEDIDO,
        )
        .first()
    )


def sincronizar_estoque_pedido(pedido):
    """Sincroniza saidas de estoque de pedido concluido.

    Nao executa commit.
    A transacao pertence ao chamador.
    """

    if not _pedido_concluido(pedido):
        return []

    if getattr(pedido, "id", None) is None:
        raise ValueError(
            "Pedido precisa estar persistido "
            "antes da movimentacao de estoque."
        )

    quantidades = _agrupar_produtos_pedido(
        pedido
    )

    if not quantidades:
        return []

    movimentos_existentes = []
    planos = []

    # Ordem deterministica dos locks reduz risco
    # de deadlock em pedidos com varios produtos.
    for produto_id in sorted(
        quantidades.keys()
    ):
        produto = (
            Produto.query
            .filter(
                Produto.id == produto_id,
            )
            .with_for_update()
            .one_or_none()
        )

        if produto is None:
            raise ValueError(
                f"Produto {produto_id} "
                "nao encontrado para movimentacao."
            )

        if not produto.controla_estoque:
            continue

        movimento_existente = (
            _obter_movimento_existente(
                pedido.id,
                produto_id,
            )
        )

        if movimento_existente is not None:
            movimentos_existentes.append(
                movimento_existente
            )
            continue

        quantidade = quantidades[
            produto_id
        ]

        estoque_anterior = (
            _decimal_quantidade(
                produto.estoque_atual
            )
        )

        if estoque_anterior < quantidade:
            raise ValueError(
                "Estoque insuficiente para "
                f"{produto.nome}: "
                f"disponivel "
                f"{estoque_anterior:.3f}, "
                f"necessario "
                f"{quantidade:.3f}."
            )

        estoque_posterior = (
            estoque_anterior
            - quantidade
        ).quantize(
            MIL,
            rounding=ROUND_HALF_UP,
        )

        planos.append(
            {
                "produto": produto,
                "quantidade": quantidade,
                "estoque_anterior":
                    estoque_anterior,
                "estoque_posterior":
                    estoque_posterior,
            }
        )

    novos_movimentos = []

    # So altera saldos depois de validar TODOS
    # os produtos do pedido.
    for plano in planos:
        produto = plano["produto"]

        produto.estoque_atual = (
            plano["estoque_posterior"]
        )

        movimento = MovimentacaoEstoque(
            produto_id=produto.id,
            pedido_id=pedido.id,
            tipo=MovimentacaoEstoque.TIPO_SAIDA,
            origem=MovimentacaoEstoque.ORIGEM_PEDIDO,
            quantidade=plano["quantidade"],
            estoque_anterior=plano[
                "estoque_anterior"
            ],
            estoque_posterior=plano[
                "estoque_posterior"
            ],
            documento=(
                getattr(
                    pedido,
                    "numero",
                    None,
                )
                or f"PED-{pedido.id}"
            ),
            observacoes=(
                "Saida automatica de estoque "
                f"do pedido "
                f"{getattr(pedido, 'numero', pedido.id)}."
            ),
            ativo=True,
        )

        db.session.add(movimento)
        novos_movimentos.append(
            movimento
        )

    db.session.flush()

    return (
        movimentos_existentes
        + novos_movimentos
    )
