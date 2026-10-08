"""altera tensao nominal carregador para texto

Revision ID: cdbaf09054ac
Revises: 20261007_01
"""

from alembic import op
import sqlalchemy as sa


revision = "cdbaf09054ac"
down_revision = "20261007_01"
branch_labels = None
depends_on = None


def upgrade():
    op.execute(
        "ALTER TABLE gerador_carregadores "
        "DROP CONSTRAINT IF EXISTS ck_gerador_carregador_tensao"
    )

    op.alter_column(
        "gerador_carregadores",
        "tensao_nominal_v",
        existing_type=sa.Numeric(10, 2),
        type_=sa.String(100),
        existing_nullable=True,
        postgresql_using="tensao_nominal_v::text",
    )


def downgrade():
    bind = op.get_bind()

    invalidos = bind.execute(sa.text("""
        SELECT COUNT(*)
        FROM gerador_carregadores
        WHERE tensao_nominal_v IS NOT NULL
          AND BTRIM(tensao_nominal_v) <> ''
          AND BTRIM(tensao_nominal_v)
              !~ '^[0-9]+([.,][0-9]+)?$'
    """)).scalar()

    if invalidos:
        raise RuntimeError(
            "Downgrade bloqueado: existem tensoes nominais nao numericas."
        )

    op.alter_column(
        "gerador_carregadores",
        "tensao_nominal_v",
        existing_type=sa.String(100),
        type_=sa.Numeric(10, 2),
        existing_nullable=True,
        postgresql_using=(
            "NULLIF(REPLACE(BTRIM(tensao_nominal_v), ',', '.'), '')::numeric"
        ),
    )

    op.create_check_constraint(
        "ck_gerador_carregador_tensao",
        "gerador_carregadores",
        "tensao_nominal_v IS NULL OR tensao_nominal_v >= 0",
    )