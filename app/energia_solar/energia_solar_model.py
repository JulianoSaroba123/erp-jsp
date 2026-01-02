"""
Modelo de dados para Cálculo de Energia Solar
"""
from app.extensoes import db
from datetime import datetime


class CalculoEnergiaSolar(db.Model):
    """Modelo para armazenar cálculos de sistemas de energia solar"""
    __tablename__ = 'calculo_energia_solar'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Dados do Cliente
    cliente_id = db.Column(db.Integer, db.ForeignKey('cliente.id'), nullable=True)
    nome_cliente = db.Column(db.String(200))
    
    # Dados de Consumo
    consumo_mensal = db.Column(db.Float, nullable=False)  # kWh/mês
    tarifa_energia = db.Column(db.Float, nullable=False)  # R$/kWh
    
    # Localização
    cidade = db.Column(db.String(100))
    estado = db.Column(db.String(2))
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)
    irradiacao_media = db.Column(db.Float)  # kWh/m²/dia
    
    # Sistema Calculado
    potencia_sistema = db.Column(db.Float)  # kWp
    numero_paineis = db.Column(db.Integer)
    potencia_painel = db.Column(db.Float)  # W
    area_necessaria = db.Column(db.Float)  # m²
    
    # Inversores
    tipo_inversor = db.Column(db.String(50))  # String, Micro, Híbrido
    potencia_inversor = db.Column(db.Float)  # kW
    numero_inversores = db.Column(db.Integer)
    
    # Estimativas
    geracao_mensal = db.Column(db.Float)  # kWh/mês
    economia_mensal = db.Column(db.Float)  # R$/mês
    economia_anual = db.Column(db.Float)  # R$/ano
    
    # Investimento
    custo_total = db.Column(db.Float)  # R$
    payback_anos = db.Column(db.Float)  # anos
    roi_25anos = db.Column(db.Float)  # %
    
    # Observações
    observacoes = db.Column(db.Text)
    tipo_instalacao = db.Column(db.String(50))  # Telhado, Solo, Carport
    orientacao = db.Column(db.String(20))  # Norte, Sul, Leste, Oeste
    inclinacao = db.Column(db.Float)  # graus
    
    # Controle
    data_calculo = db.Column(db.DateTime, default=datetime.utcnow)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'))
    status = db.Column(db.String(20), default='calculado')  # calculado, aprovado, instalado
    
    # Relacionamentos
    cliente = db.relationship('Cliente', backref='calculos_solar', foreign_keys=[cliente_id])
    usuario = db.relationship('Usuario', backref='calculos_solar')
    
    def __repr__(self):
        return f'<CalculoEnergiaSolar {self.nome_cliente} - {self.potencia_sistema}kWp>'
    
    def to_dict(self):
        """Converte o objeto para dicionário"""
        return {
            'id': self.id,
            'cliente_id': self.cliente_id,
            'nome_cliente': self.nome_cliente,
            'consumo_mensal': self.consumo_mensal,
            'tarifa_energia': self.tarifa_energia,
            'potencia_sistema': self.potencia_sistema,
            'numero_paineis': self.numero_paineis,
            'geracao_mensal': self.geracao_mensal,
            'economia_mensal': self.economia_mensal,
            'custo_total': self.custo_total,
            'payback_anos': self.payback_anos,
            'data_calculo': self.data_calculo.strftime('%d/%m/%Y %H:%M'),
            'status': self.status
        }
