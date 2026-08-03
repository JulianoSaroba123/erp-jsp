"""Create pedidos_compra and pedido_compra_itens

Revision ID: 20260803_01
Revises: 20260801_02
Create Date: 2026-08-03
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260803_01"
down_revision = "20260801_02"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "pedidos_compra",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("numero", sa.String(length=20), nullable=False),
        sa.Column("fornecedor_id", sa.Integer(), nullable=False),
        sa.Column("ordem_servico_id", sa.Integer(), nullable=True),
        sa.Column("pedido_venda_id", sa.Integer(), nullable=True),
        sa.Column("data_emissao", sa.Date(), nullable=False),
        sa.Column("previsao_entrega", sa.Date(), nullable=True),
        sa.Column("solicitante", sa.String(length=150), nullable=True),
        sa.Column("responsavel_compra", sa.String(length=150), nullable=True),
        sa.Column("condicao_pagamento", sa.Text(), nullable=True),
        sa.Column("observacoes", sa.Text(), nullable=True),
        sa.Column("finalidade", sa.String(length=30), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("subtotal", sa.Numeric(12, 2), nullable=False, server_default="0.00"),
        sa.Column("desconto", sa.Numeric(12, 2), nullable=False, server_default="0.00"),
        sa.Column("total", sa.Numeric(12, 2), nullable=False, server_default="0.00"),
        sa.Column("criado_em", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("atualizado_em", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("ativo", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.CheckConstraint(
            "status IN ('RASCUNHO', 'AGUARDANDO_APROVACAO', 'APROVADO', 'ENVIADO_FORNECEDOR', 'RECEBIDO_PARCIAL', 'RECEBIDO', 'CANCELADO')",
            name="ck_pedidos_compra_status",
        ),
        sa.CheckConstraint(
            "finalidade IN ('ESTOQUE', 'ORDEM_SERVICO', 'PEDIDO_VENDA', 'ADMINISTRATIVO')",
            name="ck_pedidos_compra_finalidade",
        ),
        sa.CheckConstraint("subtotal >= 0", name="ck_pedidos_compra_subtotal_nao_negativo"),
        sa.CheckConstraint("desconto >= 0", name="ck_pedidos_compra_desconto_nao_negativo"),
        sa.CheckConstraint("total >= 0", name="ck_pedidos_compra_total_nao_negativo"),
        sa.ForeignKeyConstraint(["fornecedor_id"], ["fornecedores.id"], name="fk_pedidos_compra_fornecedor_id", ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["ordem_servico_id"], ["ordem_servico.id"], name="fk_pedidos_compra_ordem_servico_id", ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["pedido_venda_id"], ["pedidos.id"], name="fk_pedidos_compra_pedido_venda_id", ondelete="RESTRICT"),
        sa.UniqueConstraint("numero", name="uq_pedidos_compra_numero"),
    )
    op.create_index("ix_pedidos_compra_numero", "pedidos_compra", ["numero"], unique=True)
    op.create_index("ix_pedidos_compra_fornecedor_id", "pedidos_compra", ["fornecedor_id"], unique=False)
    op.create_index("ix_pedidos_compra_ordem_servico_id", "pedidos_compra", ["ordem_servico_id"], unique=False)
    op.create_index("ix_pedidos_compra_pedido_venda_id", "pedidos_compra", ["pedido_venda_id"], unique=False)
    op.create_index("ix_pedidos_compra_finalidade", "pedidos_compra", ["finalidade"], unique=False)
    op.create_index("ix_pedidos_compra_status", "pedidos_compra", ["status"], unique=False)

    op.create_table(
        "pedido_compra_itens",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("pedido_compra_id", sa.Integer(), nullable=False),
        sa.Column("tipo_item", sa.String(length=20), nullable=False),
        sa.Column("produto_id", sa.Integer(), nullable=True),
        sa.Column("servico_id", sa.Integer(), nullable=True),
        sa.Column("descricao", sa.String(length=255), nullable=False),
        sa.Column("unidade", sa.String(length=20), nullable=True),
        sa.Column("quantidade_comprada", sa.Numeric(12, 3), nullable=False, server_default="1.000"),
        sa.Column("quantidade_recebida", sa.Numeric(12, 3), nullable=False, server_default="0.000"),
        sa.Column("valor_unitario", sa.Numeric(12, 2), nullable=False, server_default="0.00"),
        sa.Column("desconto", sa.Numeric(12, 2), nullable=False, server_default="0.00"),
        sa.Column("valor_total", sa.Numeric(12, 2), nullable=False, server_default="0.00"),
        sa.Column("ordem", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("criado_em", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("atualizado_em", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("ativo", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.CheckConstraint("tipo_item IN ('PRODUTO', 'SERVICO')", name="ck_pedido_compra_itens_tipo_item"),
        sa.CheckConstraint(
            "((produto_id IS NOT NULL AND servico_id IS NULL) OR (produto_id IS NULL AND servico_id IS NOT NULL))",
            name="ck_pedido_compra_itens_referencia_exclusiva",
        ),
        sa.CheckConstraint("quantidade_comprada > 0", name="ck_pedido_compra_itens_quantidade_positiva"),
        sa.CheckConstraint("quantidade_recebida >= 0", name="ck_pedido_compra_itens_quantidade_recebida_nao_negativa"),
        sa.CheckConstraint("valor_unitario >= 0", name="ck_pedido_compra_itens_valor_unitario_nao_negativo"),
        sa.CheckConstraint("desconto >= 0", name="ck_pedido_compra_itens_desconto_nao_negativo"),
        sa.CheckConstraint("valor_total >= 0", name="ck_pedido_compra_itens_valor_total_nao_negativo"),
        sa.ForeignKeyConstraint(["pedido_compra_id"], ["pedidos_compra.id"], name="fk_pedido_compra_itens_pedido_compra_id", ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["produto_id"], ["produtos.id"], name="fk_pedido_compra_itens_produto_id", ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["servico_id"], ["servicos.id"], name="fk_pedido_compra_itens_servico_id", ondelete="RESTRICT"),
    )
    op.create_index("ix_pedido_compra_itens_pedido_compra_id", "pedido_compra_itens", ["pedido_compra_id"], unique=False)
    op.create_index("ix_pedido_compra_itens_tipo_item", "pedido_compra_itens", ["tipo_item"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_pedido_compra_itens_tipo_item", table_name="pedido_compra_itens")
    op.drop_index("ix_pedido_compra_itens_pedido_compra_id", table_name="pedido_compra_itens")
    op.drop_table("pedido_compra_itens")

    op.drop_index("ix_pedidos_compra_status", table_name="pedidos_compra")
    op.drop_index("ix_pedidos_compra_finalidade", table_name="pedidos_compra")
    op.drop_index("ix_pedidos_compra_pedido_venda_id", table_name="pedidos_compra")
    op.drop_index("ix_pedidos_compra_ordem_servico_id", table_name="pedidos_compra")
    op.drop_index("ix_pedidos_compra_fornecedor_id", table_name="pedidos_compra")
    op.drop_index("ix_pedidos_compra_numero", table_name="pedidos_compra")
    op.drop_table("pedidos_compra")
