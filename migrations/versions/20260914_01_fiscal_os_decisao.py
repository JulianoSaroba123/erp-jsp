"""Fiscal foundation: decisao fiscal da ordem de servico.

Revision ID: 20260914_01
Revises: 20260912_01
Create Date: 2026-09-14
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260914_01"
down_revision = "20260912_01"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "ordem_servico",
        sa.Column(
            "situacao_fiscal",
            sa.String(length=30),
            nullable=False,
            server_default="PENDENTE",
        ),
    )

    op.add_column(
        "ordem_servico",
        sa.Column("motivo_nao_emissao", sa.Text(), nullable=True),
    )

    op.add_column(
        "ordem_servico",
        sa.Column("observacao_fiscal", sa.Text(), nullable=True),
    )

    op.add_column(
        "ordem_servico",
        sa.Column("decisao_fiscal_em", sa.DateTime(), nullable=True),
    )

    op.add_column(
        "ordem_servico",
        sa.Column("decisao_fiscal_usuario_id", sa.Integer(), nullable=True),
    )

    op.create_foreign_key(
        "fk_ordem_servico_decisao_fiscal_usuario",
        "ordem_servico",
        "usuarios",
        ["decisao_fiscal_usuario_id"],
        ["id"],
        ondelete="SET NULL",
    )

    op.create_index(
        "ix_ordem_servico_situacao_fiscal",
        "ordem_servico",
        ["situacao_fiscal"],
        unique=False,
    )

    op.create_table(
        "os_fiscal_historico",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("ordem_servico_id", sa.Integer(), nullable=False),
        sa.Column("situacao_anterior", sa.String(length=30), nullable=True),
        sa.Column("situacao_nova", sa.String(length=30), nullable=False),
        sa.Column("motivo", sa.Text(), nullable=True),
        sa.Column("observacao", sa.Text(), nullable=True),
        sa.Column("usuario_id", sa.Integer(), nullable=True),
        sa.Column(
            "criado_em",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.ForeignKeyConstraint(
            ["ordem_servico_id"],
            ["ordem_servico.id"],
            name="fk_os_fiscal_historico_ordem_servico",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["usuario_id"],
            ["usuarios.id"],
            name="fk_os_fiscal_historico_usuario",
            ondelete="SET NULL",
        ),
    )

    op.create_index(
        "ix_os_fiscal_historico_ordem_servico_id",
        "os_fiscal_historico",
        ["ordem_servico_id"],
        unique=False,
    )

    op.create_index(
        "ix_os_fiscal_historico_criado_em",
        "os_fiscal_historico",
        ["criado_em"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_os_fiscal_historico_criado_em",
        table_name="os_fiscal_historico",
    )

    op.drop_index(
        "ix_os_fiscal_historico_ordem_servico_id",
        table_name="os_fiscal_historico",
    )

    op.drop_table("os_fiscal_historico")

    op.drop_index(
        "ix_ordem_servico_situacao_fiscal",
        table_name="ordem_servico",
    )

    op.drop_constraint(
        "fk_ordem_servico_decisao_fiscal_usuario",
        "ordem_servico",
        type_="foreignkey",
    )

    op.drop_column("ordem_servico", "decisao_fiscal_usuario_id")
    op.drop_column("ordem_servico", "decisao_fiscal_em")
    op.drop_column("ordem_servico", "observacao_fiscal")
    op.drop_column("ordem_servico", "motivo_nao_emissao")
    op.drop_column("ordem_servico", "situacao_fiscal")
