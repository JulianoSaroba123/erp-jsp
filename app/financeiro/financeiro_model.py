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
    plano_conta_id = db.Column(db.Integer, db.ForeignKey('plano_contas.id'), nullable=True)
    comprovante_anexo = db.Column(db.String(255))  # Path do arquivo
    numero_parcela = db.Column(db.String(20))  # Ex: 1/12
    valor_original = db.Column(db.Numeric(12, 2))  # Antes de juros/descontos
    juros = db.Column(db.Numeric(12, 2), default=0)
    desconto = db.Column(db.Numeric(12, 2), default=0)
    multa = db.Column(db.Numeric(12, 2), default=0)
    
    # 🎯 ORIGEM DO LANÇAMENTO - Para rastreabilidade
    origem = db.Column(db.String(50), default='MANUAL')
    # Possíveis origens: MANUAL, CUSTO_FIXO, ORDEM_SERVICO, IMPORTACAO, INTEGRACAO
    custo_fixo_id = db.Column(db.Integer, db.ForeignKey('custos_fixos.id'), nullable=True)
    
    # Relacionamentos
    cliente = db.relationship('Cliente', backref='lancamentos_financeiros', foreign_keys=[cliente_id])
    fornecedor = db.relationship('Fornecedor', backref='lancamentos_financeiros', foreign_keys=[fornecedor_id])
    ordem_servico = db.relationship('OrdemServico', backref='lancamentos_financeiros', foreign_keys=[ordem_servico_id])
    conta_bancaria = db.relationship('ContaBancaria', backref='lancamentos', foreign_keys=[conta_bancaria_id])
    centro_custo = db.relationship('CentroCusto', backref='lancamentos', foreign_keys=[centro_custo_id])
    plano_conta = db.relationship('PlanoContas', backref='lancamentos', foreign_keys=[plano_conta_id])
    custo_fixo = db.relationship('CustoFixo', backref='lancamentos_gerados', foreign_keys=[custo_fixo_id])
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
    def origem_formatada(self):
        """Retorna origem formatada para exibição."""
        origens = {
            'MANUAL': 'Lançamento Manual',
            'CUSTO_FIXO': 'Custo Fixo Recorrente',
            'ORDEM_SERVICO': 'Ordem de Serviço',
            'IMPORTACAO': 'Importação',
            'INTEGRACAO': 'Integração'
        }
        return origens.get(self.origem, 'Manual')
    
    @property
    def origem_cor(self):
        """Retorna cor da badge da origem."""
        cores = {
            'MANUAL': 'primary',
            'CUSTO_FIXO': 'warning',
            'ORDEM_SERVICO': 'info',
            'IMPORTACAO': 'secondary',
            'INTEGRACAO': 'dark'
        }
        return cores.get(self.origem, 'primary')
    
    @property
    def origem_icone(self):
        """Retorna ícone da origem."""
        icones = {
            'MANUAL': 'fa-hand-pointer',
            'CUSTO_FIXO': 'fa-repeat',
            'ORDEM_SERVICO': 'fa-wrench',
            'IMPORTACAO': 'fa-file-import',
            'INTEGRACAO': 'fa-plug'
        }
        return icones.get(self.origem, 'fa-file')
    
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
        
        # Filtro por mês/ano - usar data_vencimento ou data_lancamento
        filtro_data = db.and_(
            db.or_(
                db.and_(
                    db.extract('month', cls.data_vencimento) == mes,
                    db.extract('year', cls.data_vencimento) == ano
                ),
                db.and_(
                    cls.data_vencimento.is_(None),
                    db.extract('month', cls.data_lancamento) == mes,
                    db.extract('year', cls.data_lancamento) == ano
                )
            ),
            cls.ativo == True
        )
        
        # Receitas (incluindo pendentes)
        receitas = cls.query.filter(
            filtro_data,
            cls.tipo.in_(['receita', 'conta_receber']),
            cls.status.in_(['recebido', 'pendente'])
        ).all()
        
        # Despesas (incluindo pendentes)
        despesas = cls.query.filter(
            filtro_data,
            cls.tipo.in_(['despesa', 'conta_pagar']),
            cls.status.in_(['pago', 'pendente'])
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

class ExtratoBancario(BaseModel):
    """
    Model para Extratos Bancários Importados.
    
    Armazena linhas de extratos bancários para conciliação.
    """
    
    __tablename__ = 'extratos_bancarios'
    
    # Conta bancária relacionada
    conta_bancaria_id = db.Column(db.Integer, db.ForeignKey('contas_bancarias.id'), nullable=False)
    
    # Dados do extrato
    data_movimento = db.Column(db.Date, nullable=False)
    descricao = db.Column(db.String(255), nullable=False)
    documento = db.Column(db.String(50))  # Número do documento/cheque
    valor = db.Column(db.Numeric(12, 2), nullable=False)
    tipo_movimento = db.Column(db.String(10), nullable=False)  # debito, credito
    
    # Saldo após movimento
    saldo = db.Column(db.Numeric(12, 2))
    
    # Conciliação
    conciliado = db.Column(db.Boolean, default=False)
    data_conciliacao = db.Column(db.DateTime)
    lancamento_id = db.Column(db.Integer, db.ForeignKey('lancamentos_financeiros.id'))
    
    # Importação
    arquivo_origem = db.Column(db.String(255))
    data_importacao = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Observações
    observacoes = db.Column(db.Text)
    
    # Relacionamentos
    conta_bancaria = db.relationship('ContaBancaria', backref='extratos', foreign_keys=[conta_bancaria_id])
    lancamento = db.relationship('LancamentoFinanceiro', backref='extrato_conciliado', foreign_keys=[lancamento_id])
    
    def __repr__(self):
        return f'<ExtratoBancario {self.data_movimento}: {self.descricao}>'
    
    @property
    def valor_formatado(self):
        """Retorna valor formatado em reais."""
        return f"R$ {abs(self.valor):,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
    
    @property
    def tipo_formatado(self):
        """Retorna tipo formatado."""
        return 'Crédito' if self.tipo_movimento == 'credito' else 'Débito'
    
    @property
    def status_conciliacao(self):
        """Retorna status da conciliação."""
        return 'Conciliado' if self.conciliado else 'Pendente'
    
    @classmethod
    def get_pendentes(cls, conta_id=None):
        """Retorna extratos pendentes de conciliação."""
        query = cls.query.filter_by(conciliado=False, ativo=True)
        if conta_id:
            query = query.filter_by(conta_bancaria_id=conta_id)
        return query.order_by(cls.data_movimento.desc())
    
    @classmethod
    def get_conciliados(cls, conta_id=None):
        """Retorna extratos já conciliados."""
        query = cls.query.filter_by(conciliado=True, ativo=True)
        if conta_id:
            query = query.filter_by(conta_bancaria_id=conta_id)
        return query.order_by(cls.data_movimento.desc())
    
    def conciliar_com_lancamento(self, lancamento_id):
        """Marca extrato como conciliado com um lançamento."""
        self.conciliado = True
        self.lancamento_id = lancamento_id
        self.data_conciliacao = datetime.utcnow()
        db.session.commit()
    
    def desconciliar(self):
        """Remove conciliação do extrato."""
        self.conciliado = False
        self.lancamento_id = None
        self.data_conciliacao = None
        db.session.commit()


class CustoFixo(BaseModel):
    """Modelo para Custos Fixos Recorrentes."""
    __tablename__ = 'custos_fixos'
    
    # Dados Básicos
    nome = db.Column(db.String(100), nullable=False)
    descricao = db.Column(db.Text)
    
    # Valores
    valor_mensal = db.Column(db.Numeric(10, 2), nullable=False)
    categoria = db.Column(db.String(50), nullable=False)  # Ex: Aluguel, Salários, Energia, Internet
    tipo = db.Column(db.String(20), nullable=False, default='DESPESA')  # DESPESA ou RECEITA
    
    # Configuração de Recorrência
    dia_vencimento = db.Column(db.Integer, nullable=False)  # 1-31
    gerar_automaticamente = db.Column(db.Boolean, default=True)
    data_inicio = db.Column(db.Date, nullable=False)
    data_fim = db.Column(db.Date)  # Null = indeterminado
    
    # Relacionamentos
    conta_bancaria_id = db.Column(db.Integer, db.ForeignKey('contas_bancarias.id'))
    centro_custo_id = db.Column(db.Integer, db.ForeignKey('centros_custo.id'))
    
    # Controle
    ativo = db.Column(db.Boolean, default=True)
    ultimo_mes_gerado = db.Column(db.String(7))  # Formato: YYYY-MM
    
    # Relationships
    conta_bancaria = db.relationship('ContaBancaria', backref='custos_fixos')
    centro_custo = db.relationship('CentroCusto', backref='custos_fixos')
    
    @property
    def valor_formatado(self):
        """Retorna valor formatado em R$."""
        return f"R$ {self.valor_mensal:,.2f}".replace(',', '_').replace('.', ',').replace('_', '.')
    
    @property
    def proximo_vencimento(self):
        """Calcula próximo vencimento baseado na data atual."""
        from datetime import date
        from calendar import monthrange
        
        hoje = date.today()
        ano = hoje.year
        mes = hoje.month
        
        # Ajustar dia se não existir no mês
        ultimo_dia_mes = monthrange(ano, mes)[1]
        dia = min(self.dia_vencimento, ultimo_dia_mes)
        
        proxima_data = date(ano, mes, dia)
        
        # Se já passou, pega próximo mês
        if proxima_data < hoje:
            if mes == 12:
                mes = 1
                ano += 1
            else:
                mes += 1
            ultimo_dia_mes = monthrange(ano, mes)[1]
            dia = min(self.dia_vencimento, ultimo_dia_mes)
            proxima_data = date(ano, mes, dia)
        
        return proxima_data
    
    def gerar_lancamento_mes(self, ano, mes):
        """Gera lançamento financeiro para o mês especificado."""
        from datetime import date
        from calendar import monthrange
        
        # Verificar se já foi gerado
        mes_key = f"{ano}-{mes:02d}"
        if self.ultimo_mes_gerado == mes_key:
            return None
        
        # Criar lançamento
        ultimo_dia_mes = monthrange(ano, mes)[1]
        dia = min(self.dia_vencimento, ultimo_dia_mes)
        data_vencimento = date(ano, mes, dia)
        
        lancamento = LancamentoFinanceiro(
            descricao=f"{self.nome} - {mes_key}",
            valor=self.valor_mensal,
            tipo=self.tipo,
            data_lancamento=data_vencimento,
            data_vencimento=data_vencimento,
            categoria=self.categoria,
            status='PENDENTE',
            conta_bancaria_id=self.conta_bancaria_id,
            centro_custo_id=self.centro_custo_id,
            origem='CUSTO_FIXO',
            custo_fixo_id=self.id  # Vincula ao custo fixo que gerou
        )
        
        db.session.add(lancamento)
        self.ultimo_mes_gerado = mes_key
        db.session.commit()
        
        return lancamento
    
    @classmethod
    def get_custos_ativos(cls):
        """Retorna todos os custos fixos ativos."""
        from datetime import date
        hoje = date.today()
        
        return cls.query.filter(
            cls.ativo == True,
            cls.data_inicio <= hoje,
            db.or_(cls.data_fim == None, cls.data_fim >= hoje)
        ).all()
    
    @classmethod
    def get_total_mensal(cls):
        """Calcula total mensal de custos fixos ativos."""
        from datetime import date
        hoje = date.today()
        
        total = db.session.query(db.func.sum(cls.valor_mensal)).filter(
            cls.ativo == True,
            cls.data_inicio <= hoje,
            db.or_(cls.data_fim == None, cls.data_fim >= hoje)
        ).scalar()
        
        return total or 0
    
    @classmethod
    def gerar_lancamentos_automaticos(cls):
        """Gera lançamentos para todos os custos fixos do mês atual."""
        from datetime import date
        
        hoje = date.today()
        custos = cls.get_custos_ativos()
        lancamentos_gerados = []
        
        for custo in custos:
            if custo.gerar_automaticamente:
                lancamento = custo.gerar_lancamento_mes(hoje.year, hoje.month)
                if lancamento:
                    lancamentos_gerados.append(lancamento)
        
        return lancamentos_gerados


# ============================================================
# PLANO DE CONTAS
# ============================================================

class PlanoContas(BaseModel):
    """
    Model para Plano de Contas Contábil.
    
    Estrutura hierárquica para classificação contábil dos lançamentos.
    Segue padrão contábil: Ativo, Passivo, Receitas, Despesas.
    """
    
    __tablename__ = 'plano_contas'
    __table_args__ = {'extend_existing': True}
    
    # Informações Básicas
    codigo = db.Column(db.String(20), unique=True, nullable=False, index=True)
    nome = db.Column(db.String(200), nullable=False)
    descricao = db.Column(db.Text)
    
    # Hierarquia
    tipo = db.Column(db.String(20), nullable=False)
    # Tipos: ATIVO, PASSIVO, RECEITA, DESPESA
    
    nivel = db.Column(db.Integer, default=1)  # 1=Pai, 2=Filho, 3=Neto, etc
    conta_pai_id = db.Column(db.Integer, db.ForeignKey('plano_contas.id'), nullable=True)
    
    # Configurações
    aceita_lancamento = db.Column(db.Boolean, default=True)  # Contas analíticas vs sintéticas
    ativa = db.Column(db.Boolean, default=True)
    
    # Natureza (para DRE)
    natureza = db.Column(db.String(20))  # DEBITO ou CREDITO
    
    # Ordenação
    ordem = db.Column(db.Integer, default=0)
    
    # Relacionamentos
    conta_pai = db.relationship('PlanoContas', remote_side='PlanoContas.id', 
                                backref='contas_filhas')
    
    def __repr__(self):
        return f'<PlanoContas {self.codigo}: {self.nome}>'
    
    @property
    def codigo_completo(self):
        """Retorna código com hierarquia completa."""
        if self.conta_pai:
            return f"{self.conta_pai.codigo_completo}.{self.codigo}"
        return self.codigo
    
    @property
    def nome_completo(self):
        """Retorna nome com hierarquia completa."""
        if self.conta_pai:
            return f"{self.conta_pai.nome} > {self.nome}"
        return self.nome
    
    @property
    def tipo_icone(self):
        """Retorna ícone baseado no tipo."""
        icones = {
            'ATIVO': 'fas fa-coins text-success',
            'PASSIVO': 'fas fa-hand-holding-usd text-danger',
            'RECEITA': 'fas fa-arrow-up text-success',
            'DESPESA': 'fas fa-arrow-down text-danger'
        }
        return icones.get(self.tipo, 'fas fa-file-invoice-dollar')
    
    @property
    def tipo_cor(self):
        """Retorna cor baseada no tipo."""
        cores = {
            'ATIVO': 'success',
            'PASSIVO': 'danger',
            'RECEITA': 'success',
            'DESPESA': 'danger'
        }
        return cores.get(self.tipo, 'secondary')
    
    @property
    def eh_sintetica(self):
        """Verifica se é conta sintética (tem filhas)."""
        return len(self.contas_filhas) > 0
    
    @property
    def eh_analitica(self):
        """Verifica se é conta analítica (não tem filhas)."""
        return not self.eh_sintetica
    
    def get_saldo(self, data_inicio=None, data_fim=None):
        """Calcula saldo da conta no período."""
        query = LancamentoFinanceiro.query.filter_by(plano_conta_id=self.id)
        
        if data_inicio:
            query = query.filter(LancamentoFinanceiro.data_lancamento >= data_inicio)
        if data_fim:
            query = query.filter(LancamentoFinanceiro.data_lancamento <= data_fim)
        
        total = sum(Decimal(str(lanc.valor or 0)) for lanc in query.all())
        
        # Se tem filhas, somar saldo delas também
        if self.eh_sintetica:
            for filha in self.contas_filhas:
                total += filha.get_saldo(data_inicio, data_fim)
        
        return total
    
    def to_dict(self):
        """Converte para dicionário."""
        return {
            'id': self.id,
            'codigo': self.codigo,
            'codigo_completo': self.codigo_completo,
            'nome': self.nome,
            'nome_completo': self.nome_completo,
            'descricao': self.descricao,
            'tipo': self.tipo,
            'nivel': self.nivel,
            'conta_pai_id': self.conta_pai_id,
            'aceita_lancamento': self.aceita_lancamento,
            'ativa': self.ativa,
            'natureza': self.natureza,
            'ordem': self.ordem,
            'eh_sintetica': self.eh_sintetica,
            'eh_analitica': self.eh_analitica
        }
    
    @classmethod
    def criar_plano_padrao(cls):
        """Cria estrutura padrão de plano de contas."""
        contas_padrao = [
            # ATIVO
            {'codigo': '1', 'nome': 'ATIVO', 'tipo': 'ATIVO', 'nivel': 1, 'aceita_lancamento': False},
            {'codigo': '1.1', 'nome': 'Ativo Circulante', 'tipo': 'ATIVO', 'nivel': 2, 'pai': '1', 'aceita_lancamento': False},
            {'codigo': '1.1.1', 'nome': 'Caixa e Bancos', 'tipo': 'ATIVO', 'nivel': 3, 'pai': '1.1'},
            {'codigo': '1.1.2', 'nome': 'Contas a Receber', 'tipo': 'ATIVO', 'nivel': 3, 'pai': '1.1'},
            {'codigo': '1.1.3', 'nome': 'Estoque', 'tipo': 'ATIVO', 'nivel': 3, 'pai': '1.1'},
            
            # PASSIVO
            {'codigo': '2', 'nome': 'PASSIVO', 'tipo': 'PASSIVO', 'nivel': 1, 'aceita_lancamento': False},
            {'codigo': '2.1', 'nome': 'Passivo Circulante', 'tipo': 'PASSIVO', 'nivel': 2, 'pai': '2', 'aceita_lancamento': False},
            {'codigo': '2.1.1', 'nome': 'Fornecedores', 'tipo': 'PASSIVO', 'nivel': 3, 'pai': '2.1'},
            {'codigo': '2.1.2', 'nome': 'Contas a Pagar', 'tipo': 'PASSIVO', 'nivel': 3, 'pai': '2.1'},
            {'codigo': '2.1.3', 'nome': 'Impostos a Recolher', 'tipo': 'PASSIVO', 'nivel': 3, 'pai': '2.1'},
            
            # RECEITAS
            {'codigo': '3', 'nome': 'RECEITAS', 'tipo': 'RECEITA', 'nivel': 1, 'aceita_lancamento': False},
            {'codigo': '3.1', 'nome': 'Receita de Serviços', 'tipo': 'RECEITA', 'nivel': 2, 'pai': '3'},
            {'codigo': '3.2', 'nome': 'Receita de Vendas', 'tipo': 'RECEITA', 'nivel': 2, 'pai': '3'},
            {'codigo': '3.3', 'nome': 'Outras Receitas', 'tipo': 'RECEITA', 'nivel': 2, 'pai': '3'},
            
            # DESPESAS
            {'codigo': '4', 'nome': 'DESPESAS', 'tipo': 'DESPESA', 'nivel': 1, 'aceita_lancamento': False},
            {'codigo': '4.1', 'nome': 'Despesas Operacionais', 'tipo': 'DESPESA', 'nivel': 2, 'pai': '4', 'aceita_lancamento': False},
            {'codigo': '4.1.1', 'nome': 'Salários e Encargos', 'tipo': 'DESPESA', 'nivel': 3, 'pai': '4.1'},
            {'codigo': '4.1.2', 'nome': 'Aluguel', 'tipo': 'DESPESA', 'nivel': 3, 'pai': '4.1'},
            {'codigo': '4.1.3', 'nome': 'Energia Elétrica', 'tipo': 'DESPESA', 'nivel': 3, 'pai': '4.1'},
            {'codigo': '4.1.4', 'nome': 'Telefone e Internet', 'tipo': 'DESPESA', 'nivel': 3, 'pai': '4.1'},
            {'codigo': '4.2', 'nome': 'Despesas Administrativas', 'tipo': 'DESPESA', 'nivel': 2, 'pai': '4', 'aceita_lancamento': False},
            {'codigo': '4.2.1', 'nome': 'Material de Escritório', 'tipo': 'DESPESA', 'nivel': 3, 'pai': '4.2'},
            {'codigo': '4.2.2', 'nome': 'Material de Limpeza', 'tipo': 'DESPESA', 'nivel': 3, 'pai': '4.2'},
        ]
        
        contas_criadas = {}
        
        for conta_data in contas_padrao:
            # Buscar conta pai se existir
            conta_pai = None
            if 'pai' in conta_data:
                conta_pai = contas_criadas.get(conta_data['pai'])
            
            conta = cls(
                codigo=conta_data['codigo'],
                nome=conta_data['nome'],
                tipo=conta_data['tipo'],
                nivel=conta_data['nivel'],
                conta_pai_id=conta_pai.id if conta_pai else None,
                aceita_lancamento=conta_data.get('aceita_lancamento', True),
                ativa=True
            )
            
            db.session.add(conta)
            db.session.flush()
            contas_criadas[conta_data['codigo']] = conta
        
        db.session.commit()
        return len(contas_criadas)


class OrcamentoAnual(BaseModel):
    """
    Model para Orçamento Anual.
    
    Permite planejar valores orçados mensalmente por categorias/centros de custo,
    comparar com valores realizados e acompanhar execução orçamentária.
    """
    
    __tablename__ = 'orcamentos_anuais'
    __table_args__ = {'extend_existing': True}
    
    # Informações Básicas
    ano = db.Column(db.Integer, nullable=False, index=True)
    mes = db.Column(db.Integer, nullable=False, index=True)  # 1-12
    descricao = db.Column(db.String(200))
    
    # Tipo e Categoria
    tipo = db.Column(db.String(20), nullable=False)  # RECEITA ou DESPESA
    categoria = db.Column(db.String(100), nullable=False, index=True)
    
    # Valores
    valor_orcado = db.Column(db.Numeric(12, 2), nullable=False, default=0)
    
    # Relacionamentos
    centro_custo_id = db.Column(db.Integer, db.ForeignKey('centros_custo.id'), nullable=True)
    plano_conta_id = db.Column(db.Integer, db.ForeignKey('plano_contas.id'), nullable=True)
    
    # Status
    ativo = db.Column(db.Boolean, default=True)
    
    # Observações
    observacoes = db.Column(db.Text)
    
    # Relacionamentos
    centro_custo = db.relationship('CentroCusto', backref='orcamentos', foreign_keys=[centro_custo_id])
    plano_conta = db.relationship('PlanoContas', backref='orcamentos', foreign_keys=[plano_conta_id])
    
    def __repr__(self):
        return f'<OrcamentoAnual {self.ano}/{self.mes:02d} - {self.categoria}: R$ {self.valor_orcado}>'
    
    @property
    def mes_nome(self):
        """Retorna nome do mês."""
        meses = {
            1: 'Janeiro', 2: 'Fevereiro', 3: 'Março', 4: 'Abril',
            5: 'Maio', 6: 'Junho', 7: 'Julho', 8: 'Agosto',
            9: 'Setembro', 10: 'Outubro', 11: 'Novembro', 12: 'Dezembro'
        }
        return meses.get(self.mes, 'N/A')
    
    @property
    def periodo(self):
        """Retorna período formatado."""
        return f"{self.mes_nome}/{self.ano}"
    
    @property
    def tipo_icone(self):
        """Retorna ícone baseado no tipo."""
        return 'fas fa-arrow-up text-success' if self.tipo == 'RECEITA' else 'fas fa-arrow-down text-danger'
    
    def calcular_realizado(self):
        """Calcula valor realizado no período."""
        from datetime import datetime
        
        # Data inicial e final do mês
        data_inicio = datetime(self.ano, self.mes, 1)
        if self.mes == 12:
            data_fim = datetime(self.ano + 1, 1, 1)
        else:
            data_fim = datetime(self.ano, self.mes + 1, 1)
        
        # Busca lançamentos do período
        query = LancamentoFinanceiro.query.filter(
            LancamentoFinanceiro.data_vencimento >= data_inicio,
            LancamentoFinanceiro.data_vencimento < data_fim,
            LancamentoFinanceiro.tipo == self.tipo
        )
        
        # Filtra por centro de custo se definido
        if self.centro_custo_id:
            query = query.filter(LancamentoFinanceiro.centro_custo_id == self.centro_custo_id)
        
        # Filtra por plano de contas se definido
        if self.plano_conta_id:
            query = query.filter(LancamentoFinanceiro.plano_conta_id == self.plano_conta_id)
        
        # Soma valores
        total = db.session.query(
            db.func.sum(LancamentoFinanceiro.valor)
        ).filter(
            LancamentoFinanceiro.id.in_([l.id for l in query.all()])
        ).scalar() or 0
        
        return float(total)
    
    @property
    def valor_realizado(self):
        """Property para valor realizado."""
        return self.calcular_realizado()
    
    @property
    def percentual_executado(self):
        """Retorna percentual de execução."""
        if self.valor_orcado == 0:
            return 0
        return (self.valor_realizado / float(self.valor_orcado)) * 100
    
    @property
    def variacao(self):
        """Retorna variação (realizado - orçado)."""
        return self.valor_realizado - float(self.valor_orcado)
    
    @property
    def status_orcamento(self):
        """Retorna status do orçamento."""
        perc = self.percentual_executado
        
        if perc <= 80:
            return {'texto': 'Dentro do Orçamento', 'classe': 'success'}
        elif perc <= 100:
            return {'texto': 'Atenção', 'classe': 'warning'}
        else:
            return {'texto': 'Estourado', 'classe': 'danger'}
    
    @classmethod
    def criar_orcamento_padrao(cls, ano):
        """
        Cria orçamentos padrão para o ano todo.
        
        Args:
            ano: Ano para criar os orçamentos
            
        Returns:
            int: Quantidade de orçamentos criados
        """
        categorias_padrao = [
            # RECEITAS
            {'tipo': 'RECEITA', 'categoria': 'Vendas Sistemas Fotovoltaicos', 'valor': 50000},
            {'tipo': 'RECEITA', 'categoria': 'Serviços de Instalação', 'valor': 15000},
            {'tipo': 'RECEITA', 'categoria': 'Manutenção e Monitoramento', 'valor': 5000},
            
            # DESPESAS
            {'tipo': 'DESPESA', 'categoria': 'Folha de Pagamento', 'valor': 20000},
            {'tipo': 'DESPESA', 'categoria': 'Fornecedores - Equipamentos', 'valor': 30000},
            {'tipo': 'DESPESA', 'categoria': 'Marketing e Publicidade', 'valor': 3000},
            {'tipo': 'DESPESA', 'categoria': 'Aluguel e Condomínio', 'valor': 2500},
            {'tipo': 'DESPESA', 'categoria': 'Energia e Telecomunicações', 'valor': 800},
            {'tipo': 'DESPESA', 'categoria': 'Impostos e Taxas', 'valor': 5000},
            {'tipo': 'DESPESA', 'categoria': 'Despesas Administrativas', 'valor': 1500},
        ]
        
        orcamentos_criados = 0
        
        for mes in range(1, 13):
            for cat in categorias_padrao:
                # Verifica se já existe
                existe = cls.query.filter_by(
                    ano=ano,
                    mes=mes,
                    tipo=cat['tipo'],
                    categoria=cat['categoria']
                ).first()
                
                if not existe:
                    orcamento = cls(
                        ano=ano,
                        mes=mes,
                        tipo=cat['tipo'],
                        categoria=cat['categoria'],
                        valor_orcado=cat['valor'],
                        ativo=True
                    )
                    db.session.add(orcamento)
                    orcamentos_criados += 1
        
        db.session.commit()
        return orcamentos_criados


class NotaFiscal(BaseModel):
    """
    Model para Gestão de Notas Fiscais.
    
    Armazena informações de notas fiscais de entrada e saída,
    com upload de arquivos XML/PDF e integração com lançamentos.
    """
    
    __tablename__ = 'notas_fiscais'
    __table_args__ = {'extend_existing': True}
    
    # Informações Básicas
    numero = db.Column(db.String(20), nullable=False, index=True)
    serie = db.Column(db.String(10))
    modelo = db.Column(db.String(10))  # 55=NF-e, 65=NFC-e, etc
    tipo = db.Column(db.String(10), nullable=False)  # ENTRADA ou SAIDA
    
    # Chave de Acesso (NF-e)
    chave_acesso = db.Column(db.String(44), unique=True, index=True)
    
    # Datas
    data_emissao = db.Column(db.Date, nullable=False, index=True)
    data_entrada_saida = db.Column(db.Date)
    
    # Valores
    valor_total = db.Column(db.Numeric(12, 2), nullable=False, default=0)
    valor_produtos = db.Column(db.Numeric(12, 2), default=0)
    valor_servicos = db.Column(db.Numeric(12, 2), default=0)
    valor_frete = db.Column(db.Numeric(12, 2), default=0)
    valor_seguro = db.Column(db.Numeric(12, 2), default=0)
    valor_desconto = db.Column(db.Numeric(12, 2), default=0)
    valor_outras_despesas = db.Column(db.Numeric(12, 2), default=0)
    
    # Impostos
    valor_icms = db.Column(db.Numeric(12, 2), default=0)
    valor_ipi = db.Column(db.Numeric(12, 2), default=0)
    valor_pis = db.Column(db.Numeric(12, 2), default=0)
    valor_cofins = db.Column(db.Numeric(12, 2), default=0)
    
    # Emitente/Destinatário
    emitente_nome = db.Column(db.String(200))
    emitente_cnpj = db.Column(db.String(18))
    emitente_ie = db.Column(db.String(20))
    
    destinatario_nome = db.Column(db.String(200))
    destinatario_cnpj = db.Column(db.String(18))
    destinatario_ie = db.Column(db.String(20))
    
    # Natureza da Operação
    natureza_operacao = db.Column(db.String(100))
    cfop = db.Column(db.String(10))
    
    # Status
    status = db.Column(db.String(20), default='PENDENTE')
    # Status: PENDENTE, PROCESSADA, PAGA, CANCELADA
    
    # Arquivos
    arquivo_xml = db.Column(db.Text)  # Caminho ou conteúdo base64
    arquivo_pdf = db.Column(db.Text)  # Caminho ou conteúdo base64
    arquivo_xml_nome = db.Column(db.String(255))
    arquivo_pdf_nome = db.Column(db.String(255))
    
    # Observações
    observacoes = db.Column(db.Text)
    
    # Relacionamentos
    cliente_id = db.Column(db.Integer, db.ForeignKey('clientes.id'), nullable=True)
    fornecedor_id = db.Column(db.Integer, db.ForeignKey('fornecedores.id'), nullable=True)
    lancamento_id = db.Column(db.Integer, db.ForeignKey('lancamentos_financeiros.id'), nullable=True)
    
    # Relacionamentos
    cliente = db.relationship('Cliente', backref='notas_fiscais', foreign_keys=[cliente_id])
    fornecedor = db.relationship('Fornecedor', backref='notas_fiscais', foreign_keys=[fornecedor_id])
    lancamento = db.relationship('LancamentoFinanceiro', backref='nota_fiscal', foreign_keys=[lancamento_id])
    
    def __repr__(self):
        return f'<NotaFiscal {self.numero}/{self.serie} - R$ {self.valor_total}>'
    
    @property
    def numero_completo(self):
        """Retorna número completo da nota."""
        if self.serie:
            return f"{self.numero}/{self.serie}"
        return self.numero
    
    @property
    def tipo_icone(self):
        """Retorna ícone baseado no tipo."""
        if self.tipo == 'ENTRADA':
            return 'fas fa-arrow-down text-danger'
        return 'fas fa-arrow-up text-success'
    
    @property
    def status_badge(self):
        """Retorna classe CSS do badge de status."""
        badges = {
            'PENDENTE': 'warning',
            'PROCESSADA': 'info',
            'PAGA': 'success',
            'CANCELADA': 'danger'
        }
        return badges.get(self.status, 'secondary')
    
    @property
    def possui_xml(self):
        """Verifica se possui arquivo XML."""
        return bool(self.arquivo_xml)
    
    @property
    def possui_pdf(self):
        """Verifica se possui arquivo PDF."""
        return bool(self.arquivo_pdf)
    
    @property
    def empresa(self):
        """Retorna cliente ou fornecedor relacionado."""
        if self.tipo == 'SAIDA' and self.cliente:
            return self.cliente
        elif self.tipo == 'ENTRADA' and self.fornecedor:
            return self.fornecedor
        return None
    
    @property
    def empresa_nome(self):
        """Retorna nome da empresa relacionada."""
        empresa = self.empresa
        if empresa:
            return empresa.nome
        # Fallback para dados do XML
        if self.tipo == 'ENTRADA':
            return self.emitente_nome
        return self.destinatario_nome
    
    @property
    def empresa_cnpj(self):
        """Retorna CNPJ da empresa relacionada."""
        empresa = self.empresa
        if empresa:
            return empresa.cnpj
        # Fallback para dados do XML
        if self.tipo == 'ENTRADA':
            return self.emitente_cnpj
        return self.destinatario_cnpj
    
    def validar_cnpj(self, cnpj):
        """
        Valida CNPJ básico (apenas formato).
        
        Args:
            cnpj: CNPJ para validar
            
        Returns:
            bool: True se válido
        """
        if not cnpj:
            return False
        
        # Remove caracteres não numéricos
        cnpj_numeros = ''.join(filter(str.isdigit, cnpj))
        
        # Verifica se tem 14 dígitos
        return len(cnpj_numeros) == 14
    
    def criar_lancamento_automatico(self):
        """
        Cria lançamento financeiro automaticamente baseado na nota.
        
        Returns:
            LancamentoFinanceiro: Lançamento criado
        """
        if self.lancamento_id:
            return self.lancamento  # Já tem lançamento
        
        # Determina tipo do lançamento
        tipo_lancamento = 'DESPESA' if self.tipo == 'ENTRADA' else 'RECEITA'
        
        # Cria lançamento
        lancamento = LancamentoFinanceiro(
            tipo=tipo_lancamento,
            descricao=f"NF {self.numero_completo} - {self.empresa_nome or self.natureza_operacao}",
            valor=self.valor_total,
            data_vencimento=self.data_emissao,
            data_emissao=self.data_emissao,
            cliente_id=self.cliente_id if self.tipo == 'SAIDA' else None,
            fornecedor_id=self.fornecedor_id if self.tipo == 'ENTRADA' else None,
            status='PENDENTE',
            categoria=self.natureza_operacao or 'Nota Fiscal',
            observacoes=f"Gerado automaticamente da NF {self.numero_completo}"
        )
        
        db.session.add(lancamento)
        db.session.flush()
        
        self.lancamento_id = lancamento.id
        
        return lancamento
    
    @classmethod
    def parse_xml_nfe(cls, xml_content):
        """
        Faz parse de XML de NF-e e extrai dados principais.
        
        Args:
            xml_content: Conteúdo do XML
            
        Returns:
            dict: Dicionário com dados extraídos
        """
        import xml.etree.ElementTree as ET
        from datetime import datetime
        
        try:
            # Parse XML
            root = ET.fromstring(xml_content)
            
            # Namespaces comuns de NF-e
            ns = {'nfe': 'http://www.portalfiscal.inf.br/nfe'}
            
            # Tenta sem namespace também
            inf_nfe = root.find('.//infNFe') or root.find('.//{http://www.portalfiscal.inf.br/nfe}infNFe')
            
            if not inf_nfe:
                return {'error': 'XML inválido - tag infNFe não encontrada'}
            
            # Extrai chave de acesso
            chave = inf_nfe.get('Id', '').replace('NFe', '')
            
            # Função auxiliar para pegar texto
            def get_text(parent, tag, default=''):
                elem = parent.find(f'.//{tag}') or parent.find(f'.//{{{ns["nfe"]}}}{tag}')
                return elem.text if elem is not None else default
            
            # Identificação
            ide = inf_nfe.find('.//ide') or inf_nfe.find('.//{http://www.portalfiscal.inf.br/nfe}ide')
            
            # Emitente
            emit = inf_nfe.find('.//emit') or inf_nfe.find('.//{http://www.portalfiscal.inf.br/nfe}emit')
            
            # Destinatário
            dest = inf_nfe.find('.//dest') or inf_nfe.find('.//{http://www.portalfiscal.inf.br/nfe}dest')
            
            # Totais
            total = inf_nfe.find('.//total') or inf_nfe.find('.//{http://www.portalfiscal.inf.br/nfe}total')
            icms_tot = total.find('.//ICMSTot') or total.find('.//{http://www.portalfiscal.inf.br/nfe}ICMSTot') if total else None
            
            # Monta dados
            dados = {
                'chave_acesso': chave,
                'numero': get_text(ide, 'nNF'),
                'serie': get_text(ide, 'serie'),
                'modelo': get_text(ide, 'mod'),
                'natureza_operacao': get_text(ide, 'natOp'),
                'cfop': get_text(ide, 'CFOP'),
                'data_emissao': datetime.strptime(get_text(ide, 'dhEmi')[:10], '%Y-%m-%d').date() if get_text(ide, 'dhEmi') else None,
                
                # Emitente
                'emitente_nome': get_text(emit, 'xNome'),
                'emitente_cnpj': get_text(emit, 'CNPJ'),
                'emitente_ie': get_text(emit, 'IE'),
                
                # Destinatário
                'destinatario_nome': get_text(dest, 'xNome'),
                'destinatario_cnpj': get_text(dest, 'CNPJ'),
                'destinatario_ie': get_text(dest, 'IE'),
            }
            
            # Valores
            if icms_tot is not None:
                dados.update({
                    'valor_produtos': float(get_text(icms_tot, 'vProd') or 0),
                    'valor_frete': float(get_text(icms_tot, 'vFrete') or 0),
                    'valor_seguro': float(get_text(icms_tot, 'vSeg') or 0),
                    'valor_desconto': float(get_text(icms_tot, 'vDesc') or 0),
                    'valor_outras_despesas': float(get_text(icms_tot, 'vOutro') or 0),
                    'valor_total': float(get_text(icms_tot, 'vNF') or 0),
                    'valor_icms': float(get_text(icms_tot, 'vICMS') or 0),
                    'valor_ipi': float(get_text(icms_tot, 'vIPI') or 0),
                    'valor_pis': float(get_text(icms_tot, 'vPIS') or 0),
                    'valor_cofins': float(get_text(icms_tot, 'vCOFINS') or 0),
                })
            
            return dados
            
        except Exception as e:
            return {'error': f'Erro ao fazer parse do XML: {str(e)}'}


# ============================================================
# NOTIFICAÇÕES E ALERTAS
# ============================================================

class Notificacao(BaseModel):
    """
    Model para Notificações e Alertas do Sistema.
    
    Gerencia alertas automáticos de vencimentos, estouros,
    saldo negativo, etc.
    """
    
    __tablename__ = 'notificacoes'
    __table_args__ = {'extend_existing': True}
    
    # Informações Básicas
    titulo = db.Column(db.String(200), nullable=False)
    mensagem = db.Column(db.Text, nullable=False)
    tipo = db.Column(db.String(30), nullable=False)
    # Tipos: VENCIMENTO, SALDO_NEGATIVO, ESTOURO_ORCAMENTO, CONCILIACAO_PENDENTE, CUSTO_FIXO
    
    # Prioridade
    prioridade = db.Column(db.String(20), default='MEDIA')
    # Prioridades: BAIXA, MEDIA, ALTA, URGENTE
    
    # Status
    lida = db.Column(db.Boolean, default=False)
    data_leitura = db.Column(db.DateTime)
    
    # Relacionamento com entidade
    entidade_tipo = db.Column(db.String(50))  # LancamentoFinanceiro, ContaBancaria, etc
    entidade_id = db.Column(db.Integer)
    
    # Ação sugerida
    acao_url = db.Column(db.String(255))  # URL para resolver o problema
    acao_texto = db.Column(db.String(100))  # Texto do botão de ação
    
    # Usuário destinatário
    usuario = db.Column(db.String(100))
    
    # Email enviado?
    email_enviado = db.Column(db.Boolean, default=False)
    data_envio_email = db.Column(db.DateTime)
    
    def __repr__(self):
        return f'<Notificacao {self.id}: {self.titulo}>'
    
    @property
    def tipo_icone(self):
        """Retorna ícone baseado no tipo."""
        icones = {
            'VENCIMENTO': 'fas fa-calendar-times text-warning',
            'SALDO_NEGATIVO': 'fas fa-exclamation-triangle text-danger',
            'ESTOURO_ORCAMENTO': 'fas fa-chart-line text-danger',
            'CONCILIACAO_PENDENTE': 'fas fa-handshake text-info',
            'CUSTO_FIXO': 'fas fa-sync text-primary',
            'PAGAMENTO_APROVADO': 'fas fa-check-circle text-success',
            'PAGAMENTO_REJEITADO': 'fas fa-times-circle text-danger'
        }
        return icones.get(self.tipo, 'fas fa-bell text-secondary')
    
    @property
    def tipo_cor(self):
        """Retorna cor do badge baseado no tipo."""
        cores = {
            'VENCIMENTO': 'warning',
            'SALDO_NEGATIVO': 'danger',
            'ESTOURO_ORCAMENTO': 'danger',
            'CONCILIACAO_PENDENTE': 'info',
            'CUSTO_FIXO': 'primary',
            'PAGAMENTO_APROVADO': 'success',
            'PAGAMENTO_REJEITADO': 'danger'
        }
        return cores.get(self.tipo, 'secondary')
    
    @property
    def prioridade_cor(self):
        """Retorna cor da prioridade."""
        cores = {
            'BAIXA': 'secondary',
            'MEDIA': 'info',
            'ALTA': 'warning',
            'URGENTE': 'danger'
        }
        return cores.get(self.prioridade, 'secondary')
    
    def marcar_como_lida(self):
        """Marca notificação como lida."""
        self.lida = True
        self.data_leitura = datetime.utcnow()
        db.session.commit()
    
    @classmethod
    def criar_notificacao(cls, titulo, mensagem, tipo, prioridade='MEDIA', 
                         entidade_tipo=None, entidade_id=None, 
                         acao_url=None, acao_texto=None, usuario=None):
        """
        Cria uma nova notificação.
        
        Args:
            titulo: Título da notificação
            mensagem: Mensagem detalhada
            tipo: Tipo (VENCIMENTO, SALDO_NEGATIVO, etc)
            prioridade: BAIXA, MEDIA, ALTA, URGENTE
            entidade_tipo: Tipo da entidade relacionada
            entidade_id: ID da entidade
            acao_url: URL para ação
            acao_texto: Texto do botão
            usuario: Usuário destinatário
        
        Returns:
            Notificacao: Instância criada
        """
        notif = cls(
            titulo=titulo,
            mensagem=mensagem,
            tipo=tipo,
            prioridade=prioridade,
            entidade_tipo=entidade_tipo,
            entidade_id=entidade_id,
            acao_url=acao_url,
            acao_texto=acao_texto,
            usuario=usuario
        )
        
        db.session.add(notif)
        db.session.commit()
        
        return notif
    
    @classmethod
    def get_nao_lidas(cls, usuario=None):
        """Retorna notificações não lidas."""
        query = cls.query.filter_by(lida=False, ativo=True)
        if usuario:
            query = query.filter_by(usuario=usuario)
        return query.order_by(cls.data_criacao.desc())
    
    @classmethod
    def get_por_prioridade(cls, prioridade, usuario=None):
        """Retorna notificações por prioridade."""
        query = cls.query.filter_by(prioridade=prioridade, lida=False, ativo=True)
        if usuario:
            query = query.filter_by(usuario=usuario)
        return query.order_by(cls.data_criacao.desc())
    
    @classmethod
    def contar_nao_lidas(cls, usuario=None):
        """Conta notificações não lidas."""
        query = cls.query.filter_by(lida=False, ativo=True)
        if usuario:
            query = query.filter_by(usuario=usuario)
        return query.count()
    
    @classmethod
    def verificar_vencimentos(cls):
        """
        Verifica lançamentos vencendo e cria notificações.
        Executa verificação de:
        - Vencimentos hoje
        - Vencimentos próximos 3 dias
        - Vencimentos próximos 7 dias
        """
        from datetime import timedelta
        
        hoje = date.today()
        em_3_dias = hoje + timedelta(days=3)
        em_7_dias = hoje + timedelta(days=7)
        
        notificacoes_criadas = []
        
        # Vencendo hoje
        vencendo_hoje = LancamentoFinanceiro.query.filter(
            LancamentoFinanceiro.data_vencimento == hoje,
            LancamentoFinanceiro.status == 'pendente',
            LancamentoFinanceiro.ativo == True
        ).all()
        
        for lanc in vencendo_hoje:
            # Verifica se já existe notificação
            existe = cls.query.filter_by(
                entidade_tipo='LancamentoFinanceiro',
                entidade_id=lanc.id,
                tipo='VENCIMENTO',
                lida=False
            ).first()
            
            if not existe:
                notif = cls.criar_notificacao(
                    titulo=f'💰 Vencimento HOJE: {lanc.descricao}',
                    mensagem=f'O lançamento "{lanc.descricao}" vence hoje! Valor: {lanc.valor_formatado}',
                    tipo='VENCIMENTO',
                    prioridade='URGENTE',
                    entidade_tipo='LancamentoFinanceiro',
                    entidade_id=lanc.id,
                    acao_url=f'/financeiro/lancamentos/{lanc.id}/pagar',
                    acao_texto='Pagar Agora'
                )
                notificacoes_criadas.append(notif)
        
        # Vencendo em 3 dias
        vencendo_3dias = LancamentoFinanceiro.query.filter(
            LancamentoFinanceiro.data_vencimento == em_3_dias,
            LancamentoFinanceiro.status == 'pendente',
            LancamentoFinanceiro.ativo == True
        ).all()
        
        for lanc in vencendo_3dias:
            existe = cls.query.filter_by(
                entidade_tipo='LancamentoFinanceiro',
                entidade_id=lanc.id,
                tipo='VENCIMENTO',
                lida=False
            ).first()
            
            if not existe:
                notif = cls.criar_notificacao(
                    titulo=f'⏰ Vence em 3 dias: {lanc.descricao}',
                    mensagem=f'O lançamento "{lanc.descricao}" vence em 3 dias. Valor: {lanc.valor_formatado}',
                    tipo='VENCIMENTO',
                    prioridade='ALTA',
                    entidade_tipo='LancamentoFinanceiro',
                    entidade_id=lanc.id,
                    acao_url=f'/financeiro/lancamentos/{lanc.id}/editar',
                    acao_texto='Ver Detalhes'
                )
                notificacoes_criadas.append(notif)
        
        return notificacoes_criadas
    
    @classmethod
    def verificar_saldo_negativo(cls):
        """Verifica contas com saldo negativo."""
        contas_negativas = ContaBancaria.query.filter(
            ContaBancaria.saldo_atual < 0,
            ContaBancaria.ativo == True,
            ContaBancaria.ativa == True
        ).all()
        
        notificacoes_criadas = []
        
        for conta in contas_negativas:
            # Verifica se já existe notificação recente (últimas 24h)
            ontem = datetime.utcnow() - timedelta(days=1)
            existe = cls.query.filter(
                cls.entidade_tipo == 'ContaBancaria',
                cls.entidade_id == conta.id,
                cls.tipo == 'SALDO_NEGATIVO',
                cls.lida == False,
                cls.data_criacao >= ontem
            ).first()
            
            if not existe:
                notif = cls.criar_notificacao(
                    titulo=f'⚠️ Saldo Negativo: {conta.nome}',
                    mensagem=f'A conta "{conta.nome}" está com saldo negativo: {conta.saldo_formatado}',
                    tipo='SALDO_NEGATIVO',
                    prioridade='URGENTE',
                    entidade_tipo='ContaBancaria',
                    entidade_id=conta.id,
                    acao_url=f'/financeiro/contas-bancarias',
                    acao_texto='Ver Conta'
                )
                notificacoes_criadas.append(notif)
        
        return notificacoes_criadas
    
    @classmethod
    def verificar_estouro_orcamento(cls):
        """Verifica orçamentos estourados."""
        from datetime import date
        
        mes_atual = date.today().month
        ano_atual = date.today().year
        
        # Buscar orçamentos do mês atual
        orcamentos = OrcamentoAnual.query.filter_by(
            ano=ano_atual,
            mes=mes_atual,
            ativo=True
        ).all()
        
        notificacoes_criadas = []
        
        for orc in orcamentos:
            perc = orc.percentual_executado
            
            # Alerta se passar de 100%
            if perc > 100:
                existe = cls.query.filter_by(
                    entidade_tipo='OrcamentoAnual',
                    entidade_id=orc.id,
                    tipo='ESTOURO_ORCAMENTO',
                    lida=False
                ).first()
                
                if not existe:
                    notif = cls.criar_notificacao(
                        titulo=f'🚨 Orçamento Estourado: {orc.categoria}',
                        mensagem=f'O orçamento de "{orc.categoria}" está {perc:.1f}% executado (estouro de {perc-100:.1f}%)',
                        tipo='ESTOURO_ORCAMENTO',
                        prioridade='URGENTE',
                        entidade_tipo='OrcamentoAnual',
                        entidade_id=orc.id,
                        acao_url='/financeiro/orcamento-anual/dashboard',
                        acao_texto='Ver Orçamento'
                    )
                    notificacoes_criadas.append(notif)
            
            # Alerta se passar de 90%
            elif perc > 90:
                existe = cls.query.filter_by(
                    entidade_tipo='OrcamentoAnual',
                    entidade_id=orc.id,
                    tipo='ESTOURO_ORCAMENTO',
                    lida=False
                ).first()
                
                if not existe:
                    notif = cls.criar_notificacao(
                        titulo=f'⚠️ Atenção: {orc.categoria} em {perc:.1f}%',
                        mensagem=f'O orçamento de "{orc.categoria}" está próximo do limite ({perc:.1f}% executado)',
                        tipo='ESTOURO_ORCAMENTO',
                        prioridade='ALTA',
                        entidade_tipo='OrcamentoAnual',
                        entidade_id=orc.id,
                        acao_url='/financeiro/orcamento-anual/dashboard',
                        acao_texto='Ver Orçamento'
                    )
                    notificacoes_criadas.append(notif)
        
        return notificacoes_criadas
    
    @classmethod
    def verificar_conciliacao_pendente(cls):
        """Verifica extratos pendentes de conciliação."""
        # Contar extratos não conciliados
        pendentes = ExtratoBancario.query.filter_by(
            conciliado=False,
            ativo=True
        ).count()
        
        notificacoes_criadas = []
        
        if pendentes > 0:
            # Verifica se já existe notificação recente
            ontem = datetime.utcnow() - timedelta(days=1)
            existe = cls.query.filter(
                cls.tipo == 'CONCILIACAO_PENDENTE',
                cls.lida == False,
                cls.data_criacao >= ontem
            ).first()
            
            if not existe:
                notif = cls.criar_notificacao(
                    titulo=f'📋 {pendentes} Extrato(s) Pendente(s) de Conciliação',
                    mensagem=f'Existem {pendentes} lançamentos de extrato bancário aguardando conciliação.',
                    tipo='CONCILIACAO_PENDENTE',
                    prioridade='MEDIA',
                    acao_url='/financeiro/conciliacao-bancaria',
                    acao_texto='Conciliar Agora'
                )
                notificacoes_criadas.append(notif)
        
        return notificacoes_criadas
    
    @classmethod
    def verificar_todas(cls):
        """
        Executa todas as verificações de alertas.
        Deve ser chamado por CRON ou scheduler.
        """
        notificacoes = []
        
        notificacoes.extend(cls.verificar_vencimentos())
        notificacoes.extend(cls.verificar_saldo_negativo())
        notificacoes.extend(cls.verificar_estouro_orcamento())
        notificacoes.extend(cls.verificar_conciliacao_pendente())
        
        return notificacoes


# ============================================================
# RATEIO DE DESPESAS
# ============================================================

class RateioDespesa(BaseModel):
    """
    Model para Rateio de Despesas.
    
    Permite dividir uma despesa entre múltiplos centros de custo,
    projetos ou departamentos.
    """
    
    __tablename__ = 'rateios_despesas'
    __table_args__ = {'extend_existing': True}
    
    # Lançamento principal
    lancamento_id = db.Column(db.Integer, db.ForeignKey('lancamentos_financeiros.id'), nullable=False)
    
    # Centro de custo destino
    centro_custo_id = db.Column(db.Integer, db.ForeignKey('centros_custo.id'), nullable=False)
    
    # Valores
    percentual = db.Column(db.Numeric(5, 2), nullable=False)  # 0 a 100
    valor_rateado = db.Column(db.Numeric(12, 2), nullable=False)
    
    # Observações
    observacoes = db.Column(db.Text)
    
    # Relacionamentos
    lancamento = db.relationship('LancamentoFinanceiro', backref='rateios', foreign_keys=[lancamento_id])
    centro_custo = db.relationship('CentroCusto', backref='rateios_recebidos', foreign_keys=[centro_custo_id])
    
    def __repr__(self):
        return f'<RateioDespesa L:{self.lancamento_id} -> CC:{self.centro_custo_id} ({self.percentual}%)>'
    
    @property
    def percentual_formatado(self):
        """Retorna percentual formatado."""
        return f"{self.percentual}%"
    
    @property
    def valor_formatado(self):
        """Retorna valor formatado."""
        return f"R$ {self.valor_rateado:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
    
    @classmethod
    def criar_rateio(cls, lancamento_id, distribuicao):
        """
        Cria rateio de despesa.
        
        Args:
            lancamento_id: ID do lançamento a ratear
            distribuicao: Lista de dicts com {'centro_custo_id': X, 'percentual': Y}
            
        Returns:
            list: Lista de rateios criados
            
        Raises:
            ValueError: Se percentuais não somam 100%
        """
        # Validar soma de percentuais
        total_perc = sum(float(d['percentual']) for d in distribuicao)
        if abs(total_perc - 100) > 0.01:  # Tolerância para arredondamento
            raise ValueError(f'Percentuais devem somar 100%. Total: {total_perc}%')
        
        # Buscar lançamento
        lancamento = LancamentoFinanceiro.query.get(lancamento_id)
        if not lancamento:
            raise ValueError('Lançamento não encontrado')
        
        # Remover rateios antigos se existirem
        cls.query.filter_by(lancamento_id=lancamento_id).delete()
        
        # Criar novos rateios
        rateios_criados = []
        valor_total = float(lancamento.valor)
        
        for dist in distribuicao:
            percentual = float(dist['percentual'])
            valor_rateado = (valor_total * percentual) / 100
            
            rateio = cls(
                lancamento_id=lancamento_id,
                centro_custo_id=dist['centro_custo_id'],
                percentual=percentual,
                valor_rateado=valor_rateado,
                observacoes=dist.get('observacoes')
            )
            
            db.session.add(rateio)
            rateios_criados.append(rateio)
        
        db.session.commit()
        
        return rateios_criados
    
    @classmethod
    def get_por_lancamento(cls, lancamento_id):
        """Retorna rateios de um lançamento."""
        return cls.query.filter_by(lancamento_id=lancamento_id, ativo=True).all()
    
    @classmethod
    def get_por_centro_custo(cls, centro_custo_id, data_inicio=None, data_fim=None):
        """Retorna rateios recebidos por um centro de custo."""
        query = cls.query.filter_by(centro_custo_id=centro_custo_id, ativo=True)
        
        if data_inicio or data_fim:
            query = query.join(LancamentoFinanceiro)
            if data_inicio:
                query = query.filter(LancamentoFinanceiro.data_lancamento >= data_inicio)
            if data_fim:
                query = query.filter(LancamentoFinanceiro.data_lancamento <= data_fim)
        
        return query.all()
    
    @classmethod
    def calcular_total_centro(cls, centro_custo_id, data_inicio=None, data_fim=None):
        """Calcula total rateado para um centro de custo."""
        rateios = cls.get_por_centro_custo(centro_custo_id, data_inicio, data_fim)
        return sum(float(r.valor_rateado) for r in rateios)


# ============================================================
# IMPORTAÇÃO EM LOTE
# ============================================================

class ImportacaoLote(BaseModel):
    """
    Model para Importação em Lote de Lançamentos.
    
    Controla importações de arquivos Excel/CSV.
    """
    
    __tablename__ = 'importacoes_lote'
    __table_args__ = {'extend_existing': True}
    
    # Informações do arquivo
    arquivo_nome = db.Column(db.String(255), nullable=False)
    arquivo_path = db.Column(db.String(500))
    tipo_arquivo = db.Column(db.String(20))  # EXCEL, CSV
    
    # Status da importação
    status = db.Column(db.String(30), default='PROCESSANDO')
    # Status: PROCESSANDO, CONCLUIDA, ERRO, PARCIAL
    
    # Contadores
    total_linhas = db.Column(db.Integer, default=0)
    linhas_importadas = db.Column(db.Integer, default=0)
    linhas_erro = db.Column(db.Integer, default=0)
    
    # Detalhes
    erros_detalhes = db.Column(db.Text)  # JSON com erros
    configuracao = db.Column(db.Text)  # JSON com mapeamento de colunas
    
    # Usuário responsável
    usuario = db.Column(db.String(100))
    
    # Timestamps
    data_inicio = db.Column(db.DateTime, default=datetime.utcnow)
    data_fim = db.Column(db.DateTime)
    
    def __repr__(self):
        return f'<ImportacaoLote {self.id}: {self.arquivo_nome} ({self.status})>'
    
    @property
    def status_cor(self):
        """Retorna cor do badge de status."""
        cores = {
            'PROCESSANDO': 'info',
            'CONCLUIDA': 'success',
            'ERRO': 'danger',
            'PARCIAL': 'warning'
        }
        return cores.get(self.status, 'secondary')
    
    @property
    def percentual_sucesso(self):
        """Calcula percentual de sucesso."""
        if self.total_linhas == 0:
            return 0
        return (self.linhas_importadas / self.total_linhas) * 100
    
    @property
    def duracao(self):
        """Calcula duração da importação."""
        if not self.data_fim:
            return None
        delta = self.data_fim - self.data_inicio
        return delta.total_seconds()
    
    def finalizar(self, status='CONCLUIDA'):
        """Finaliza importação."""
        self.status = status
        self.data_fim = datetime.utcnow()
        db.session.commit()


# ============================================================
# RELATÓRIOS CUSTOMIZÁVEIS
# ============================================================

class RelatorioCustomizado(BaseModel):
    """
    Model para Relatórios Customizáveis.
    
    Permite criar relatórios personalizados com campos,
    filtros e agrupamentos definidos pelo usuário.
    """
    
    __tablename__ = 'relatorios_customizados'
    __table_args__ = {'extend_existing': True}
    
    # Informações Básicas
    nome = db.Column(db.String(200), nullable=False)
    descricao = db.Column(db.Text)
    
    # Tipo de relatório
    tipo = db.Column(db.String(50), nullable=False)
    # Tipos: LANCAMENTOS, FLUXO_CAIXA, DRE, CONTAS_PAGAR, CONTAS_RECEBER, CENTROS_CUSTO
    
    # Configuração (JSON)
    campos_selecionados = db.Column(db.Text)  # JSON: ['campo1', 'campo2', ...]
    filtros = db.Column(db.Text)  # JSON: {'campo': 'valor', ...}
    agrupamento = db.Column(db.String(100))  # Campo para agrupar
    ordenacao = db.Column(db.String(100))  # Campo para ordenar
    ordem_direcao = db.Column(db.String(10), default='ASC')  # ASC ou DESC
    
    # Formato de exportação padrão
    formato_padrao = db.Column(db.String(20), default='EXCEL')  # EXCEL, PDF, CSV
    
    # Compartilhamento
    publico = db.Column(db.Boolean, default=False)
    usuario_criador = db.Column(db.String(100))
    
    # Favorito
    favorito = db.Column(db.Boolean, default=False)
    
    # Última execução
    ultima_execucao = db.Column(db.DateTime)
    total_execucoes = db.Column(db.Integer, default=0)
    
    def __repr__(self):
        return f'<RelatorioCustomizado {self.id}: {self.nome}>'
    
    @property
    def tipo_icone(self):
        """Retorna ícone baseado no tipo."""
        icones = {
            'LANCAMENTOS': 'fas fa-list',
            'FLUXO_CAIXA': 'fas fa-chart-line',
            'DRE': 'fas fa-chart-bar',
            'CONTAS_PAGAR': 'fas fa-file-invoice-dollar',
            'CONTAS_RECEBER': 'fas fa-receipt',
            'CENTROS_CUSTO': 'fas fa-sitemap'
        }
        return icones.get(self.tipo, 'fas fa-file-alt')
    
    def get_campos_lista(self):
        """Retorna lista de campos selecionados."""
        import json
        if self.campos_selecionados:
            return json.loads(self.campos_selecionados)
        return []
    
    def get_filtros_dict(self):
        """Retorna dicionário de filtros."""
        import json
        if self.filtros:
            return json.loads(self.filtros)
        return {}
    
    def set_campos(self, campos):
        """Define campos selecionados."""
        import json
        self.campos_selecionados = json.dumps(campos)
    
    def set_filtros(self, filtros_dict):
        """Define filtros."""
        import json
        self.filtros = json.dumps(filtros_dict)
    
    def executar(self):
        """
        Executa o relatório e retorna dados.
        
        Returns:
            list: Lista de resultados
        """
        self.ultima_execucao = datetime.utcnow()
        self.total_execucoes += 1
        db.session.commit()
        
        # Buscar dados baseado no tipo
        if self.tipo == 'LANCAMENTOS':
            return self._executar_lancamentos()
        elif self.tipo == 'FLUXO_CAIXA':
            return self._executar_fluxo_caixa()
        elif self.tipo == 'DRE':
            return self._executar_dre()
        elif self.tipo == 'CONTAS_PAGAR':
            return self._executar_contas_pagar()
        elif self.tipo == 'CONTAS_RECEBER':
            return self._executar_contas_receber()
        elif self.tipo == 'CENTROS_CUSTO':
            return self._executar_centros_custo()
        
        return []
    
    def _executar_lancamentos(self):
        """Executa relatório de lançamentos."""
        filtros = self.get_filtros_dict()
        
        query = LancamentoFinanceiro.query.filter_by(ativo=True)
        
        # Aplicar filtros
        if 'tipo' in filtros:
            query = query.filter_by(tipo=filtros['tipo'])
        
        if 'status' in filtros:
            query = query.filter_by(status=filtros['status'])
        
        if 'categoria' in filtros:
            query = query.filter_by(categoria=filtros['categoria'])
        
        if 'data_inicio' in filtros:
            query = query.filter(LancamentoFinanceiro.data_lancamento >= filtros['data_inicio'])
        
        if 'data_fim' in filtros:
            query = query.filter(LancamentoFinanceiro.data_lancamento <= filtros['data_fim'])
        
        if 'conta_bancaria_id' in filtros:
            query = query.filter_by(conta_bancaria_id=filtros['conta_bancaria_id'])
        
        if 'centro_custo_id' in filtros:
            query = query.filter_by(centro_custo_id=filtros['centro_custo_id'])
        
        # Ordenação
        if self.ordenacao:
            campo_ordem = getattr(LancamentoFinanceiro, self.ordenacao, None)
            if campo_ordem:
                if self.ordem_direcao == 'DESC':
                    query = query.order_by(campo_ordem.desc())
                else:
                    query = query.order_by(campo_ordem.asc())
        
        return query.all()
    
    def _executar_fluxo_caixa(self):
        """Executa relatório de fluxo de caixa."""
        # Implementação similar aos outros relatórios
        return []
    
    def _executar_dre(self):
        """Executa relatório de DRE."""
        return []
    
    def _executar_contas_pagar(self):
        """Executa relatório de contas a pagar."""
        return LancamentoFinanceiro.query.filter(
            LancamentoFinanceiro.tipo.in_(['despesa', 'conta_pagar']),
            LancamentoFinanceiro.ativo == True
        ).all()
    
    def _executar_contas_receber(self):
        """Executa relatório de contas a receber."""
        return LancamentoFinanceiro.query.filter(
            LancamentoFinanceiro.tipo.in_(['receita', 'conta_receber']),
            LancamentoFinanceiro.ativo == True
        ).all()
    
    def _executar_centros_custo(self):
        """Executa relatório de centros de custo."""
        return CentroCusto.query.filter_by(ativo=True).all()
    
    @classmethod
    def get_campos_disponiveis(cls, tipo):
        """
        Retorna campos disponíveis para um tipo de relatório.
        
        Args:
            tipo: Tipo do relatório
            
        Returns:
            list: Lista de dicts com campos
        """
        campos_lancamentos = [
            {'nome': 'data_lancamento', 'label': 'Data Lançamento', 'tipo': 'data'},
            {'nome': 'data_vencimento', 'label': 'Data Vencimento', 'tipo': 'data'},
            {'nome': 'descricao', 'label': 'Descrição', 'tipo': 'texto'},
            {'nome': 'tipo', 'label': 'Tipo', 'tipo': 'opcao'},
            {'nome': 'status', 'label': 'Status', 'tipo': 'opcao'},
            {'nome': 'valor', 'label': 'Valor', 'tipo': 'numero'},
            {'nome': 'categoria', 'label': 'Categoria', 'tipo': 'texto'},
            {'nome': 'numero_documento', 'label': 'Nº Documento', 'tipo': 'texto'},
            {'nome': 'forma_pagamento', 'label': 'Forma Pagamento', 'tipo': 'texto'},
        ]
        
        if tipo == 'LANCAMENTOS':
            return campos_lancamentos
        elif tipo == 'CONTAS_PAGAR' or tipo == 'CONTAS_RECEBER':
            return campos_lancamentos
        
        return []
    
    @classmethod
    def get_filtros_disponiveis(cls, tipo):
        """
        Retorna filtros disponíveis para um tipo de relatório.
        
        Args:
            tipo: Tipo do relatório
            
        Returns:
            list: Lista de dicts com filtros
        """
        filtros_lancamentos = [
            {'nome': 'tipo', 'label': 'Tipo', 'tipo': 'select'},
            {'nome': 'status', 'label': 'Status', 'tipo': 'select'},
            {'nome': 'categoria', 'label': 'Categoria', 'tipo': 'text'},
            {'nome': 'data_inicio', 'label': 'Data Início', 'tipo': 'date'},
            {'nome': 'data_fim', 'label': 'Data Fim', 'tipo': 'date'},
            {'nome': 'conta_bancaria_id', 'label': 'Conta Bancária', 'tipo': 'select'},
            {'nome': 'centro_custo_id', 'label': 'Centro de Custo', 'tipo': 'select'},
        ]
        
        if tipo in ['LANCAMENTOS', 'CONTAS_PAGAR', 'CONTAS_RECEBER']:
            return filtros_lancamentos
        
        return []
