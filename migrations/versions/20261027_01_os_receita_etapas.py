"""Registro de receita por etapa de OS, sem preenchimento histórico automático."""
from alembic import op
import sqlalchemy as sa
revision = '20261027_01'
down_revision = '20261026_01'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('os_receita_etapas',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('ordem_servico_id', sa.Integer(), sa.ForeignKey('ordem_servico.id'), nullable=False),
        sa.Column('data_competencia', sa.Date(), nullable=False),
        sa.Column('descricao', sa.String(255), nullable=False),
        sa.Column('valor', sa.Numeric(12, 2), nullable=False),
        sa.Column('usuario', sa.String(100), nullable=False),
        sa.Column('chave_operacao', sa.String(64), nullable=False),
        sa.Column('usuario_estorno', sa.String(100)),
        sa.Column('motivo_estorno', sa.Text()),
        sa.Column('data_estorno', sa.DateTime()),
        sa.Column('criado_em', sa.DateTime(), nullable=False),
        sa.Column('atualizado_em', sa.DateTime(), nullable=False),
        sa.Column('ativo', sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.CheckConstraint('valor > 0', name='ck_os_receita_etapa_valor_positivo'),
        sa.UniqueConstraint('chave_operacao', name='uq_os_receita_etapa_operacao'))
    op.create_index('ix_os_receita_etapas_ordem_servico_id', 'os_receita_etapas', ['ordem_servico_id'])
    op.create_index('ix_os_receita_etapas_data_competencia', 'os_receita_etapas', ['data_competencia'])


def downgrade():
    if op.get_bind().execute(sa.text('SELECT COUNT(*) FROM os_receita_etapas')).scalar():
        raise RuntimeError('Downgrade bloqueado: existem etapas com histórico de reconhecimento.')
    op.drop_index('ix_os_receita_etapas_data_competencia', table_name='os_receita_etapas')
    op.drop_index('ix_os_receita_etapas_ordem_servico_id', table_name='os_receita_etapas')
    op.drop_table('os_receita_etapas')
