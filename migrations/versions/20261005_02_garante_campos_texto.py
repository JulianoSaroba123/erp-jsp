"""garante campos narrativos TEXT apos inicializacao

Revision ID: 20261005_02
Revises: 20261005_01
Create Date: 2026-10-05
"""

from alembic import op


revision = "20261005_02"
down_revision = "20261005_01"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        "ALTER TABLE propostas "
        "ALTER COLUMN prazo_execucao TYPE TEXT"
    )
    op.execute(
        "ALTER TABLE propostas "
        "ALTER COLUMN garantia TYPE TEXT"
    )


def downgrade() -> None:
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
    op.execute(
        "ALTER TABLE propostas "
        "ALTER COLUMN garantia TYPE VARCHAR(500)"
    )
    op.execute(
        "ALTER TABLE propostas "
        "ALTER COLUMN prazo_execucao TYPE VARCHAR(500)"
    )
