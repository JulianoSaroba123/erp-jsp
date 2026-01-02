"""
Modelos de Catálogo para Energia Solar
"""
from app.extensoes import db
from datetime import datetime


class PlacaSolar(db.Model):
    """Modelo para catálogo de placas solares"""
    __tablename__ = 'placa_solar'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Identificação
    modelo = db.Column(db.String(100), nullable=False)
    fabricante = db.Column(db.String(100), nullable=False)
    
    # Especificações Técnicas
    potencia = db.Column(db.Float, nullable=False)  # Watts
    comprimento = db.Column(db.Float)  # mm
    largura = db.Column(db.Float)  # mm
    espessura = db.Column(db.Float)  # mm
    peso = db.Column(db.Float)  # kg
    num_celulas = db.Column(db.Integer)  # 60, 72, 144, etc
    
    # Características Elétricas
    tensao_circuito_aberto = db.Column(db.Float)  # Voc
    corrente_curto_circuito = db.Column(db.Float)  # Isc
    tensao_maxima_potencia = db.Column(db.Float)  # Vmp
    corrente_maxima_potencia = db.Column(db.Float)  # Imp
    eficiencia = db.Column(db.Float)  # %
    
    # Coeficientes de Temperatura
    coef_temp_potencia = db.Column(db.Float)  # %/°C
    temp_operacao_nominal = db.Column(db.Float)  # NOCT
    
    # Garantias
    garantia_produto = db.Column(db.Integer)  # anos
    garantia_desempenho = db.Column(db.Integer)  # anos
    degradacao_ano1 = db.Column(db.Float)  # %
    degradacao_anual = db.Column(db.Float)  # %
    
    # Comercial
    preco_custo = db.Column(db.Float)
    preco_venda = db.Column(db.Float)
    fornecedor = db.Column(db.String(200))
    
    # Controle
    ativo = db.Column(db.Boolean, default=True)
    data_cadastro = db.Column(db.DateTime, default=datetime.utcnow)
    observacoes = db.Column(db.Text)
    
    def __repr__(self):
        return f'<PlacaSolar {self.fabricante} {self.modelo} - {self.potencia}W>'
    
    def area_m2(self):
        """Calcula área em m²"""
        if self.comprimento and self.largura:
            return (self.comprimento * self.largura) / 1000000
        return 2.0  # padrão
    
    def to_dict(self):
        return {
            'id': self.id,
            'modelo': self.modelo,
            'fabricante': self.fabricante,
            'potencia': self.potencia,
            'dimensoes': f"{self.comprimento}x{self.largura}mm",
            'num_celulas': self.num_celulas,
            'eficiencia': self.eficiencia,
            'preco_venda': self.preco_venda,
            'garantia_produto': self.garantia_produto
        }


class InversorSolar(db.Model):
    """Modelo para catálogo de inversores solares"""
    __tablename__ = 'inversor_solar'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Identificação
    modelo = db.Column(db.String(100), nullable=False)
    fabricante = db.Column(db.String(100), nullable=False)
    tipo = db.Column(db.String(50))  # String, Micro, Híbrido
    
    # Especificações Elétricas
    potencia_nominal = db.Column(db.Float, nullable=False)  # kW
    potencia_maxima = db.Column(db.Float)  # kW
    tensao_entrada_min = db.Column(db.Float)  # V
    tensao_entrada_max = db.Column(db.Float)  # V
    tensao_mppt_min = db.Column(db.Float)  # V
    tensao_mppt_max = db.Column(db.Float)  # V
    corrente_entrada_max = db.Column(db.Float)  # A
    num_mppt = db.Column(db.Integer)  # Número de rastreadores
    strings_por_mppt = db.Column(db.Integer)
    
    # Saída
    tensao_saida = db.Column(db.String(50))  # 127V, 220V, 380V
    fases = db.Column(db.String(20))  # Monofásico, Bifásico, Trifásico
    corrente_saida_max = db.Column(db.Float)  # A
    frequencia = db.Column(db.String(20))  # 60Hz
    
    # Características
    eficiencia_maxima = db.Column(db.Float)  # %
    eficiencia_europeia = db.Column(db.Float)  # %
    consumo_noturno = db.Column(db.Float)  # W
    
    # Proteções
    grau_protecao = db.Column(db.String(20))  # IP65, IP67
    temp_operacao_min = db.Column(db.Float)  # °C
    temp_operacao_max = db.Column(db.Float)  # °C
    
    # Físico
    peso = db.Column(db.Float)  # kg
    dimensoes = db.Column(db.String(100))  # LxAxP
    
    # Garantia
    garantia_anos = db.Column(db.Integer)
    
    # Comercial
    preco_custo = db.Column(db.Float)
    preco_venda = db.Column(db.Float)
    fornecedor = db.Column(db.String(200))
    
    # Controle
    ativo = db.Column(db.Boolean, default=True)
    data_cadastro = db.Column(db.DateTime, default=datetime.utcnow)
    observacoes = db.Column(db.Text)
    
    def __repr__(self):
        return f'<InversorSolar {self.fabricante} {self.modelo} - {self.potencia_nominal}kW>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'modelo': self.modelo,
            'fabricante': self.fabricante,
            'tipo': self.tipo,
            'potencia_nominal': self.potencia_nominal,
            'num_mppt': self.num_mppt,
            'eficiencia_maxima': self.eficiencia_maxima,
            'fases': self.fases,
            'preco_venda': self.preco_venda,
            'garantia_anos': self.garantia_anos
        }
