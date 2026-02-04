# -*- coding: utf-8 -*-
"""
ERP JSP v3.0 - Model de Serviço
================================

Model para cadastro de serviços oferecidos pela empresa.
Os serviços cadastrados aqui podem ser adicionados às Ordens de Serviço.

Autor: JSP Soluções
Data: 2026
"""

from app.extensoes import db
from app.models import BaseModel
from decimal import Decimal

# Constantes para padronização
TIPO_COBRANCA_CHOICES = [
    ('hora', 'Por Hora'),
    ('dia', 'Por Dia'),
    ('servico', 'Serviço Fechado'),
    ('km', 'Por Quilômetro'),
    ('item', 'Por Item/Unidade')
]

CATEGORIA_CHOICES = [
    ('instalacao', 'Instalação'),
    ('manutencao', 'Manutenção'),
    ('reparo', 'Reparo'),
    ('consultoria', 'Consultoria'),
    ('projeto', 'Projeto'),
    ('vistoria', 'Vistoria'),
    ('treinamento', 'Treinamento'),
    ('outros', 'Outros')
]


class Servico(BaseModel):
    """
    Model para Serviço.
    
    Cadastro de serviços oferecidos pela empresa que podem ser
    adicionados às ordens de serviço.
    """
    
    __tablename__ = 'servicos'
    
    # Constantes da classe
    TIPO_COBRANCA_CHOICES = TIPO_COBRANCA_CHOICES
    CATEGORIA_CHOICES = CATEGORIA_CHOICES
    
    # Dados principais
    codigo = db.Column(db.String(20), unique=True, index=True)
    nome = db.Column(db.String(200), nullable=False, index=True)
    descricao = db.Column(db.Text)
    
    # Categoria e tipo
    categoria = db.Column(db.String(50), default='outros')  # instalacao, manutencao, reparo, etc.
    tipo_cobranca = db.Column(db.String(20), default='servico', nullable=False)  # hora, dia, servico, km, item
    
    # Valores
    valor_base = db.Column(db.Numeric(10, 2), default=0.00, nullable=False)
    valor_minimo = db.Column(db.Numeric(10, 2), default=0.00)  # Valor mínimo a cobrar
    
    # Estimativas
    tempo_estimado = db.Column(db.Integer)  # Em minutos
    tempo_estimado_min = db.Column(db.Integer)  # Tempo mínimo em minutos
    tempo_estimado_max = db.Column(db.Integer)  # Tempo máximo em minutos
    
    # Garantia
    prazo_garantia = db.Column(db.Integer, default=0)  # Em dias
    
    # Materiais necessários (opcional - para referência)
    materiais_necessarios = db.Column(db.Text)  # Lista de materiais que geralmente são usados
    
    # Observações e instruções
    observacoes = db.Column(db.Text)
    instrucoes_execucao = db.Column(db.Text)  # Instruções para o técnico
    
    # Configurações
    requer_agendamento = db.Column(db.Boolean, default=False)
    disponivel_app = db.Column(db.Boolean, default=True)  # Disponível para agendamento via app
    destaque = db.Column(db.Boolean, default=False)  # Serviço em destaque
    
    # Meta campos herdados de BaseModel:
    # id, data_criacao, data_atualizacao, ativo, usuario_criacao, usuario_atualizacao
    
    def __repr__(self):
        return f'<Servico {self.codigo}: {self.nome}>'
    
    def __str__(self):
        return f'{self.nome}'
    
    @property
    def nome_display(self):
        """Nome formatado para exibição com código."""
        if self.codigo:
            return f'{self.codigo} - {self.nome}'
        return self.nome
    
    @property
    def categoria_display(self):
        """Retorna categoria formatada."""
        categorias = dict(CATEGORIA_CHOICES)
        return categorias.get(self.categoria, self.categoria.title())
    
    @property
    def tipo_cobranca_display(self):
        """Retorna tipo de cobrança formatado."""
        tipos = dict(TIPO_COBRANCA_CHOICES)
        return tipos.get(self.tipo_cobranca, self.tipo_cobranca.title())
    
    @property
    def valor_base_formatado(self):
        """Retorna valor base formatado."""
        if self.valor_base:
            return f'R$ {float(self.valor_base):,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.')
        return 'R$ 0,00'
    
    @property
    def tempo_estimado_formatado(self):
        """Retorna tempo estimado formatado (HH:MM)."""
        if self.tempo_estimado:
            horas = self.tempo_estimado // 60
            minutos = self.tempo_estimado % 60
            if horas > 0:
                return f'{horas}h {minutos}min'
            return f'{minutos}min'
        return 'Não estimado'
    
    @property
    def tempo_estimado_range(self):
        """Retorna range de tempo estimado."""
        if self.tempo_estimado_min and self.tempo_estimado_max:
            min_h = self.tempo_estimado_min // 60
            min_m = self.tempo_estimado_min % 60
            max_h = self.tempo_estimado_max // 60
            max_m = self.tempo_estimado_max % 60
            
            min_str = f'{min_h}h {min_m}min' if min_h > 0 else f'{min_m}min'
            max_str = f'{max_h}h {max_m}min' if max_h > 0 else f'{max_m}min'
            
            return f'{min_str} - {max_str}'
        return self.tempo_estimado_formatado
    
    @classmethod
    def gerar_proximo_codigo(cls):
        """
        Gera o próximo código de serviço no formato SRV001, SRV002, etc.
        """
        # Busca o serviço com maior código
        ultimo_servico = cls.query.filter(
            cls.codigo.like('SRV%')
        ).order_by(cls.codigo.desc()).first()
        
        if ultimo_servico:
            try:
                # Extrai o número do código (SRV001 -> 001)
                numero = int(ultimo_servico.codigo.replace('SRV', ''))
                proximo = numero + 1
            except:
                proximo = 1
        else:
            proximo = 1
        
        # Gera código no formato SRV001
        codigo = f'SRV{proximo:03d}'
        
        # Verifica se já existe (segurança)
        tentativas = 0
        while cls.query.filter_by(codigo=codigo).first() and tentativas < 100:
            proximo += 1
            codigo = f'SRV{proximo:03d}'
            tentativas += 1
        
        return codigo
    
    @classmethod
    def buscar_por_codigo(cls, codigo):
        """Busca serviço por código."""
        return cls.query.filter_by(codigo=codigo, ativo=True).first()
    
    @classmethod
    def buscar_por_categoria(cls, categoria):
        """Busca serviços por categoria."""
        return cls.query.filter_by(categoria=categoria, ativo=True).all()
    
    @classmethod
    def listar_disponiveis(cls):
        """Lista apenas serviços disponíveis (ativos e disponíveis no app)."""
        return cls.query.filter_by(ativo=True, disponivel_app=True).order_by(cls.nome).all()
    
    @classmethod
    def listar_destaques(cls):
        """Lista serviços em destaque."""
        return cls.query.filter_by(ativo=True, destaque=True).order_by(cls.nome).all()
    
    @classmethod
    def estatisticas_dashboard(cls):
        """Retorna estatísticas para o dashboard."""
        total = cls.query.filter_by(ativo=True).count()
        disponiveis = cls.query.filter_by(ativo=True, disponivel_app=True).count()
        destaques = cls.query.filter_by(ativo=True, destaque=True).count()
        
        # Conta por categoria
        from sqlalchemy import func
        por_categoria = db.session.query(
            cls.categoria,
            func.count(cls.id)
        ).filter_by(ativo=True).group_by(cls.categoria).all()
        
        categorias = {cat: count for cat, count in por_categoria}
        
        return {
            'total': total,
            'disponiveis': disponiveis,
            'destaques': destaques,
            'por_categoria': categorias
        }
    
    def calcular_valor_estimado(self, quantidade=1):
        """
        Calcula valor estimado baseado no tipo de cobrança.
        
        Args:
            quantidade: Quantidade de horas, dias, km, etc.
        
        Returns:
            Decimal: Valor estimado
        """
        valor = Decimal(str(self.valor_base or 0)) * Decimal(str(quantidade))
        
        # Verifica valor mínimo
        if self.valor_minimo and valor < Decimal(str(self.valor_minimo)):
            valor = Decimal(str(self.valor_minimo))
        
        return float(valor)
    
    def validar_dados(self):
        """Valida os dados do serviço."""
        erros = []
        
        if not self.nome or not self.nome.strip():
            erros.append("Nome é obrigatório")
        
        if self.valor_base is not None and self.valor_base < 0:
            erros.append("Valor base não pode ser negativo")
        
        if self.tempo_estimado is not None and self.tempo_estimado < 0:
            erros.append("Tempo estimado não pode ser negativo")
        
        if self.prazo_garantia is not None and self.prazo_garantia < 0:
            erros.append("Prazo de garantia não pode ser negativo")
        
        return erros
    
    def to_dict(self):
        """Converte o serviço para dicionário (útil para APIs)."""
        return {
            'id': self.id,
            'codigo': self.codigo,
            'nome': self.nome,
            'descricao': self.descricao,
            'categoria': self.categoria,
            'categoria_display': self.categoria_display,
            'tipo_cobranca': self.tipo_cobranca,
            'tipo_cobranca_display': self.tipo_cobranca_display,
            'valor_base': float(self.valor_base) if self.valor_base else 0,
            'valor_base_formatado': self.valor_base_formatado,
            'tempo_estimado': self.tempo_estimado,
            'tempo_estimado_formatado': self.tempo_estimado_formatado,
            'prazo_garantia': self.prazo_garantia,
            'disponivel_app': self.disponivel_app,
            'destaque': self.destaque
        }
