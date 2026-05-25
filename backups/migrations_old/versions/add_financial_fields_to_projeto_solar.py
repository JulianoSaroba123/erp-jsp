"""
Add financial fields to ProjetoSolar
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'add_financial_fields'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    op.add_column('projeto_solar', sa.Column('concessionaria_id', sa.Integer(), nullable=True))
    op.add_column('projeto_solar', sa.Column('tarifa_kwh', sa.Numeric(10, 4), nullable=True, server_default='0'))
    op.add_column('projeto_solar', sa.Column('economia_mensal', sa.Numeric(12, 2), nullable=True, server_default='0'))
    op.add_column('projeto_solar', sa.Column('economia_anual', sa.Numeric(12, 2), nullable=True, server_default='0'))
    op.add_column('projeto_solar', sa.Column('impostos_percentual', sa.Numeric(8, 2), nullable=True, server_default='0'))

def downgrade():
    op.drop_column('projeto_solar', 'concessionaria_id')
    op.drop_column('projeto_solar', 'tarifa_kwh')
    op.drop_column('projeto_solar', 'economia_mensal')
    op.drop_column('projeto_solar', 'economia_anual')
    op.drop_column('projeto_solar', 'impostos_percentual')