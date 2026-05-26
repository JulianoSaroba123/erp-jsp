# -*- coding: utf-8 -*-
"""
ERP JSP v3.0 - Model de Itens do Orçamento
===========================================
Modelo para armazenar itens individuais do orçamento de projetos.
"""

from app.extensoes import db
from datetime import datetime

class OrcamentoItem(db.Model):
    """Modelo para itens do orçamento de energia solar"""
    __tablename__ = 'orcamento_itens'
    
    id = db.Column(db.Integer, primary_key=True)
    projeto_id = db.Column(db.Integer, nullable=False, index=True)
    
    # Dados do Item
    descricao = db.Column(db.String(300), nullable=False)
    categoria = db.Column(db.String(50))  # modulos, inversor, estrutura, custos_fixos, outros
    quantidade = db.Column(db.Numeric(10, 2), default=1)
    unidade_medida = db.Column(db.String(20), default='un')
    
    # Valores
    preco_unitario = db.Column(db.Numeric(10, 2), default=0)
    preco_total = db.Column(db.Numeric(10, 2), default=0)
    lucro_percentual = db.Column(db.Numeric(5, 2), default=0)
    faturamento = db.Column(db.Numeric(10, 2), default=0)
    
    # Controle
    ordem = db.Column(db.Integer, default=0)
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<OrcamentoItem {self.descricao}>'
    
    def calcular_totais(self):
        """Calcula valores totais do item"""
        self.preco_total = float(self.quantidade or 0) * float(self.preco_unitario or 0)
        self.faturamento = self.preco_total * (1 + (float(self.lucro_percentual or 0) / 100))
    
    def to_dict(self):
        """Converte para dicionário"""
        return {
            'id': self.id,
            'projeto_id': self.projeto_id,
            'descricao': self.descricao,
            'categoria': self.categoria,
            'quantidade': float(self.quantidade) if self.quantidade else 0,
            'unidade_medida': self.unidade_medida,
            'preco_unitario': float(self.preco_unitario) if self.preco_unitario else 0,
            'preco_total': float(self.preco_total) if self.preco_total else 0,
            'lucro_percentual': float(self.lucro_percentual) if self.lucro_percentual else 0,
            'faturamento': float(self.faturamento) if self.faturamento else 0,
            'ordem': self.ordem
        }
