

from aplicacao.extensoes import db
from datetime import datetime, date

from .financeiro_compat import normalizar_status, normalizar_tipo

class LancamentoFinanceiro(db.Model):
    __tablename__ = 'lancamentos_financeiros'

    id = db.Column(db.Integer, primary_key=True)
    tipo = db.Column(db.String(20), nullable=False)              # 'Receita' ou 'Despesa'
    categoria = db.Column(db.String(100), nullable=False)
    descricao = db.Column(db.String(255), nullable=False)
    valor = db.Column(db.Float, nullable=False, default=0.0)
    data = db.Column(db.Date, nullable=False, default=date.today)
    data_pagamento = db.Column(db.Date, nullable=True)
    forma_pagamento = db.Column(db.String(50))
    status = db.Column(db.String(20), nullable=False, default='Pendente')  # 'Pendente', 'Pago', 'Atrasado'
    observacoes = db.Column(db.Text)

    def is_receita(self): return normalizar_tipo(self.tipo) == 'Receita'
    def is_despesa(self): return normalizar_tipo(self.tipo) == 'Despesa'

    @property
    def status_normalizado(self):
        return normalizar_status(self.status)

    @property
    def tipo_normalizado(self):
        return normalizar_tipo(self.tipo)
    
    @property
    def is_from_os(self):
        """Indica que este lançamento NÃO é de uma Ordem de Serviço"""
        return False

    def __repr__(self):
        return f'<LancamentoFinanceiro {self.tipo} {self.valor:.2f}>'

