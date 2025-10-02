from datetime import date
from aplicacao.extensoes import db
from decimal import Decimal

class LancamentoFinanceiroOS(db.Model):
    __tablename__ = "financeiro_lancamentos_os"

    id = db.Column(db.Integer, primary_key=True)
    os_id = db.Column(db.Integer, db.ForeignKey("ordens_servico.id"), index=True)
    descricao = db.Column(db.String(255), nullable=False)
    valor = db.Column(db.Numeric(10, 2), nullable=False)
    data_vencimento = db.Column(db.Date, nullable=False)
    data_pagamento = db.Column(db.Date, nullable=True)
    forma_pagamento = db.Column(db.String(50))   # pix, dinheiro, boleto, cartao
    status = db.Column(db.String(20), default="Pendente")  # Pendente|Pago
    parcela = db.Column(db.Integer, nullable=True)         # 0..N (0 para entrada)
    total_parcelas = db.Column(db.Integer, nullable=True)
    
    # opcional: marca de origem/controle
    origem = db.Column(db.String(30), default="OS")
    
    # Relacionamento com a OS
    os = db.relationship('OrdemServico', backref='lancamentos_financeiros')
    
    # Propriedade para compatibilidade com o template
    @property
    def data(self):
        """Retorna data_vencimento para compatibilidade com template financeiro"""
        return self.data_vencimento
    
    @property
    def tipo(self):
        """Retorna tipo fixo para compatibilidade com template financeiro"""
        return "Receita"
    
    @property
    def categoria(self):
        """Retorna categoria baseada na origem"""
        return f"Ordem de Serviço (OS {self.os_id})"
    
    @property
    def is_from_os(self):
        """Indica que este lançamento é de uma Ordem de Serviço"""
        return True
    
    def __repr__(self):
        return f'<LancamentoFinanceiroOS {self.id} - OS {self.os_id} - {self.valor}>'
