"""Cria funda??o N:N da concilia??o banc?ria.

Revision ID: 20260917_01
Revises: 20260912_01
Create Date: 2026-09-17
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260917_01"
down_revision = "20260912_01"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "conciliacao_bancaria_itens",
        sa.Column(
            "id",
            sa.Integer(),
            primary_key=True,
            autoincrement=True,
        ),
        sa.Column(
            "extrato_id",
            sa.Integer(),
            nullable=False,
        ),
        sa.Column(
            "lancamento_id",
            sa.Integer(),
            nullable=False,
        ),
        sa.Column(
            "valor_conciliado",
            sa.Numeric(12, 2),
            nullable=False,
        ),
        sa.Column(
            "data_conciliacao",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column(
            "usuario",
            sa.String(length=100),
            nullable=True,
        ),
        sa.Column(
            "observacoes",
            sa.Text(),
            nullable=True,
        ),
        sa.Column(
            "criado_em",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column(
            "atualizado_em",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column(
            "ativo",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("true"),
        ),
        sa.ForeignKeyConstraint(
            ["extrato_id"],
            ["extratos_bancarios.id"],
            name="fk_conciliacao_bancaria_itens_extrato_id",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["lancamento_id"],
            ["lancamentos_financeiros.id"],
            name="fk_conciliacao_bancaria_itens_lancamento_id",
            ondelete="RESTRICT",
        ),
        sa.UniqueConstraint(
            "extrato_id",
            "lancamento_id",
            name="uq_conciliacao_bancaria_extrato_lancamento",
        ),
        sa.CheckConstraint(
            "valor_conciliado > 0",
            name="ck_conciliacao_bancaria_valor_positivo",
        ),
    )

    op.create_index(
        "ix_conciliacao_bancaria_itens_extrato_id",
        "conciliacao_bancaria_itens",
        ["extrato_id"],
        unique=False,
    )

    op.create_index(
        "ix_conciliacao_bancaria_itens_lancamento_id",
        "conciliacao_bancaria_itens",
        ["lancamento_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_conciliacao_bancaria_itens_lancamento_id",
        table_name="conciliacao_bancaria_itens",
    )

    op.drop_index(
        "ix_conciliacao_bancaria_itens_extrato_id",
        table_name="conciliacao_bancaria_itens",
    )

    op.drop_table("conciliacao_bancaria_itens")
