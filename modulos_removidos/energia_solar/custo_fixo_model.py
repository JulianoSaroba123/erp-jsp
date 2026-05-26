"""
Modelo para Custos Padrão Solar - Catálogo de custos padrão para projetos
"""
from app.extensoes import db
from datetime import datetime


class CustoPadraoSolar(db.Model):
    """Custos padrão que aparecem automaticamente em novos projetos solares"""
    __tablename__ = 'custo_fixo'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Dados principais
    descricao = db.Column(db.String(200), nullable=False)
    unidade = db.Column(db.String(20), default='un')  # un, %, m², etc
    quantidade = db.Column(db.Float, default=1.0)
    valor_unitario = db.Column(db.Float, default=0.0)
    lucro_percentual = db.Column(db.Float, default=0.0)  # % lucro padrão
    faturamento = db.Column(db.String(50), default='EMPRESA')  # EMPRESA, FORNECEDOR, etc
    
    # Tipo de custo
    tipo = db.Column(db.String(50))  # COMISSAO, DESCONTO, CUSTO_FIXO, etc
    categoria = db.Column(db.String(50))  # Vendas, Administrativa, Técnica
    
    # Controle
    ativo = db.Column(db.Boolean, default=True)
    aplicar_automaticamente = db.Column(db.Boolean, default=True)  # Se deve aparecer em novos projetos
    data_cadastro = db.Column(db.DateTime, default=datetime.utcnow)
    data_atualizacao = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    observacoes = db.Column(db.Text)
    
    def to_dict(self):
        """Converte para dicionário para JSON"""
        return {
            'id': self.id,
            'descricao': self.descricao,
            'unidade': self.unidade,
            'qtd': self.quantidade,
            'valorUnit': self.valor_unitario,
            'lucro': self.lucro_percentual,
            'faturamento': self.faturamento,
            'tipo': self.tipo,
            'categoria': self.categoria
        }
    
    def __repr__(self):
        return f'<CustoPadraoSolar {self.descricao} - R$ {self.valor_unitario}>'
