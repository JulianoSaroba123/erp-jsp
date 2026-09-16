"""Fiscal foundation: idempotencia do documento NFS-e.

Revision ID: 20260915_03
Revises: 20260915_02
Create Date: 2026-09-15
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260915_03"
down_revision = "20260915_02"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "nfse_documento",
        sa.Column(
            "chave_idempotencia",
            sa.String(length=160),
            nullable=True,
        ),
    )

    op.create_unique_constraint(
        "uq_nfse_documento_chave_idempotencia",
        "nfse_documento",
        ["chave_idempotencia"],
    )


def downgrade() -> None:
    op.drop_constraint(
        "uq_nfse_documento_chave_idempotencia",
        "nfse_documento",
        type_="unique",
    )

    op.drop_column(
        "nfse_documento",
        "chave_idempotencia",
    )
