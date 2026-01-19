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
    
    # ✨ AUDITORIA - Rastreabilidade completa
    usuario_criador = db.Column(db.String(100))  # Quem criou
    usuario_editor = db.Column(db.String(100))   # Último que editou
    data_criacao_auditoria = db.Column(db.DateTime, default=datetime.utcnow)
    data_edicao_auditoria = db.Column(db.DateTime, onupdate=datetime.utcnow)
    
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
    
    # ✨ GESTÃO FINANCEIRA AVANÇADA
    conta_bancaria_id = db.Column(db.Integer, db.ForeignKey('contas_bancarias.id'), nullable=True)
    centro_custo_id = db.Column(db.Integer, db.ForeignKey('centros_custo.id'), nullable=True)
    comprovante_anexo = db.Column(db.String(255))  # Path do arquivo
    numero_parcela = db.Column(db.String(20))  # Ex: 1/12
    valor_original = db.Column(db.Numeric(12, 2))  # Antes de juros/descontos
    juros = db.Column(db.Numeric(12, 2), default=0)
    desconto = db.Column(db.Numeric(12, 2), default=0)
    multa = db.Column(db.Numeric(12, 2), default=0)
    
    # Relacionamentos
    cliente = db.relationship('Cliente', backref='lancamentos_financeiros', foreign_keys=[cliente_id])
    fornecedor = db.relationship('Fornecedor', backref='lancamentos_financeiros', foreign_keys=[fornecedor_id])
    ordem_servico = db.relationship('OrdemServico', backref='lancamentos_financeiros', foreign_keys=[ordem_servico_id])
    conta_bancaria = db.relationship('ContaBancaria', backref='lancamentos', foreign_keys=[conta_bancaria_id])
    centro_custo = db.relationship('CentroCusto', backref='lancamentos', foreign_keys=[centro_custo_id])
    historico = db.relationship('HistoricoFinanceiro', backref='lancamento', cascade='all, delete-orphan')
    
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
    
    def marcar_como_pago(self, data_pagamento=None, usuario=None):
        """Marca lançamento como pago e registra no histórico."""
        if not data_pagamento:
            data_pagamento = date.today()
        
        # Registrar histórico
        if usuario:
            historico = HistoricoFinanceiro(
                lancamento_id=self.id,
                campo_alterado='status',
                valor_anterior=self.status,
                valor_novo='pago' if self.tipo in ['despesa', 'conta_pagar'] else 'recebido',
                usuario=usuario,
                acao='pagamento',
                motivo=f'Marcado como pago em {data_pagamento}'
            )
            db.session.add(historico)
        
        self.status = 'pago' if self.tipo in ['despesa', 'conta_pagar'] else 'recebido'
        self.data_pagamento = data_pagamento
        self.usuario_editor = usuario
        
        # Atualizar saldo da conta bancária
        if self.conta_bancaria_id:
            conta = ContaBancaria.query.get(self.conta_bancaria_id)
            if conta:
                if self.tipo in ['receita', 'conta_receber']:
                    conta.atualizar_saldo(self.valor, 'adicionar')
                elif self.tipo in ['despesa', 'conta_pagar']:
                    conta.atualizar_saldo(self.valor, 'subtrair')
        
        db.session.commit()
    
    def cancelar(self, usuario=None, motivo=None):
        """Cancela o lançamento e registra no histórico."""
        if usuario:
            historico = HistoricoFinanceiro(
                lancamento_id=self.id,
                campo_alterado='status',
                valor_anterior=self.status,
                valor_novo='cancelado',
                usuario=usuario,
                acao='exclusao',
                motivo=motivo or 'Lançamento cancelado'
            )
            db.session.add(historico)
        
        self.status = 'cancelado'
        self.usuario_editor = usuario
        db.session.commit()
    
    @classmethod
    def calcular_fluxo_caixa(cls, dias_futuro=30):
        """
        Calcula projeção de fluxo de caixa.
        
        Args:
            dias_futuro: Número de dias para projetar
            
        Returns:
            dict com saldo atual e projeções
        """
        from datetime import timedelta
        hoje = date.today()
        data_futura = hoje + timedelta(days=dias_futuro)
        
        # Saldo atual em contas
        saldo_atual = ContaBancaria.get_saldo_total()
        
        # Contas a receber até a data
        receber = cls.query.filter(
            cls.tipo.in_(['receita', 'conta_receber']),
            cls.status == 'pendente',
            cls.data_vencimento <= data_futura,
            cls.ativo == True
        ).all()
        total_receber = sum(float(r.valor) for r in receber)
        
        # Contas a pagar até a data
        pagar = cls.query.filter(
            cls.tipo.in_(['despesa', 'conta_pagar']),
            cls.status == 'pendente',
            cls.data_vencimento <= data_futura,
            cls.ativo == True
        ).all()
        total_pagar = sum(float(p.valor) for p in pagar)
        
        # Projeção
        saldo_projetado = saldo_atual + total_receber - total_pagar
        
        return {
            'saldo_atual': saldo_atual,
            'a_receber': total_receber,
            'a_pagar': total_pagar,
            'saldo_projetado': saldo_projetado,
            'dias': dias_futuro,
            'data_referencia': data_futura.strftime('%d/%m/%Y')
        }


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


class ContaBancaria(BaseModel):
    """
    Model para Contas Bancárias.
    
    Gerencia contas correntes, poupança e caixas da empresa.
    Fundamental para conciliação e fluxo de caixa.
    """
    
    __tablename__ = 'contas_bancarias'
    
    # Identificação
    nome = db.Column(db.String(100), nullable=False)
    tipo = db.Column(db.String(20), nullable=False)  # conta_corrente, poupanca, caixa
    
    # Dados bancários
    banco = db.Column(db.String(100))
    agencia = db.Column(db.String(20))
    numero_conta = db.Column(db.String(30))
    
    # Controle financeiro
    saldo_inicial = db.Column(db.Numeric(12, 2), default=0)
    saldo_atual = db.Column(db.Numeric(12, 2), default=0)
    limite_credito = db.Column(db.Numeric(12, 2), default=0)
    
    # Status
    ativa = db.Column(db.Boolean, default=True)
    principal = db.Column(db.Boolean, default=False)  # Conta principal da empresa
    
    # Observações
    observacoes = db.Column(db.Text)
    
    def __repr__(self):
        return f'<ContaBancaria {self.nome}>'
    
    @property
    def saldo_com_limite(self):
        """Retorna saldo disponível considerando limite."""
        return float(self.saldo_atual) + float(self.limite_credito or 0)
    
    @property
    def saldo_formatado(self):
        """Retorna saldo formatado em reais."""
        return f"R$ {self.saldo_atual:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
    
    def atualizar_saldo(self, valor, operacao='adicionar'):
        """
        Atualiza saldo da conta.
        
        Args:
            valor: Valor a ser adicionado ou subtraído
            operacao: 'adicionar' ou 'subtrair'
        """
        if operacao == 'adicionar':
            self.saldo_atual += valor
        elif operacao == 'subtrair':
            self.saldo_atual -= valor
        
        db.session.commit()
    
    @classmethod
    def get_saldo_total(cls):
        """Retorna soma de saldos de todas as contas ativas."""
        contas = cls.query.filter_by(ativo=True).all()
        return sum(float(c.saldo_atual) for c in contas)


class CentroCusto(BaseModel):
    """
    Model para Centro de Custo.
    
    Permite segregar receitas e despesas por departamento, projeto ou filial.
    Essencial para análise gerencial detalhada.
    """
    
    __tablename__ = 'centros_custo'
    
    # Identificação
    codigo = db.Column(db.String(20), unique=True, nullable=False)
    nome = db.Column(db.String(100), nullable=False)
    descricao = db.Column(db.Text)
    
    # Tipo
    tipo = db.Column(db.String(30))  # departamento, projeto, filial, produto
    
    # Responsável
    responsavel = db.Column(db.String(100))
    
    # Orçamento
    orcamento_mensal = db.Column(db.Numeric(12, 2))
    
    # Hierarquia (opcional)
    centro_pai_id = db.Column(db.Integer, db.ForeignKey('centros_custo.id'))
    
    def __repr__(self):
        return f'<CentroCusto {self.codigo}: {self.nome}>'
    
    @property
    def nome_completo(self):
        """Retorna código e nome."""
        return f"{self.codigo} - {self.nome}"
    
    @classmethod
    def get_despesas_mes(cls, centro_id, mes=None, ano=None):
        """Calcula total de despesas do centro no mês."""
        from datetime import date
        if not mes:
            mes = date.today().month
        if not ano:
            ano = date.today().year
        
        despesas = LancamentoFinanceiro.query.filter(
            LancamentoFinanceiro.centro_custo_id == centro_id,
            LancamentoFinanceiro.tipo.in_(['despesa', 'conta_pagar']),
            db.extract('month', LancamentoFinanceiro.data_lancamento) == mes,
            db.extract('year', LancamentoFinanceiro.data_lancamento) == ano,
            LancamentoFinanceiro.ativo == True
        ).all()
        
        return sum(float(d.valor) for d in despesas)

# Configurar relacionamentos
CentroCusto.centro_pai = db.relationship('CentroCusto', 
                                         remote_side=[CentroCusto.id], 
                                         backref='centros_filhos')


class HistoricoFinanceiro(BaseModel):
    """
    Model para Histórico de Alterações Financeiras.
    
    Registra todas as mudanças em lançamentos para auditoria completa.
    """
    
    __tablename__ = 'historico_financeiro'
    
    # Lançamento relacionado
    lancamento_id = db.Column(db.Integer, db.ForeignKey('lancamentos_financeiros.id'), nullable=False)
    
    # Dados da alteração
    campo_alterado = db.Column(db.String(50), nullable=False)
    valor_anterior = db.Column(db.Text)
    valor_novo = db.Column(db.Text)
    
    # Auditoria
    usuario = db.Column(db.String(100), nullable=False)
    data_alteracao = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    ip_address = db.Column(db.String(45))
    acao = db.Column(db.String(20))  # criacao, edicao, exclusao, pagamento
    
    # Observação da alteração
    motivo = db.Column(db.Text)
    
    def __repr__(self):
        return f'<HistoricoFinanceiro L:{self.lancamento_id} - {self.acao}>'