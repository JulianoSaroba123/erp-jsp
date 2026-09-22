"""Fiscal foundation: documento seguro de NFS-e.

Revision ID: 20260915_02
Revises: 20260915_01
Create Date: 2026-09-15
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260915_02"
down_revision = "20260915_01"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "nfse_documento",

        sa.Column(
            "id",
            sa.Integer(),
            autoincrement=True,
            nullable=False,
        ),

        sa.Column(
            "ordem_servico_id",
            sa.Integer(),
            nullable=False,
        ),

        sa.Column(
            "configuracao_fiscal_id",
            sa.Integer(),
            nullable=False,
        ),

        sa.Column(
            "status",
            sa.String(length=30),
            server_default="RASCUNHO",
            nullable=False,
        ),

        sa.Column(
            "ambiente",
            sa.String(length=20),
            server_default="HOMOLOGACAO",
            nullable=False,
        ),

        sa.Column(
            "provider",
            sa.String(length=50),
            nullable=True,
        ),

        sa.Column(
            "serie_rps",
            sa.String(length=20),
            nullable=True,
        ),

        sa.Column(
            "numero_rps",
            sa.Integer(),
            nullable=True,
        ),

        sa.Column(
            "numero_nfse",
            sa.String(length=50),
            nullable=True,
        ),

        sa.Column(
            "protocolo",
            sa.String(length=100),
            nullable=True,
        ),

        sa.Column(
            "codigo_verificacao",
            sa.String(length=100),
            nullable=True,
        ),

        sa.Column(
            "chave_acesso",
            sa.String(length=100),
            nullable=True,
        ),

        sa.Column(
            "mensagem_status",
            sa.Text(),
            nullable=True,
        ),

        sa.Column(
            "criado_em",
            sa.DateTime(),
            nullable=False,
        ),

        sa.Column(
            "atualizado_em",
            sa.DateTime(),
            nullable=False,
        ),

        sa.Column(
            "ativo",
            sa.Boolean(),
            server_default=sa.text("true"),
            nullable=False,
        ),

        sa.CheckConstraint(
            "status IN ("
            "'RASCUNHO', "
            "'PREPARADA', "
            "'PENDENTE_ENVIO', "
            "'PROCESSANDO', "
            "'AUTORIZADA', "
            "'REJEITADA', "
            "'CANCELADA'"
            ")",
            name="ck_nfse_documento_status",
        ),

        sa.CheckConstraint(
            "ambiente IN ('HOMOLOGACAO', 'PRODUCAO')",
            name="ck_nfse_documento_ambiente",
        ),

        sa.CheckConstraint(
            "numero_rps IS NULL OR numero_rps >= 1",
            name="ck_nfse_documento_numero_rps",
        ),

        sa.ForeignKeyConstraint(
            ["ordem_servico_id"],
            ["ordem_servico.id"],
            name="fk_nfse_documento_ordem_servico",
            ondelete="RESTRICT",
        ),

        sa.ForeignKeyConstraint(
            ["configuracao_fiscal_id"],
            ["configuracao_fiscal.id"],
            name="fk_nfse_documento_config_fiscal",
            ondelete="RESTRICT",
        ),

        sa.PrimaryKeyConstraint("id"),

        sa.UniqueConstraint(
            "serie_rps",
            "numero_rps",
            name="uq_nfse_documento_serie_numero_rps",
        ),
    )

    op.create_index(
        "ix_nfse_documento_ordem_servico_id",
        "nfse_documento",
        ["ordem_servico_id"],
        unique=False,
    )

    op.create_index(
        "ix_nfse_documento_configuracao_fiscal_id",
        "nfse_documento",
        ["configuracao_fiscal_id"],
        unique=False,
    )

    op.create_index(
        "ix_nfse_documento_status",
        "nfse_documento",
        ["status"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_nfse_documento_status",
        table_name="nfse_documento",
    )

    op.drop_index(
        "ix_nfse_documento_configuracao_fiscal_id",
        table_name="nfse_documento",
    )

    op.drop_index(
        "ix_nfse_documento_ordem_servico_id",
        table_name="nfse_documento",
    )

    op.drop_table("nfse_documento")
