"""Adiciona identificadores idempotentes à importação de extratos.

Revision ID: 20260912_01
Revises: 20260803_01
Create Date: 2026-09-12
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260912_01"
down_revision = "20260803_01"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "extratos_bancarios",
        sa.Column("identificador_externo", sa.String(length=255), nullable=True),
    )
    op.add_column(
        "extratos_bancarios",
        sa.Column("fingerprint_importacao", sa.String(length=64), nullable=True),
    )

    op.create_index(
        "uq_extratos_bancarios_conta_fingerprint_importacao",
        "extratos_bancarios",
        ["conta_bancaria_id", "fingerprint_importacao"],
        unique=True,
    )
    op.create_index(
        "uq_extratos_bancarios_conta_identificador_externo",
        "extratos_bancarios",
        ["conta_bancaria_id", "identificador_externo"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index(
        "uq_extratos_bancarios_conta_identificador_externo",
        table_name="extratos_bancarios",
    )
    op.drop_index(
        "uq_extratos_bancarios_conta_fingerprint_importacao",
        table_name="extratos_bancarios",
    )
    op.drop_column("extratos_bancarios", "fingerprint_importacao")
    op.drop_column("extratos_bancarios", "identificador_externo")
