"""Create pedidos and pedido_itens foundation

Revision ID: 20260801_02
Revises: 20260801_01
Create Date: 2026-08-01
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20260801_02"
down_revision = "20260801_01"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "pedidos",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("numero", sa.String(length=20), nullable=False),
        sa.Column("cliente_id", sa.Integer(), nullable=False),
        sa.Column("proposta_id", sa.Integer(), nullable=True),
        sa.Column("data_pedido", sa.Date(), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("responsavel", sa.String(length=100), nullable=True),
        sa.Column("solicitante", sa.String(length=150), nullable=True),
        sa.Column("telefone_contato", sa.String(length=25), nullable=True),
        sa.Column("email_contato", sa.String(length=150), nullable=True),
        sa.Column("prazo_previsto", sa.Date(), nullable=True),
        sa.Column("condicoes_pagamento", sa.Text(), nullable=True),
        sa.Column("subtotal", sa.Numeric(12, 2), nullable=False, server_default="0.00"),
        sa.Column("desconto", sa.Numeric(12, 2), nullable=False, server_default="0.00"),
        sa.Column("valor_total", sa.Numeric(12, 2), nullable=False, server_default="0.00"),
        sa.Column("observacoes", sa.Text(), nullable=True),
        sa.Column("criado_em", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("atualizado_em", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("ativo", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.CheckConstraint(
            "status IN ('RASCUNHO', 'AGUARDANDO_CONFIRMACAO', 'CONFIRMADO', 'EM_EXECUCAO', 'CONCLUIDO', 'CANCELADO')",
            name="ck_pedidos_status",
        ),
        sa.CheckConstraint("subtotal >= 0", name="ck_pedidos_subtotal_nao_negativo"),
        sa.CheckConstraint("desconto >= 0", name="ck_pedidos_desconto_nao_negativo"),
        sa.CheckConstraint("valor_total >= 0", name="ck_pedidos_valor_total_nao_negativo"),
        sa.ForeignKeyConstraint(["cliente_id"], ["clientes.id"], name="fk_pedidos_cliente_id", ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["proposta_id"], ["propostas.id"], name="fk_pedidos_proposta_id", ondelete="RESTRICT"),
        sa.UniqueConstraint("numero", name="uq_pedidos_numero"),
        sa.UniqueConstraint("proposta_id", name="uq_pedidos_proposta_id"),
    )
    op.create_index("ix_pedidos_numero", "pedidos", ["numero"], unique=True)
    op.create_index("ix_pedidos_cliente_id", "pedidos", ["cliente_id"], unique=False)
    op.create_index("ix_pedidos_proposta_id", "pedidos", ["proposta_id"], unique=True)
    op.create_index("ix_pedidos_status", "pedidos", ["status"], unique=False)

    op.create_table(
        "pedido_itens",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("pedido_id", sa.Integer(), nullable=False),
        sa.Column("tipo_item", sa.String(length=20), nullable=False),
        sa.Column("produto_id", sa.Integer(), nullable=True),
        sa.Column("servico_id", sa.Integer(), nullable=True),
        sa.Column("descricao", sa.String(length=255), nullable=False),
        sa.Column("quantidade", sa.Numeric(12, 3), nullable=False, server_default="1.000"),
        sa.Column("valor_unitario", sa.Numeric(12, 2), nullable=False, server_default="0.00"),
        sa.Column("desconto", sa.Numeric(12, 2), nullable=False, server_default="0.00"),
        sa.Column("valor_total", sa.Numeric(12, 2), nullable=False, server_default="0.00"),
        sa.Column("ordem", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("criado_em", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("atualizado_em", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("ativo", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.CheckConstraint("tipo_item IN ('PRODUTO', 'SERVICO')", name="ck_pedido_itens_tipo_item"),
        sa.CheckConstraint(
            "((produto_id IS NOT NULL AND servico_id IS NULL) OR (produto_id IS NULL AND servico_id IS NOT NULL))",
            name="ck_pedido_itens_referencia_exclusiva",
        ),
        sa.CheckConstraint("quantidade > 0", name="ck_pedido_itens_quantidade_positiva"),
        sa.CheckConstraint("valor_unitario >= 0", name="ck_pedido_itens_valor_unitario_nao_negativo"),
        sa.CheckConstraint("desconto >= 0", name="ck_pedido_itens_desconto_nao_negativo"),
        sa.CheckConstraint("valor_total >= 0", name="ck_pedido_itens_valor_total_nao_negativo"),
        sa.ForeignKeyConstraint(["pedido_id"], ["pedidos.id"], name="fk_pedido_itens_pedido_id", ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["produto_id"], ["produtos.id"], name="fk_pedido_itens_produto_id", ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["servico_id"], ["servicos.id"], name="fk_pedido_itens_servico_id", ondelete="RESTRICT"),
    )
    op.create_index("ix_pedido_itens_pedido_id", "pedido_itens", ["pedido_id"], unique=False)
    op.create_index("ix_pedido_itens_tipo_item", "pedido_itens", ["tipo_item"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_pedido_itens_tipo_item", table_name="pedido_itens")
    op.drop_index("ix_pedido_itens_pedido_id", table_name="pedido_itens")
    op.drop_table("pedido_itens")

    op.drop_index("ix_pedidos_status", table_name="pedidos")
    op.drop_index("ix_pedidos_proposta_id", table_name="pedidos")
    op.drop_index("ix_pedidos_cliente_id", table_name="pedidos")
    op.drop_index("ix_pedidos_numero", table_name="pedidos")
    op.drop_table("pedidos")
