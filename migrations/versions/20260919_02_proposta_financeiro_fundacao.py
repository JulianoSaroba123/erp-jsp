"""Fundacao financeira para propostas comerciais.

Revision ID: 20260919_02
Revises: 20260919_01
Create Date: 2026-09-19

Adiciona rastreabilidade explicita entre lancamentos financeiros,
propostas comerciais e parcelas de propostas.

Uma parcela de proposta pode possuir no maximo um lancamento financeiro,
garantindo idempotencia estrutural no fluxo Proposta -> Financeiro.
"""

from alembic import op
import sqlalchemy as sa


revision = "20260919_02"
down_revision = "20260919_01"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "lancamentos_financeiros",
        sa.Column(
            "proposta_id",
            sa.Integer(),
            sa.ForeignKey("propostas.id"),
            nullable=True,
        ),
    )

    op.add_column(
        "lancamentos_financeiros",
        sa.Column(
            "proposta_parcela_id",
            sa.Integer(),
            sa.ForeignKey("parcelas_proposta.id"),
            nullable=True,
        ),
    )

    op.create_index(
        "ix_lancamentos_financeiros_proposta_id",
        "lancamentos_financeiros",
        ["proposta_id"],
        unique=False,
    )

    op.create_index(
        "ux_lancamentos_financeiros_proposta_parcela_id",
        "lancamentos_financeiros",
        ["proposta_parcela_id"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index(
        "ux_lancamentos_financeiros_proposta_parcela_id",
        table_name="lancamentos_financeiros",
    )

    op.drop_index(
        "ix_lancamentos_financeiros_proposta_id",
        table_name="lancamentos_financeiros",
    )

    op.drop_column(
        "lancamentos_financeiros",
        "proposta_parcela_id",
    )

    op.drop_column(
        "lancamentos_financeiros",
        "proposta_id",
    )
