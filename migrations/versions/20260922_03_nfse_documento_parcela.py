"""vincula nfse a parcela da ordem de servico

Revision ID: 20260922_03
Revises: 20260922_02
Create Date: 2026-09-22
"""

from alembic import op
import sqlalchemy as sa


revision = "20260922_03"
down_revision = "20260922_02"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "nfse_documento",
        sa.Column(
            "ordem_servico_parcela_id",
            sa.Integer(),
            nullable=True,
        ),
    )

    op.add_column(
        "nfse_documento",
        sa.Column(
            "valor_servicos",
            sa.Numeric(12, 2),
            nullable=True,
        ),
    )

    op.create_foreign_key(
        "fk_nfse_documento_ordem_servico_parcela",
        "nfse_documento",
        "ordem_servico_parcelas",
        ["ordem_servico_parcela_id"],
        ["id"],
        ondelete="RESTRICT",
    )

    op.create_index(
        "ix_nfse_documento_ordem_servico_parcela_id",
        "nfse_documento",
        ["ordem_servico_parcela_id"],
        unique=False,
    )

    op.create_unique_constraint(
        "uq_nfse_documento_parcela",
        "nfse_documento",
        ["ordem_servico_parcela_id"],
    )

    op.create_check_constraint(
        "ck_nfse_documento_valor_servicos",
        "nfse_documento",
        "valor_servicos IS NULL OR valor_servicos > 0",
    )


def downgrade() -> None:
    op.drop_constraint(
        "ck_nfse_documento_valor_servicos",
        "nfse_documento",
        type_="check",
    )

    op.drop_constraint(
        "uq_nfse_documento_parcela",
        "nfse_documento",
        type_="unique",
    )

    op.drop_index(
        "ix_nfse_documento_ordem_servico_parcela_id",
        table_name="nfse_documento",
    )

    op.drop_constraint(
        "fk_nfse_documento_ordem_servico_parcela",
        "nfse_documento",
        type_="foreignkey",
    )

    op.drop_column(
        "nfse_documento",
        "valor_servicos",
    )

    op.drop_column(
        "nfse_documento",
        "ordem_servico_parcela_id",
    )
