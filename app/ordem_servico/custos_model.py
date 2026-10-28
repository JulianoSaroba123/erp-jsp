"""Custos administrativos: não são lançamentos financeiros nem eventos bancários."""
from app.extensoes import db
from app.models import BaseModel


class CustoOrdemServico(BaseModel):
    __tablename__ = 'os_custos_internos'
    __table_args__ = (
        db.CheckConstraint("situacao IN ('realizado','estimado','nao_informado')", name='ck_os_custo_situacao'),
        db.CheckConstraint("modalidade IN ('hora','diaria','servico','unidade')", name='ck_os_custo_modalidade'),
        db.CheckConstraint("categoria IN ('mao_obra','material','deslocamento','alimentacao','terceirizacao','outros','tributos')", name='ck_os_custo_categoria'),
        db.CheckConstraint("(situacao = 'nao_informado' AND valor IS NULL) OR (situacao <> 'nao_informado' AND valor IS NOT NULL AND valor >= 0)", name='ck_os_custo_valor'),
        db.CheckConstraint("quantidade > 0", name='ck_os_custo_quantidade'),
        db.CheckConstraint("lancamento_id IS NULL OR (situacao = 'realizado' AND valor > 0)", name='ck_os_custo_rateio'),
        db.UniqueConstraint('chave_operacao', name='uq_os_custo_operacao'),
    )
    # OS nula significa serviços internos; não se cria uma OS artificial.
    ordem_servico_id = db.Column(db.Integer, db.ForeignKey('ordem_servico.id', ondelete='RESTRICT'), index=True)
    apontamento_id = db.Column(db.Integer, db.ForeignKey('ordem_servico_colaborador.id', ondelete='RESTRICT'), index=True)
    colaborador_id = db.Column(db.Integer, db.ForeignKey('colaborador.id', ondelete='RESTRICT'))
    produto_os_id = db.Column(db.Integer, db.ForeignKey('ordem_servico_produtos.id', ondelete='RESTRICT'))
    lancamento_id = db.Column(db.Integer, db.ForeignKey('lancamentos_financeiros.id', ondelete='RESTRICT'), index=True)
    categoria = db.Column(db.String(30), nullable=False)
    modalidade = db.Column(db.String(15), nullable=False)
    descricao = db.Column(db.String(255), nullable=False)
    data_custo = db.Column(db.Date, nullable=False)
    quantidade = db.Column(db.Numeric(12, 3), nullable=False)
    valor = db.Column(db.Numeric(12, 2))  # total histórico explícito, nunca preço atual do produto
    situacao = db.Column(db.String(20), nullable=False)
    fonte_custo = db.Column(db.String(255), nullable=False)
    chave_operacao = db.Column(db.String(64), nullable=False)
    versao = db.Column(db.Integer, nullable=False, default=1, server_default='1')
    assinatura = db.Column(db.String(64), nullable=False)
    colaborador = db.relationship('Colaborador')
    lancamento = db.relationship('LancamentoFinanceiro')


db.Index('uq_os_custo_ativo_assinatura', CustoOrdemServico.assinatura, unique=True,
    postgresql_where=CustoOrdemServico.ativo.is_(True), sqlite_where=CustoOrdemServico.ativo.is_(True))


class EventoCustoInterno(BaseModel):
    __tablename__ = 'os_custos_auditoria'
    entidade = db.Column(db.String(20), nullable=False)
    registro_id = db.Column(db.Integer, nullable=False, index=True)
    ordem_servico_id = db.Column(db.Integer, db.ForeignKey('ordem_servico.id', ondelete='RESTRICT'), index=True)
    usuario = db.Column(db.String(100), nullable=False)
    operacao = db.Column(db.String(30), nullable=False)
    motivo = db.Column(db.String(1000), nullable=False)
    anterior = db.Column(db.Text, nullable=False)
    novo = db.Column(db.Text, nullable=False)

# Protege os vínculos nos caminhos ORM existentes, além dos locks do serviço.
from sqlalchemy import event, inspect, select, or_


@event.listens_for(CustoOrdemServico, 'before_delete')
@event.listens_for(EventoCustoInterno, 'before_delete')
@event.listens_for(EventoCustoInterno, 'before_update')
def preservar_historico(mapper, connection, target):
    raise ValueError('Custos e auditoria internos não podem ser excluídos ou ter o histórico alterado.')


def proteger_pagamento_com_rateio(mapper, connection, target):
    campos = [c.name for c in target.__table__.columns if c.name not in {'atualizado_em', 'usuario_editor', 'data_edicao_auditoria'}]
    if not any(inspect(target).attrs[c].history.has_changes() for c in campos):
        return
    if not inspect(connection).has_table('os_custos_internos'):
        return
    if connection.execute(select(CustoOrdemServico.id).where(CustoOrdemServico.lancamento_id == target.id).limit(1)).first():
        raise ValueError('Pagamento possui rateio ou histórico de custos. Use revisão administrativa; o pagamento original deve ser preservado.')


from app.financeiro.financeiro_model import LancamentoFinanceiro
from app.ordem_servico.ordem_servico_model import OrdemServicoProduto
from app.colaborador.colaborador_model import OrdemServicoColaborador

event.listen(LancamentoFinanceiro, 'before_update', proteger_pagamento_com_rateio)


@event.listens_for(OrdemServicoProduto, 'before_delete')
@event.listens_for(OrdemServicoColaborador, 'before_delete')
def proteger_origem_custo(mapper, connection, target):
    coluna = CustoOrdemServico.apontamento_id if isinstance(target, OrdemServicoColaborador) else CustoOrdemServico.produto_os_id
    if inspect(connection).has_table('os_custos_internos') and connection.execute(select(CustoOrdemServico.id).where(coluna == target.id).limit(1)).first():
        raise ValueError('Registro possui custo histórico vinculado; a exclusão física não é permitida.')


@event.listens_for(OrdemServicoProduto, 'before_update')
def proteger_material_historico(mapper, connection, target):
    if not any(inspect(target).attrs[c].history.has_changes() for c in ('produto_id','descricao','quantidade','ordem_servico_id')):
        return
    if inspect(connection).has_table('os_custos_internos') and connection.execute(select(CustoOrdemServico.id).where(CustoOrdemServico.produto_os_id == target.id).limit(1)).first():
        raise ValueError('Material possui custo histórico vinculado. Preserve sua identificação e quantidade.')
