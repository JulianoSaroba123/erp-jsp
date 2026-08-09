"""Add pedido_compra_id FK to lancamentos_financeiros

Revision ID: 20260808_01
Revises: 20260803_01
Create Date: 2026-08-08
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260808_01"
down_revision = "20260803_01"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table(
        "lancamentos_financeiros",
        recreate="auto",
        reflect_kwargs={"resolve_fks": False},
    ) as batch_op:
        batch_op.add_column(sa.Column("pedido_compra_id", sa.Integer(), nullable=True))
        batch_op.create_index(
            "ix_lancamentos_financeiros_pedido_compra_id",
            ["pedido_compra_id"],
            unique=True,
        )
        batch_op.create_foreign_key(
            "fk_lancamentos_financeiros_pedido_compra_id",
            "pedidos_compra",
            ["pedido_compra_id"],
            ["id"],
        )


def downgrade() -> None:
    with op.batch_alter_table(
        "lancamentos_financeiros",
        recreate="auto",
        reflect_kwargs={"resolve_fks": False},
    ) as batch_op:
        batch_op.drop_constraint(
            "fk_lancamentos_financeiros_pedido_compra_id",
            type_="foreignkey",
        )
        batch_op.drop_index("ix_lancamentos_financeiros_pedido_compra_id")
        batch_op.drop_column("pedido_compra_id")
