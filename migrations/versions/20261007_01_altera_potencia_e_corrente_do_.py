"""altera potencia e corrente do alternador para texto

Revision ID: 20261007_01
Revises: 20261006_03
Create Date: 2026-10-07 11:35:14.367253

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '20261007_01'
down_revision: Union[str, Sequence[str], None] = '20261006_03'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.drop_constraint(
        "ck_gerador_alternador_potencia",
        "gerador_alternadores",
        type_="check",
    )
    op.drop_constraint(
        "ck_gerador_alternador_corrente",
        "gerador_alternadores",
        type_="check",
    )

    op.alter_column(
        "gerador_alternadores",
        "potencia_kva",
        existing_type=sa.Numeric(12, 2),
        type_=sa.String(length=100),
        existing_nullable=True,
        postgresql_using="potencia_kva::text",
    )
    op.alter_column(
        "gerador_alternadores",
        "corrente_a",
        existing_type=sa.Numeric(12, 2),
        type_=sa.String(length=100),
        existing_nullable=True,
        postgresql_using="corrente_a::text",
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.execute(sa.text("""
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1
                FROM gerador_alternadores
                WHERE (
                    (
                        potencia_kva IS NOT NULL
                        AND BTRIM(potencia_kva) <> ''
                        AND BTRIM(potencia_kva)
                            !~ '^[0-9]+([.][0-9]+)?$'
                    )
                    OR
                    (
                        corrente_a IS NOT NULL
                        AND BTRIM(corrente_a) <> ''
                        AND BTRIM(corrente_a)
                            !~ '^[0-9]+([.][0-9]+)?$'
                    )
                )
            ) THEN
                RAISE EXCEPTION
                    'Downgrade bloqueado: potencia/corrente possuem valores textuais.';
            END IF;
        END $$;
    """))

    op.alter_column(
        "gerador_alternadores",
        "potencia_kva",
        existing_type=sa.String(length=100),
        type_=sa.Numeric(12, 2),
        existing_nullable=True,
        postgresql_using=(
            "NULLIF(BTRIM(potencia_kva), '')::numeric(12,2)"
        ),
    )
    op.alter_column(
        "gerador_alternadores",
        "corrente_a",
        existing_type=sa.String(length=100),
        type_=sa.Numeric(12, 2),
        existing_nullable=True,
        postgresql_using=(
            "NULLIF(BTRIM(corrente_a), '')::numeric(12,2)"
        ),
    )

    op.create_check_constraint(
        "ck_gerador_alternador_potencia",
        "gerador_alternadores",
        "potencia_kva IS NULL OR potencia_kva >= 0",
    )
    op.create_check_constraint(
        "ck_gerador_alternador_corrente",
        "gerador_alternadores",
        "corrente_a IS NULL OR corrente_a >= 0",
    )
