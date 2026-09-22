"""Adiciona regime tributario nacional da DPS.

Revision ID: 20260916_01
Revises: 20260915_03
"""

from alembic import op
import sqlalchemy as sa


revision = "20260916_01"
down_revision = "20260915_03"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "configuracao_fiscal",
        sa.Column(
            "op_simp_nac",
            sa.String(length=1),
            nullable=True,
        ),
    )

    op.add_column(
        "configuracao_fiscal",
        sa.Column(
            "reg_ap_trib_sn",
            sa.String(length=1),
            nullable=True,
        ),
    )

    op.add_column(
        "configuracao_fiscal",
        sa.Column(
            "reg_esp_trib",
            sa.String(length=1),
            nullable=True,
        ),
    )


def downgrade():
    op.drop_column(
        "configuracao_fiscal",
        "reg_esp_trib",
    )

    op.drop_column(
        "configuracao_fiscal",
        "reg_ap_trib_sn",
    )

    op.drop_column(
        "configuracao_fiscal",
        "op_simp_nac",
    )
