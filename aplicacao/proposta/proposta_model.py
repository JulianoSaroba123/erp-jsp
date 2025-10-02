from datetime import datetime
from aplicacao.extensoes import db

class Proposta(db.Model):
    __tablename__ = 'propostas'
    
    id = db.Column(db.Integer, primary_key=True)
    numero = db.Column(db.String(50), unique=True, nullable=False)
    
    # Cliente
    cliente_id = db.Column(db.Integer, db.ForeignKey('clientes.id'), nullable=False)
    cliente = db.relationship('Cliente', backref='propostas')
    
    # Informações básicas
    titulo = db.Column(db.String(200), nullable=False)
    descricao = db.Column(db.Text)
    
    # Status da proposta
    status = db.Column(db.String(50), nullable=False, default='Pendente')  # Pendente, Aprovada, Rejeitada, Expirada
    
    # Valores
    valor_total = db.Column(db.Numeric(10, 2), nullable=False, default=0.00)
    desconto = db.Column(db.Numeric(10, 2), default=0.00)
    valor_final = db.Column(db.Numeric(10, 2), nullable=False, default=0.00)
    
    # Condições comerciais
    forma_pagamento = db.Column(db.String(100))
    prazo_entrega = db.Column(db.String(100))
    condicoes_gerais = db.Column(db.Text)
    
    # Datas
    data_criacao = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    data_validade = db.Column(db.Date)
    data_aprovacao = db.Column(db.DateTime)
    data_exclusao = db.Column(db.DateTime)  # Soft delete
    
    # Observações internas
    observacoes_internas = db.Column(db.Text)
    
    def __repr__(self):
        return f'<Proposta {self.numero}: {self.titulo}>'
    
    def gerar_numero(self):
        """Gera número sequencial da proposta"""
        if not self.numero:
            ultimo_id = db.session.query(Proposta).count()
            self.numero = f"PROP-{ultimo_id + 1:06d}"
    
    @property
    def status_badge_class(self):
        """Retorna classe CSS para badge do status"""
        status_classes = {
            'Pendente': 'bg-warning',
            'Aprovada': 'bg-success',
            'Rejeitada': 'bg-danger',
            'Expirada': 'bg-secondary'
        }
        return status_classes.get(self.status, 'bg-secondary')
    
    def calcular_valor_final(self):
        """Calcula o valor final considerando desconto"""
        if self.valor_total and self.desconto:
            self.valor_final = self.valor_total - self.desconto
        else:
            self.valor_final = self.valor_total or 0.00

    def soft_delete(self):
        """Marca o registro como excluído sem removê-lo do banco"""
        self.data_exclusao = datetime.utcnow()

class PropostaItem(db.Model):
    """Itens da proposta (serviços e produtos)"""
    __tablename__ = 'proposta_itens'
    
    id = db.Column(db.Integer, primary_key=True)
    proposta_id = db.Column(db.Integer, db.ForeignKey('propostas.id'), nullable=False)
    proposta = db.relationship('Proposta', backref='itens')
    
    # Tipo do item
    tipo = db.Column(db.String(20), nullable=False)  # 'servico' ou 'produto'
    
    # Referências (pode ser serviço ou produto)
    servico_id = db.Column(db.Integer, db.ForeignKey('servicos.id'))
    produto_id = db.Column(db.Integer, db.ForeignKey('produtos.id'))
    
    # Detalhes do item
    descricao = db.Column(db.String(200), nullable=False)
    quantidade = db.Column(db.Numeric(8, 2), nullable=False, default=1.00)
    valor_unitario = db.Column(db.Numeric(10, 2), nullable=False)
    valor_total = db.Column(db.Numeric(10, 2), nullable=False)
    
    def __repr__(self):
        return f'<PropostaItem: {self.descricao}>'
    
    def calcular_total(self):
        """Calcula valor total do item"""
        if self.quantidade and self.valor_unitario:
            self.valor_total = self.quantidade * self.valor_unitario