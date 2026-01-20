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
            origem='CUSTO_FIXO'
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
    lancamentos = db.relationship('LancamentoFinanceiro', 
                                  backref='plano_conta',
                                  foreign_keys='LancamentoFinanceiro.plano_conta_id')
    
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
