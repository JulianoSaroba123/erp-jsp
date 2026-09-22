"""merge heads fiscal e main

Revision ID: 20260922_01
Revises: 20260916_01, 20260921_01
Create Date: 2026-09-21 22:12:48.620371

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '20260922_01'
down_revision: Union[str, Sequence[str], None] = ('20260916_01', '20260921_01')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
