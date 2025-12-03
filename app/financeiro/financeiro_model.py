# -*- coding: utf-8 -*-
"""
ERP JSP v3.0 - Model de Financeiro
==================================

Model para gerenciamento financeiro do sistema.
Controla lançamentos, contas a pagar e receber.

Autor: JSP Soluções
Data: 2025
"""

from datetime import datetime, date
from decimal import Decimal
from app.extensoes import db
from app.models import BaseModel


class LancamentoFinanceiro(BaseModel):
    """
    Model para Lançamentos Financeiros.
    
    Controla todas as movimentações financeiras do sistema,
    incluindo receitas, despesas, contas a pagar e receber.
    """
    
    __tablename__ = 'lancamentos_financeiros'
    
    # Campos básicos
    descricao = db.Column(db.String(255), nullable=False)
    valor = db.Column(db.Numeric(12, 2), nullable=False)
    
    # Tipo de lançamento
    tipo = db.Column(db.String(20), nullable=False)
    # Possíveis tipos: receita, despesa, conta_receber, conta_pagar
    
    # Status do lançamento
    status = db.Column(db.String(20), default='pendente', nullable=False)
    # Possíveis status: pendente, pago, recebido, cancelado, vencido
    
    # Categoria
    categoria = db.Column(db.String(100))
    subcategoria = db.Column(db.String(100))
    
    # Datas
    data_lancamento = db.Column(db.Date, default=date.today, nullable=False)
    data_vencimento = db.Column(db.Date)
    data_pagamento = db.Column(db.Date)
    
    # Informações adicionais
    observacoes = db.Column(db.Text)
    numero_documento = db.Column(db.String(50))
    forma_pagamento = db.Column(db.String(50))
    
    # Relacionamentos opcionais
    cliente_id = db.Column(db.Integer, db.ForeignKey('clientes.id'), nullable=True)
    fornecedor_id = db.Column(db.Integer, db.ForeignKey('fornecedores.id'), nullable=True)
    ordem_servico_id = db.Column(db.Integer, db.ForeignKey('ordem_servico.id'), nullable=True)
    
    # Controle de recorrência
    recorrente = db.Column(db.Boolean, default=False)
    frequencia = db.Column(db.String(20))  # mensal, anual, semanal
    
    # Relacionamentos
    cliente = db.relationship('Cliente', backref='lancamentos_financeiros', foreign_keys=[cliente_id])
    fornecedor = db.relationship('Fornecedor', backref='lancamentos_financeiros', foreign_keys=[fornecedor_id])
    ordem_servico = db.relationship('OrdemServico', backref='lancamentos_financeiros', foreign_keys=[ordem_servico_id])
    
    def __repr__(self):
        return f'<LancamentoFinanceiro {self.id}: {self.descricao}>'
    
    def __str__(self):
        return f'{self.descricao} - R$ {self.valor}'
    
    @property
    def valor_formatado(self):
        """Retorna valor formatado em reais."""
        return f"R$ {self.valor:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
    
    @property
    def tipo_formatado(self):
        """Retorna tipo formatado para exibição."""
        tipos = {
            'receita': 'Receita',
            'despesa': 'Despesa', 
            'conta_receber': 'Conta a Receber',
            'conta_pagar': 'Conta a Pagar'
        }
        return tipos.get(self.tipo, self.tipo.title())
    
    @property
    def status_formatado(self):
        """Retorna status formatado para exibição."""
        status_map = {
            'pendente': 'Pendente',
            'pago': 'Pago',
            'recebido': 'Recebido',
            'cancelado': 'Cancelado',
            'vencido': 'Vencido'
        }
        return status_map.get(self.status, self.status.title())
    
    @property
    def status_cor(self):
        """Retorna cor do badge do status."""
        cores = {
            'pendente': 'warning',
            'pago': 'success',
            'recebido': 'success',
            'cancelado': 'secondary',
            'vencido': 'danger'
        }
        return cores.get(self.status, 'secondary')
    
    @property
    def tipo_cor(self):
        """Retorna cor do badge do tipo."""
        cores = {
            'receita': 'success',
            'despesa': 'danger',
            'conta_receber': 'info',
            'conta_pagar': 'warning'
        }
        return cores.get(self.tipo, 'secondary')
    
    @property
    def dias_vencimento(self):
        """Calcula dias até o vencimento."""
        if not self.data_vencimento:
            return None
        
        hoje = date.today()
        delta = self.data_vencimento - hoje
        return delta.days
    
    @property
    def situacao_vencimento(self):
        """Retorna situação do vencimento."""
        if not self.data_vencimento:
            return 'sem_vencimento'
        
        dias = self.dias_vencimento
        if dias < 0:
            return 'vencido'
        elif dias == 0:
            return 'vence_hoje'
        elif dias <= 7:
            return 'vence_semana'
        elif dias <= 30:
            return 'vence_mes'
        else:
            return 'futuro'
    
    @classmethod
    def get_receitas(cls):
        """Retorna todas as receitas."""
        return cls.query.filter_by(tipo='receita', ativo=True)
    
    @classmethod
    def get_despesas(cls):
        """Retorna todas as despesas."""
        return cls.query.filter_by(tipo='despesa', ativo=True)
    
    @classmethod
    def get_contas_receber(cls):
        """Retorna contas a receber."""
        return cls.query.filter_by(tipo='conta_receber', ativo=True)
    
    @classmethod
    def get_contas_pagar(cls):
        """Retorna contas a pagar."""
        return cls.query.filter_by(tipo='conta_pagar', ativo=True)
    
    @classmethod
    def get_pendentes(cls):
        """Retorna lançamentos pendentes."""
        return cls.query.filter_by(status='pendente', ativo=True)
    
    @classmethod
    def get_vencidos(cls):
        """Retorna lançamentos vencidos."""
        hoje = date.today()
        return cls.query.filter(
            cls.data_vencimento < hoje,
            cls.status.in_(['pendente']),
            cls.ativo == True
        )
    
    @classmethod
    def get_resumo_mes(cls, mes=None, ano=None):
        """Retorna resumo financeiro do mês."""
        if not mes:
            mes = date.today().month
        if not ano:
            ano = date.today().year
        
        # Filtro por mês/ano
        filtro_data = db.and_(
            db.extract('month', cls.data_lancamento) == mes,
            db.extract('year', cls.data_lancamento) == ano,
            cls.ativo == True
        )
        
        receitas = cls.query.filter(
            filtro_data,
            cls.tipo.in_(['receita', 'conta_receber']),
            cls.status == 'recebido'
        ).all()
        
        despesas = cls.query.filter(
            filtro_data,
            cls.tipo.in_(['despesa', 'conta_pagar']),
            cls.status == 'pago'
        ).all()
        
        total_receitas = sum(float(r.valor) for r in receitas)
        total_despesas = sum(float(d.valor) for d in despesas)
        saldo = total_receitas - total_despesas
        
        return {
            'total_receitas': total_receitas,
            'total_despesas': total_despesas,
            'saldo': saldo,
            'qtd_receitas': len(receitas),
            'qtd_despesas': len(despesas)
        }
    
    def marcar_como_pago(self, data_pagamento=None):
        """Marca lançamento como pago."""
        if not data_pagamento:
            data_pagamento = date.today()
        
        self.status = 'pago' if self.tipo in ['despesa', 'conta_pagar'] else 'recebido'
        self.data_pagamento = data_pagamento
        db.session.commit()
    
    def cancelar(self):
        """Cancela o lançamento."""
        self.status = 'cancelado'
        db.session.commit()


class CategoriaFinanceira(BaseModel):
    """
    Model para Categorias Financeiras.
    
    Organiza os lançamentos em categorias e subcategorias.
    """
    
    __tablename__ = 'categorias_financeiras'
    
    nome = db.Column(db.String(100), nullable=False)
    descricao = db.Column(db.Text)
    tipo = db.Column(db.String(20), nullable=False)  # receita, despesa
    cor = db.Column(db.String(20), default='primary')
    icone = db.Column(db.String(50), default='fas fa-money-bill')
    
    # Categoria pai (para subcategorias)
    categoria_pai_id = db.Column(db.Integer, db.ForeignKey('categorias_financeiras.id'))
    
    def __repr__(self):
        return f'<CategoriaFinanceira {self.nome}>'
    
    @classmethod
    def get_por_tipo(cls, tipo):
        """Retorna categorias por tipo."""
        return cls.query.filter_by(tipo=tipo, ativo=True, categoria_pai_id=None)

# Configurar relacionamento após definição da classe
CategoriaFinanceira.categoria_pai = db.relationship('CategoriaFinanceira', 
                                                   remote_side=[CategoriaFinanceira.id], 
                                                   backref='subcategorias')


class PlanoContas(BaseModel):
    """
    Model para Plano de Contas.
    
    Estrutura contábil básica do sistema.
    """
    
    __tablename__ = 'plano_contas'
    
    codigo = db.Column(db.String(20), unique=True, nullable=False)
    nome = db.Column(db.String(200), nullable=False)
    tipo = db.Column(db.String(20), nullable=False)  # ativo, passivo, receita, despesa
    natureza = db.Column(db.String(20), nullable=False)  # debito, credito
    
    # Hierarquia
    conta_pai_id = db.Column(db.Integer, db.ForeignKey('plano_contas.id'))
    nivel = db.Column(db.Integer, default=1)
    
    def __repr__(self):
        return f'<PlanoContas {self.codigo}: {self.nome}>'

# Configurar relacionamento após definição da classe
PlanoContas.conta_pai = db.relationship('PlanoContas', 
                                       remote_side=[PlanoContas.id], 
                                       backref='contas_filhas')