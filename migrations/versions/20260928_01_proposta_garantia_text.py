"""Amplia garantia contratual das propostas para TEXT.

Revision ID: 20260928_01
Revises: 20260922_03
Create Date: 2026-09-28
"""

from alembic import op
import sqlalchemy as sa


revision = "20260928_01"
down_revision = "20260922_03"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column(
        "propostas",
        "garantia",
        existing_type=sa.String(length=500),
        type_=sa.Text(),
        existing_nullable=True,
        postgresql_using="garantia::text",
    )


def downgrade() -> None:
    # Não truncar contratos existentes numa reversão.
    bind = op.get_bind()
    excedentes = bind.execute(
        sa.text(
            "SELECT count(*) FROM propostas "
            "WHERE char_length(garantia) > 500"
        )
    ).scalar_one()
    if excedentes:
        raise RuntimeError(
            "Downgrade bloqueado: existem garantias com mais de "
            "500 caracteres. Preserve os textos antes de reverter."
        )

    op.alter_column(
        "propostas",
        "garantia",
        existing_type=sa.Text(),
        type_=sa.String(length=500),
        existing_nullable=True,
        postgresql_using="garantia::varchar(500)",
    )
