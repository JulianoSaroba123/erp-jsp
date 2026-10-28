"""Custos e rateios administrativos; aditiva, sem backfill financeiro.

Revision ID: 20261028_01
Revises: 20261026_01
Branch própria: usar os_custos@head, independente das etapas da PR48.
"""
from alembic import op
import sqlalchemy as sa

revision = '20261028_01'
down_revision = '20261026_01'
branch_labels = ('os_custos',)
depends_on = None


def comuns():
    return [sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('criado_em', sa.DateTime(), nullable=False),
        sa.Column('atualizado_em', sa.DateTime(), nullable=False),
        sa.Column('ativo', sa.Boolean(), nullable=False, server_default=sa.true())]


def upgrade():
    op.create_table('os_custos_internos', *comuns(),
        sa.Column('ordem_servico_id', sa.Integer(), sa.ForeignKey('ordem_servico.id', ondelete='RESTRICT')),
        sa.Column('apontamento_id', sa.Integer(), sa.ForeignKey('ordem_servico_colaborador.id', ondelete='RESTRICT')),
        sa.Column('colaborador_id', sa.Integer(), sa.ForeignKey('colaborador.id', ondelete='RESTRICT')),
        sa.Column('produto_os_id', sa.Integer(), sa.ForeignKey('ordem_servico_produtos.id', ondelete='RESTRICT')),
        sa.Column('lancamento_id', sa.Integer(), sa.ForeignKey('lancamentos_financeiros.id', ondelete='RESTRICT')),
        sa.Column('categoria', sa.String(30), nullable=False),
        sa.Column('modalidade', sa.String(15), nullable=False),
        sa.Column('descricao', sa.String(255), nullable=False),
        sa.Column('data_custo', sa.Date(), nullable=False),
        sa.Column('quantidade', sa.Numeric(12,3), nullable=False),
        sa.Column('valor', sa.Numeric(12,2)),
        sa.Column('situacao', sa.String(20), nullable=False),
        sa.Column('fonte_custo', sa.String(255), nullable=False),
        sa.Column('chave_operacao', sa.String(64), nullable=False),
        sa.Column('versao', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('assinatura', sa.String(64), nullable=False),
        sa.CheckConstraint("situacao IN ('realizado','estimado','nao_informado')", name='ck_os_custo_situacao'),
        sa.CheckConstraint("modalidade IN ('hora','diaria','servico','unidade')", name='ck_os_custo_modalidade'),
        sa.CheckConstraint("categoria IN ('mao_obra','material','deslocamento','alimentacao','terceirizacao','outros','tributos')", name='ck_os_custo_categoria'),
        sa.CheckConstraint("(situacao = 'nao_informado' AND valor IS NULL) OR (situacao <> 'nao_informado' AND valor IS NOT NULL AND valor >= 0)", name='ck_os_custo_valor'),
        sa.CheckConstraint('quantidade > 0', name='ck_os_custo_quantidade'),
        sa.CheckConstraint("lancamento_id IS NULL OR (situacao = 'realizado' AND valor > 0)", name='ck_os_custo_rateio'),
        sa.UniqueConstraint('chave_operacao', name='uq_os_custo_operacao'))
    for campo in ('ordem_servico_id','apontamento_id','lancamento_id'):
        op.create_index('ix_os_custos_internos_' + campo, 'os_custos_internos', [campo])
    op.create_index('uq_os_custo_ativo_assinatura', 'os_custos_internos', ['assinatura'], unique=True,
        postgresql_where=sa.text('ativo = true'), sqlite_where=sa.text('ativo = 1'))
    op.create_table('os_custos_auditoria', *comuns(),
        sa.Column('entidade', sa.String(20), nullable=False),
        sa.Column('registro_id', sa.Integer(), nullable=False),
        sa.Column('ordem_servico_id', sa.Integer(), sa.ForeignKey('ordem_servico.id', ondelete='RESTRICT')),
        sa.Column('usuario', sa.String(100), nullable=False),
        sa.Column('operacao', sa.String(30), nullable=False),
        sa.Column('motivo', sa.String(1000), nullable=False),
        sa.Column('anterior', sa.Text(), nullable=False),
        sa.Column('novo', sa.Text(), nullable=False))
    for campo in ('ordem_servico_id','registro_id'):
        op.create_index('ix_os_custos_auditoria_' + campo, 'os_custos_auditoria', [campo])


def downgrade():
    bind = op.get_bind()
    for tabela in ('os_custos_internos','os_custos_auditoria'):
        if bind.execute(sa.text('SELECT COUNT(*) FROM ' + tabela)).scalar():
            raise RuntimeError('Reversão bloqueada: custos ou histórico existentes. Preserve os dados e reverta somente a aplicação.')
    op.drop_table('os_custos_auditoria')
    op.drop_table('os_custos_internos')
