"""add apelido to cliente

Revision ID: 0001_add_apelido
Revises: 
Create Date: 2025-09-10 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '0001_add_apelido'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()
    # only add the column if it doesn't exist to make migration idempotent
    inspector = sa.inspect(conn)
    cols = [c['name'] for c in inspector.get_columns('clientes')]
    if 'apelido' not in cols:
        op.add_column('clientes', sa.Column('apelido', sa.String(length=100), nullable=True))


def downgrade():
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    cols = [c['name'] for c in inspector.get_columns('clientes')]
    if 'apelido' in cols:
        op.drop_column('clientes', 'apelido')
