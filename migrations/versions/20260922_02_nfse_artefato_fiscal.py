"""persiste artefato fiscal preparado da nfse

Revision ID: 20260922_02
Revises: 20260922_01
Create Date: 2026-09-21
"""

from alembic import op
import sqlalchemy as sa


revision = "20260922_02"
down_revision = "20260922_01"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "nfse_documento",
        sa.Column(
            "xml_envio",
            sa.LargeBinary(),
            nullable=True,
        ),
    )

    op.add_column(
        "nfse_documento",
        sa.Column(
            "xml_envio_sha256",
            sa.String(length=64),
            nullable=True,
        ),
    )

    op.add_column(
        "nfse_documento",
        sa.Column(
            "preparado_em",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
    )


def downgrade() -> None:
    op.drop_column(
        "nfse_documento",
        "preparado_em",
    )

    op.drop_column(
        "nfse_documento",
        "xml_envio_sha256",
    )

    op.drop_column(
        "nfse_documento",
        "xml_envio",
    )
