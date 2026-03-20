# -*- coding: utf-8 -*-
"""
ERP JSP v3.0 - Model de Colaborador
====================================

Model para gerenciamento de colaboradores/técnicos.
Controla dados dos colaboradores e horas trabalhadas em OSs.

Autor: JSP Soluções
Data: 2025
"""

from app.extensoes import db
from app.models import BaseModel
from decimal import Decimal
from datetime import datetime, date, time

# Constantes para padronização
CARGO_CHOICES = [
    ('tecnico', 'Técnico'),
    ('eletricista', 'Eletricista'),
    ('engenheiro', 'Engenheiro'),
    ('ajudante', 'Ajudante'),
    ('instalador', 'Instalador'),
    ('outros', 'Outros')
]

CARGO_MAP = dict(CARGO_CHOICES)


class Colaborador(BaseModel):
    """
    Model para Colaborador/Técnico.
    
    Armazena informações dos colaboradores que trabalham nas OSs.
    """
    
    __tablename__ = 'colaborador'
    
    # Constantes da classe
    CARGO_CHOICES = CARGO_CHOICES
    CARGO_MAP = CARGO_MAP
    
    # === DADOS PRINCIPAIS ===
    nome = db.Column(db.String(150), nullable=False, index=True)
    
    # === DOCUMENTOS ===
    cpf = db.Column(db.String(14), unique=True, index=True)  # 000.000.000-00
    
    # === CONTATO ===
    telefone = db.Column(db.String(20))
    celular = db.Column(db.String(20))
    email = db.Column(db.String(150))
    
    # === DADOS PROFISSIONAIS ===
    cargo = db.Column(db.String(50), default='tecnico')  # tecnico, eletricista, ajudante, etc.
    especialidade = db.Column(db.String(200))  # Área de especialização
    data_admissao = db.Column(db.Date)
    data_demissao = db.Column(db.Date)  # Null enquanto estiver ativo
    
    # === DADOS FINANCEIROS (opcional - para futura precificação) ===
    valor_hora = db.Column(db.Numeric(10, 2), default=0.00)  # Custo/hora do colaborador
    
    # === OBSERVAÇÕES ===
    observacoes = db.Column(db.Text)
    
    # === RELACIONAMENTOS ===
    # Relacionamento com ordens de serviço (via tabela intermediária)
    # Acessível via: colaborador.trabalhos_os
    
    def __repr__(self):
        return f'<Colaborador {self.nome}>'
    
    def __str__(self):
        return self.nome
    
    @property
    def cargo_formatado(self):
        """Retorna cargo formatado para exibição."""
        return CARGO_MAP.get(self.cargo, self.cargo.title())
    
    @property
    def esta_ativo(self):
        """Verifica se o colaborador está ativo (não foi demitido)."""
        return self.ativo and (self.data_demissao is None or self.data_demissao > date.today())
    
    @property
    def total_horas_trabalhadas(self):
        """Calcula total de horas trabalhadas pelo colaborador (histórico)."""
        total = 0.0
        for trabalho in self.trabalhos_os:
            if trabalho.ativo:
                total += float(trabalho.total_horas or 0)
        return total
    
    @property
    def total_os_trabalhadas(self):
        """Retorna total de OSs que o colaborador participou."""
        return len([t for t in self.trabalhos_os if t.ativo])
    
    @staticmethod
    def buscar_ativos():
        """Retorna todos os colaboradores ativos ordenados por nome."""
        return Colaborador.query.filter_by(ativo=True).filter(
            (Colaborador.data_demissao.is_(None)) | (Colaborador.data_demissao > date.today())
        ).order_by(Colaborador.nome).all()


class OrdemServicoColaborador(BaseModel):
    """
    Model para relacionamento entre Ordem de Serviço e Colaborador.
    
    Registra as horas trabalhadas de cada colaborador em cada OS.
    """
    
    __tablename__ = 'ordem_servico_colaborador'
    
    # === RELACIONAMENTOS ===
    ordem_servico_id = db.Column(db.Integer, db.ForeignKey('ordem_servico.id'), nullable=False)
    ordem_servico = db.relationship('OrdemServico', backref='colaboradores_trabalho')
    
    colaborador_id = db.Column(db.Integer, db.ForeignKey('colaborador.id'), nullable=False)
    colaborador = db.relationship('Colaborador', backref='trabalhos_os')
    
    # === DADOS DO TRABALHO ===
    data_trabalho = db.Column(db.Date, default=date.today, nullable=False)
    
    # Controle de horas (pode usar hora_inicio/fim OU total_horas direto)
    hora_inicio = db.Column(db.Time)
    hora_fim = db.Column(db.Time)
    total_horas = db.Column(db.Numeric(5, 2), default=0.00)  # 8.5 = 8h30min
    
    # === DESCRIÇÃO DA ATIVIDADE ===
    descricao_atividade = db.Column(db.Text)  # O que foi feito
    observacoes = db.Column(db.Text)  # Observações gerais
    
    def __repr__(self):
        return f'<OSColaborador OS#{self.ordem_servico_id} - {self.colaborador.nome if self.colaborador else "?"}: {self.total_horas}h>'
    
    def __str__(self):
        return f'{self.colaborador.nome if self.colaborador else "?"} - {self.total_horas}h'
    
    def calcular_horas_automatico(self):
        """Calcula total de horas baseado em hora_inicio e hora_fim."""
        if self.hora_inicio and self.hora_fim:
            # Converte time para datetime para cálculo
            hoje = datetime.today().date()
            inicio = datetime.combine(hoje, self.hora_inicio)
            fim = datetime.combine(hoje, self.hora_fim)
            
            # Se hora final for menor, assume que passou para o dia seguinte
            if fim < inicio:
                from datetime import timedelta
                fim += timedelta(days=1)
            
            diferenca = fim - inicio
            horas_decimais = diferenca.total_seconds() / 3600  # converte para horas
            self.total_horas = Decimal(str(round(horas_decimais, 2)))
        
        return self.total_horas
    
    @property
    def total_horas_formatado(self):
        """Retorna total de horas em formato legível (ex: '8h 30min')."""
        if not self.total_horas:
            return '0h'
        
        horas_decimal = float(self.total_horas)
        horas_inteiras = int(horas_decimal)
        minutos = int((horas_decimal - horas_inteiras) * 60)
        
        if minutos > 0:
            return f'{horas_inteiras}h {minutos}min'
        else:
            return f'{horas_inteiras}h'
    
    @property
    def periodo_trabalho(self):
        """Retorna período de trabalho formatado (ex: '08:00 - 17:00')."""
        if self.hora_inicio and self.hora_fim:
            return f'{self.hora_inicio.strftime("%H:%M")} - {self.hora_fim.strftime("%H:%M")}'
        return 'Não informado'
