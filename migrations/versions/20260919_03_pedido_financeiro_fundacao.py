"""Fundacao financeira para pedidos de venda.

Revision ID: 20260919_03
Revises: 20260919_02
Create Date: 2026-09-19

Adiciona rastreabilidade explicita entre lancamentos financeiros
e pedidos de venda.

Nesta fundacao cada pedido de venda direta possui no maximo
um recebivel financeiro.
"""

from alembic import op
import sqlalchemy as sa


revision = "20260919_03"
down_revision = "20260919_02"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "lancamentos_financeiros",
        sa.Column(
            "pedido_id",
            sa.Integer(),
            sa.ForeignKey("pedidos.id"),
            nullable=True,
        ),
    )

    op.create_index(
        "ux_lancamentos_financeiros_pedido_id",
        "lancamentos_financeiros",
        ["pedido_id"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index(
        "ux_lancamentos_financeiros_pedido_id",
        table_name="lancamentos_financeiros",
    )

    op.drop_column(
        "lancamentos_financeiros",
        "pedido_id",
    )
