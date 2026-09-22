"""Fiscal foundation: configuracao fiscal da empresa.

Revision ID: 20260915_01
Revises: 20260914_01
Create Date: 2026-09-15
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260915_01"
down_revision = "20260914_01"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "configuracao_fiscal",

        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),

        sa.Column(
            "configuracao_id",
            sa.Integer(),
            nullable=False,
        ),

        sa.Column("inscricao_municipal", sa.String(length=50), nullable=True),
        sa.Column("regime_tributario", sa.String(length=30), nullable=True),

        sa.Column(
            "optante_simples_nacional",
            sa.Boolean(),
            server_default=sa.text("false"),
            nullable=False,
        ),

        sa.Column("cnae_principal", sa.String(length=20), nullable=True),

        sa.Column(
            "codigo_servico_municipal",
            sa.String(length=30),
            nullable=True,
        ),

        sa.Column("codigo_lc116", sa.String(length=20), nullable=True),

        sa.Column(
            "aliquota_iss_padrao",
            sa.Numeric(precision=5, scale=2),
            nullable=True,
        ),

        sa.Column("municipio_ibge", sa.String(length=7), nullable=True),

        sa.Column(
            "ambiente",
            sa.String(length=20),
            server_default="HOMOLOGACAO",
            nullable=False,
        ),

        sa.Column("provider", sa.String(length=50), nullable=True),

        sa.Column(
            "serie_rps",
            sa.String(length=20),
            server_default="1",
            nullable=False,
        ),

        sa.Column(
            "proximo_rps",
            sa.Integer(),
            server_default="1",
            nullable=False,
        ),

        sa.Column(
            "integracao_ativa",
            sa.Boolean(),
            server_default=sa.text("false"),
            nullable=False,
        ),

        sa.Column("criado_em", sa.DateTime(), nullable=False),
        sa.Column("atualizado_em", sa.DateTime(), nullable=False),

        sa.Column(
            "ativo",
            sa.Boolean(),
            server_default=sa.text("true"),
            nullable=False,
        ),

        sa.CheckConstraint(
            "ambiente IN ('HOMOLOGACAO', 'PRODUCAO')",
            name="ck_config_fiscal_ambiente",
        ),

        sa.CheckConstraint(
            "aliquota_iss_padrao IS NULL OR "
            "(aliquota_iss_padrao >= 0 AND aliquota_iss_padrao <= 100)",
            name="ck_config_fiscal_aliquota_iss",
        ),

        sa.CheckConstraint(
            "proximo_rps >= 1",
            name="ck_config_fiscal_proximo_rps",
        ),

        sa.ForeignKeyConstraint(
            ["configuracao_id"],
            ["configuracao.id"],
            name="fk_config_fiscal_configuracao",
            ondelete="RESTRICT",
        ),

        sa.PrimaryKeyConstraint("id"),

        sa.UniqueConstraint(
            "configuracao_id",
            name="uq_config_fiscal_configuracao",
        ),
    )


def downgrade() -> None:
    op.drop_table("configuracao_fiscal")
