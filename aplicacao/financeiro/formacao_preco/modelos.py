from aplicacao.extensoes import db
from sqlalchemy import Column, Integer, Float, JSON, DateTime
from datetime import datetime
import json

class FormacaoPrecoConfig(db.Model):
    """Modelo para armazenar configurações de formação de preço"""
    __tablename__ = 'formacao_preco_config'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Custos fixos mensais (JSON: {"aluguel": 1500, "energia": 300, ...})
    custos_fixos_mensais = db.Column(db.JSON, default=dict)
    
    # Custo variável por hora (material, deslocamento, etc.)
    custo_variavel_hora = db.Column(db.Float, default=0.0)
    
    # Preço médio praticado no mercado
    preco_medio_praticado = db.Column(db.Float, default=0.0)
    
    # Margem de lucro desejada (%)
    margem_desejada = db.Column(db.Float, default=30.0)
    
    # Horas de trabalho por mês
    horas_trabalho_mes = db.Column(db.Integer, default=160)
    
    # Metadados
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)
    atualizado_em = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __init__(self):
        self.custos_fixos_mensais = {
            'aluguel': 0.0,
            'energia': 0.0,
            'internet': 0.0,
            'telefone': 0.0,
            'contador': 0.0,
            'seguro': 0.0,
            'outros': 0.0
        }
    
    @classmethod
    def get_or_create_default(cls):
        """Retorna a configuração existente ou cria uma padrão"""
        config = cls.query.first()
        if not config:
            config = cls()
            db.session.add(config)
            db.session.commit()
        return config
    
    @property 
    def total_custos_fixos(self):
        """Calcula o total dos custos fixos mensais"""
        if not self.custos_fixos_mensais:
            return 0.0
        return sum(self.custos_fixos_mensais.values())
    
    @property
    def custo_fixo_por_hora(self):
        """Calcula o custo fixo por hora"""
        if self.horas_trabalho_mes <= 0:
            return 0.0
        return self.total_custos_fixos / self.horas_trabalho_mes
    
    @property
    def custo_total_por_hora(self):
        """Calcula o custo total por hora (fixo + variável)"""
        return self.custo_fixo_por_hora + self.custo_variavel_hora
    
    @property
    def margem_atual_percentual(self):
        """Calcula a margem atual em %"""
        if self.preco_medio_praticado <= 0 or self.custo_total_por_hora <= 0:
            return 0.0
        
        margem = ((self.preco_medio_praticado - self.custo_total_por_hora) / self.preco_medio_praticado) * 100
        return max(0, margem)  # Não pode ser negativa
    
    def to_dict(self):
        """Converte para dicionário para JSON"""
        return {
            'id': self.id,
            'custos_fixos_mensais': self.custos_fixos_mensais or {},
            'custo_variavel_hora': self.custo_variavel_hora,
            'preco_medio_praticado': self.preco_medio_praticado,
            'margem_desejada': self.margem_desejada,
            'horas_trabalho_mes': self.horas_trabalho_mes,
            'total_custos_fixos': self.total_custos_fixos,
            'custo_fixo_por_hora': self.custo_fixo_por_hora,
            'custo_total_por_hora': self.custo_total_por_hora,
            'margem_atual_percentual': self.margem_atual_percentual
        }

def calcular_ponto_equilibrio(config):
    """
    Calcula o ponto de equilíbrio baseado na configuração
    
    Returns:
        dict: Resultado com métricas do ponto de equilíbrio
    """
    
    # Validações básicas
    if not config or config.horas_trabalho_mes <= 0:
        return {
            'erro': 'Configuração inválida: horas de trabalho deve ser maior que 0',
            'status': 'erro'
        }
    
    # Cálculos básicos
    total_custos_fixos = config.total_custos_fixos
    custo_fixo_hora = config.custo_fixo_por_hora
    custo_variavel_hora = config.custo_variavel_hora
    custo_total_hora = config.custo_total_por_hora
    
    # Preço mínimo para cobrir custos (ponto de equilíbrio)
    preco_minimo_hora = custo_total_hora
    
    # Para atingir a margem desejada
    if config.margem_desejada > 0:
        # Preço = Custo / (1 - Margem/100)
        preco_com_margem = custo_total_hora / (1 - config.margem_desejada / 100)
    else:
        preco_com_margem = custo_total_hora
    
    # Faturamento mínimo necessário
    faturamento_minimo_mes = total_custos_fixos
    
    # Horas mínimas para equilibrio
    if config.preco_medio_praticado > custo_variavel_hora:
        # Ponto de equilíbrio: Custos Fixos / (Preço - Custo Variável)
        horas_minimas_equilibrio = total_custos_fixos / (config.preco_medio_praticado - custo_variavel_hora)
    else:
        horas_minimas_equilibrio = float('inf')  # Impossível atingir equilibrio
    
    # Faturamento com preço atual
    faturamento_atual_mes = config.preco_medio_praticado * config.horas_trabalho_mes
    
    # Margem atual vs desejada
    margem_atual = config.margem_atual_percentual
    diferenca_margem = margem_atual - config.margem_desejada
    
    # Status do negócio
    if faturamento_atual_mes < faturamento_minimo_mes:
        status_equilibrio = 'Abaixo do ponto de equilíbrio'
        status_classe = 'danger'
    elif abs(diferenca_margem) <= 2:  # Tolerância de 2%
        status_equilibrio = 'No ponto de equilíbrio'
        status_classe = 'warning'
    else:
        status_equilibrio = 'Acima do ponto de equilíbrio'
        status_classe = 'success'
    
    # Recomendações
    recomendacoes = []
    
    if margem_atual < config.margem_desejada:
        diferenca_preco = preco_com_margem - config.preco_medio_praticado
        recomendacoes.append(f"Aumentar preço em R$ {diferenca_preco:.2f}/hora para atingir margem desejada")
    
    if horas_minimas_equilibrio > config.horas_trabalho_mes:
        horas_extras = horas_minimas_equilibrio - config.horas_trabalho_mes
        recomendacoes.append(f"Trabalhar {horas_extras:.1f} horas a mais por mês para equilibrio")
    
    if total_custos_fixos > faturamento_atual_mes * 0.7:  # Custos fixos > 70% do faturamento
        recomendacoes.append("Custos fixos muito altos - considere reduzi-los")
    
    return {
        # Inputs
        'total_custos_fixos': total_custos_fixos,
        'custo_variavel_hora': custo_variavel_hora,
        'custo_total_hora': custo_total_hora,
        'preco_atual': config.preco_medio_praticado,
        'horas_trabalho_mes': config.horas_trabalho_mes,
        
        # Cálculos do ponto de equilíbrio
        'preco_minimo_hora': preco_minimo_hora,
        'preco_com_margem_desejada': preco_com_margem,
        'faturamento_minimo_mes': faturamento_minimo_mes,
        'faturamento_atual_mes': faturamento_atual_mes,
        'horas_minimas_equilibrio': min(horas_minimas_equilibrio, 999),  # Cap para display
        
        # Margens
        'margem_atual': margem_atual,
        'margem_desejada': config.margem_desejada,
        'diferenca_margem': diferenca_margem,
        
        # Status
        'status_equilibrio': status_equilibrio,
        'status_classe': status_classe,
        
        # Recomendações
        'recomendacoes': recomendacoes,
        
        # Indicadores extras
        'dias_trabalho_equilibrio': horas_minimas_equilibrio / 8 if horas_minimas_equilibrio != float('inf') else 999,
        'percentual_custos_fixos': (total_custos_fixos / faturamento_atual_mes * 100) if faturamento_atual_mes > 0 else 100
    }
