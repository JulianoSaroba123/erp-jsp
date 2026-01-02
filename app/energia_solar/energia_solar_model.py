"""
Modelo de dados para Cálculo de Energia Solar - Versão Completa GOORU
"""
from app.extensoes import db
from datetime import datetime


class CalculoEnergiaSolar(db.Model):
    """Modelo para armazenar cálculos completos de sistemas de energia solar"""
    __tablename__ = 'calculo_energia_solar'
    
    id = db.Column(db.Integer, primary_key=True)
    numero_projeto = db.Column(db.String(50), unique=True)  # ID único do projeto
    
    # Dados do Cliente
    cliente_id = db.Column(db.Integer, nullable=True)
    nome_cliente = db.Column(db.String(200))
    local_instalacao = db.Column(db.String(300))  # Endereço completo
    
    local_instalacao = db.Column(db.String(300))  # Endereço completo
    
    # Dados de Consumo
    consumo_mensal = db.Column(db.Float, nullable=False)  # kWh/mês
    consumo_anual = db.Column(db.Float)  # kWh/ano
    tarifa_energia = db.Column(db.Float, nullable=False)  # R$/kWh (sem impostos)
    
    # Histórico de Consumo (12 meses) - JSON
    historico_consumo_json = db.Column(db.Text)  # JSON array [mes1, mes2, ...]
    
    # Custos Adicionais da Energia
    iluminacao_publica = db.Column(db.Float, default=0)  # R$
    demais_custos = db.Column(db.Float, default=0)  # R$
    fatura_minima = db.Column(db.Float, default=0)  # R$
    taxa_disponibilidade = db.Column(db.Float, default=50)  # kWh
    
    # Parâmetros Financeiros
    simultaneidade = db.Column(db.Float, default=35.0)  # % consumo simultâneo
    reajuste_anual_energia = db.Column(db.Float, default=10.0)  # % ao ano
    perda_eficiencia_anual = db.Column(db.Float, default=0.0)  # % degradação painéis
    vida_util_sistema = db.Column(db.Integer, default=25)  # anos
    
    vida_util_sistema = db.Column(db.Integer, default=25)  # anos
    
    # Localização
    cidade = db.Column(db.String(100))
    estado = db.Column(db.String(2))
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)
    irradiacao_media = db.Column(db.Float)  # kWh/m²/dia
    irradiacao_mensal_json = db.Column(db.Text)  # JSON dos 12 meses
    cliente_grupo = db.Column(db.String(10))  # A, B, etc
    
    # Equipamentos Selecionados
    placa_id = db.Column(db.Integer)  # FK para PlacaSolar
    placa_modelo = db.Column(db.String(100))
    placa_fabricante = db.Column(db.String(100))
    placa_potencia = db.Column(db.Float)  # W
    placa_comprimento = db.Column(db.Float)  # mm
    placa_largura = db.Column(db.Float)  # mm
    placa_num_celulas = db.Column(db.Integer)
    
    inversor_id = db.Column(db.Integer)  # FK para InversorSolar
    inversor_modelo = db.Column(db.String(100))
    inversor_fabricante = db.Column(db.String(100))
    inversor_potencia = db.Column(db.Float)  # kW
    inversor_tipo = db.Column(db.String(50))  # String, Micro, Híbrido
    
    # Sistema Calculado
    potencia_sistema = db.Column(db.Float)  # kWp
    numero_paineis = db.Column(db.Integer)
    numero_inversores = db.Column(db.Integer)
    area_necessaria = db.Column(db.Float)  # m²
    producao_especifica = db.Column(db.Float)  # kWh/kWp.ano
    
    producao_especifica = db.Column(db.Float)  # kWh/kWp.ano
    
    # Instalação Elétrica
    circuito = db.Column(db.String(20))  # Monofásico, Bifásico, Trifásico
    tensao_instalacao = db.Column(db.String(20))  # 127V, 220V, 380V
    qtd_placas_instalacao = db.Column(db.Integer)
    qtd_inversores_instalacao = db.Column(db.Integer)
    disjuntor = db.Column(db.String(20))  # 63 A, etc
    cabo_fase = db.Column(db.String(20))  # 2x16 mm²
    cabo_neutro = db.Column(db.String(20))
    cabo_aterramento = db.Column(db.String(20))
    posicao_placas = db.Column(db.String(20))  # Retrato, Paisagem
    disposicao = db.Column(db.String(10))  # 6 x 1, etc
    area_instalacao = db.Column(db.Float)  # m²
    
    # Estimativas de Geração
    geracao_mensal = db.Column(db.Float)  # kWh/mês
    geracao_anual = db.Column(db.Float)  # kWh/ano
    geracao_mensal_json = db.Column(db.Text)  # JSON dos 12 meses
    
    geracao_mensal_json = db.Column(db.Text)  # JSON dos 12 meses
    
    # Economia
    economia_mensal = db.Column(db.Float)  # R$/mês
    economia_anual = db.Column(db.Float)  # R$/ano
    economia_25anos = db.Column(db.Float)  # R$ total
    
    # Lei 14.300 (Antes e Depois)
    economia_antes_lei = db.Column(db.Float)  # R$/ano
    economia_depois_lei = db.Column(db.Float)  # R$/ano
    
    # Investimento e Retorno
    custo_total = db.Column(db.Float)  # R$
    valor_nota_fiscal = db.Column(db.Float)  # R$
    valor_faturado_empresa = db.Column(db.Float)  # R$
    valor_faturado_cliente = db.Column(db.Float)  # R$
    impostos = db.Column(db.Float)  # R$
    lucro = db.Column(db.Float)  # R$
    percentual_lucro = db.Column(db.Float)  # %
    
    payback_anos = db.Column(db.Float)  # anos
    payback_meses = db.Column(db.Integer)  # meses
    roi = db.Column(db.Float)  # retorno sobre investimento (múltiplo)
    roi_percentual = db.Column(db.Float)  # %
    
    roi_percentual = db.Column(db.Float)  # %
    
    # Financiamento
    valor_financiado = db.Column(db.Float)  # R$
    periodo_financiamento = db.Column(db.Integer)  # meses
    juros_mensal = db.Column(db.Float)  # %
    parcela_mensal = db.Column(db.Float)  # R$
    
    # Observações e Configurações
    observacoes = db.Column(db.Text)
    tipo_instalacao = db.Column(db.String(50))  # Telhado, Solo, Carport
    orientacao = db.Column(db.String(20))  # Norte, Sul, Leste, Oeste
    inclinacao = db.Column(db.Float)  # graus
    
    # Controle
    data_calculo = db.Column(db.DateTime, default=datetime.utcnow)
    data_prevista_entrega = db.Column(db.Date)
    usuario_id = db.Column(db.Integer, nullable=True)
    status = db.Column(db.String(20), default='em_aberto')  # em_aberto, a_visitar, aprovado, instalado
    etapa_projeto = db.Column(db.String(20), default='calculo')  # calculo, orcamento, contrato, instalacao
    
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
