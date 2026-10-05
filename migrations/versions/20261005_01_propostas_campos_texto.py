"""amplia campos narrativos da proposta para TEXT

Revision ID: 20261005_01
Revises: 20260922_03
Create Date: 2026-10-05
"""

from alembic import op
import sqlalchemy as sa


revision = "20261005_01"
down_revision = "20260922_03"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column(
        "propostas",
        "prazo_execucao",
        existing_type=sa.String(length=500),
        type_=sa.Text(),
        existing_nullable=True,
    )
    op.alter_column(
        "propostas",
        "garantia",
        existing_type=sa.String(length=500),
        type_=sa.Text(),
        existing_nullable=True,
    )


def downgrade() -> None:
    # Evita truncamento silencioso caso já existam textos maiores que 500.
    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1
                FROM propostas
                WHERE length(coalesce(prazo_execucao, '')) > 500
                   OR length(coalesce(garantia, '')) > 500
            ) THEN
                RAISE EXCEPTION
                    'Downgrade bloqueado: existem textos com mais de 500 caracteres';
            END IF;
        END
        $$;
        """
    )

    op.alter_column(
        "propostas",
        "garantia",
        existing_type=sa.Text(),
        type_=sa.String(length=500),
        existing_nullable=True,
    )
    op.alter_column(
        "propostas",
        "prazo_execucao",
        existing_type=sa.Text(),
        type_=sa.String(length=500),
        existing_nullable=True,
    )
