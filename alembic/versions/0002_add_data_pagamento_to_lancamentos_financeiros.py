"""add data_pagamento to lancamentos_financeiros

Revision ID: 0002_add_data_pagamento
Revises: 0001_add_apelido
Create Date: 2026-07-27 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0002_add_data_pagamento'
down_revision = '0001_add_apelido'
branch_labels = None
depends_on = None


def _column_exists(conn, table_name, column_name):
    inspector = sa.inspect(conn)
    return any(col['name'] == column_name for col in inspector.get_columns(table_name))


def upgrade():
    conn = op.get_bind()
    if not _column_exists(conn, 'lancamentos_financeiros', 'data_pagamento'):
        op.add_column('lancamentos_financeiros', sa.Column('data_pagamento', sa.Date(), nullable=True))


def downgrade():
    conn = op.get_bind()
    if _column_exists(conn, 'lancamentos_financeiros', 'data_pagamento'):
        op.drop_column('lancamentos_financeiros', 'data_pagamento')
