# -*- coding: utf-8 -*-
"""
ERP JSP v3.0 - Model de Notas Fiscais de Serviço (NFS-e)
========================================================

Model para gerenciamento de Notas Fiscais de Prestação de Serviços Eletrônicas.
Controla emissão, cancelamento e gerenciamento de NFS-e.

Autor: JSP Soluções
Data: 2026
"""

from datetime import datetime, date
from decimal import Decimal
from app.extensoes import db
from app.models import BaseModel


class NotaFiscalServico(BaseModel):
    """
    Model para Notas Fiscais de Prestação de Serviços (NFS-e).
    
    Armazena informações específicas para notas fiscais de serviços,
    incluindo RPS, ISS, retenções e dados do tomador/prestador.
    """
    
    __tablename__ = 'notas_fiscais_servico'
    __table_args__ = {'extend_existing': True}
    
    # Informações Básicas
    numero = db.Column(db.String(20), nullable=False, index=True)
    numero_rps = db.Column(db.String(20))  # Recibo Provisório de Serviços
    serie_rps = db.Column(db.String(10))
    data_emissao = db.Column(db.Date, nullable=False, index=True)
    
    # Competência (mês de referência)
    competencia = db.Column(db.Date, nullable=True)
    
    # Tipo
    tipo_nfse = db.Column(db.String(20), default='PRESTADOR')  # PRESTADOR ou TOMADOR
    status = db.Column(db.String(20), default='EMITIDA')  # EMITIDA, CANCELADA, SUBSTITUIDA
    
    # Prestador (Normalmente a empresa)
    prestador_nome = db.Column(db.String(200))
    prestador_cnpj = db.Column(db.String(18))
    prestador_im = db.Column(db.String(20))  # Inscrição Municipal
    prestador_endereco = db.Column(db.String(300))
    prestador_telefone = db.Column(db.String(20))
    prestador_email = db.Column(db.String(100))
    
    # Tomador (Cliente)
    tomador_nome = db.Column(db.String(200), nullable=False)
    tomador_cnpj_cpf = db.Column(db.String(18))
    tomador_im = db.Column(db.String(20))
    tomador_endereco = db.Column(db.String(300))
    tomador_telefone = db.Column(db.String(20))
    tomador_email = db.Column(db.String(100))
    
    # Serviços
    descricao_servico = db.Column(db.Text, nullable=False)
    codigo_servico = db.Column(db.String(10))  # Código de serviço LC 116/2003
    codigo_cnae = db.Column(db.String(10))
    local_prestacao = db.Column(db.String(200))  # Onde o serviço foi prestado
    
    # Valores
    valor_servicos = db.Column(db.Numeric(12, 2), nullable=False)
    valor_deducoes = db.Column(db.Numeric(12, 2), default=0)
    valor_base_calculo = db.Column(db.Numeric(12, 2))
    
    # ISS
    aliquota_iss = db.Column(db.Numeric(5, 2), default=0)  # Percentual
    valor_iss = db.Column(db.Numeric(12, 2), default=0)
    valor_iss_retido = db.Column(db.Numeric(12, 2), default=0)
    iss_retido = db.Column(db.Boolean, default=False)
    
    # Outras Retenções
    valor_pis = db.Column(db.Numeric(12, 2), default=0)
    valor_cofins = db.Column(db.Numeric(12, 2), default=0)
    valor_inss = db.Column(db.Numeric(12, 2), default=0)
    valor_ir = db.Column(db.Numeric(12, 2), default=0)
    valor_csll = db.Column(db.Numeric(12, 2), default=0)
    
    # Valores Líquidos
    valor_liquido = db.Column(db.Numeric(12, 2))
    valor_total_nota = db.Column(db.Numeric(12, 2), nullable=False)
    
    # Outras Informações
    natureza_operacao = db.Column(db.String(2))  # 1=Tributação no município...
    regime_especial_tributacao = db.Column(db.String(2))
    optante_simples = db.Column(db.Boolean, default=False)
    incentivo_fiscal = db.Column(db.Boolean, default=False)
    
    # Código de Verificação e Chave
    codigo_verificacao = db.Column(db.String(50))
    chave_acesso = db.Column(db.String(50))
    
    # Observações
    observacoes = db.Column(db.Text)
    informacoes_complementares = db.Column(db.Text)
    
    # Arquivos
    arquivo_pdf = db.Column(db.Text)  # Base64 ou caminho
    arquivo_xml = db.Column(db.Text)
    
    # Relacionamentos
    cliente_id = db.Column(db.Integer, db.ForeignKey('clientes.id'), nullable=True)
    ordem_servico_id = db.Column(db.Integer, db.ForeignKey('ordem_servico.id'), nullable=True)
    lancamento_id = db.Column(db.Integer, db.ForeignKey('lancamentos_financeiros.id'), nullable=True)
    
    # Relacionamentos
    cliente = db.relationship('Cliente', backref='notas_fiscais_servico', foreign_keys=[cliente_id])
    ordem_servico = db.relationship('OrdemServico', backref='notas_fiscais_servico', foreign_keys=[ordem_servico_id])
    lancamento = db.relationship('LancamentoFinanceiro', backref='nota_fiscal_servico', foreign_keys=[lancamento_id])
    
    def __repr__(self):
        return f'<NotaFiscalServico {self.numero} - R$ {self.valor_total_nota}>'
    
    @property
    def numero_completo(self):
        """Retorna número completo da nota."""
        if self.numero_rps:
            return f"NFS-e {self.numero} (RPS {self.numero_rps}/{self.serie_rps})"
        return f"NFS-e {self.numero}"
    
    @property
    def tipo_icone(self):
        """Retorna ícone baseado no tipo."""
        if self.status == 'CANCELADA':
            return 'fas fa-ban text-danger'
        elif self.status == 'SUBSTITUIDA':
            return 'fas fa-exchange-alt text-warning'
        return 'fas fa-file-invoice text-success'
    
    def calcular_valores(self):
        """
        Calcula automaticamente todos os valores da NFS-e.
        """
        # Base de cálculo = Valor dos serviços - Deduções
        self.valor_base_calculo = float(self.valor_servicos or 0) - float(self.valor_deducoes or 0)
        
        # ISS
        if self.aliquota_iss and self.valor_base_calculo:
            self.valor_iss = (float(self.valor_base_calculo) * float(self.aliquota_iss)) / 100
        
        # Valor líquido = Valor serviços - todas as retenções
        total_retencoes = float(self.valor_iss_retido or 0) + float(self.valor_pis or 0) + \
                         float(self.valor_cofins or 0) + float(self.valor_inss or 0) + \
                         float(self.valor_ir or 0) + float(self.valor_csll or 0)
        
        self.valor_liquido = float(self.valor_servicos or 0) - total_retencoes
        
        # Valor total da nota
        self.valor_total_nota = float(self.valor_servicos or 0)
    
    def gerar_lancamento_financeiro(self, conta_id=None):
        """
        Gera lançamento financeiro automaticamente a partir da NFS-e.
        
        Args:
            conta_id: ID da conta bancária (opcional)
            
        Returns:
            LancamentoFinanceiro: Lançamento criado
        """
        from app.financeiro.financeiro_model import LancamentoFinanceiro
        
        if self.lancamento_id:
            return None  # Já tem lançamento
        
        lancamento = LancamentoFinanceiro(
            descricao=f'NFS-e {self.numero} - {self.tomador_nome}',
            valor=self.valor_liquido or self.valor_total_nota,
            tipo='receita' if self.tipo_nfse == 'PRESTADOR' else 'despesa',
            status='pendente',
            data_lancamento=self.data_emissao,
            data_vencimento=self.data_emissao,
            categoria='Prestação de Serviços',
            subcategoria=self.codigo_servico or 'Serviços',
            cliente_id=self.cliente_id,
            observacoes=f'Gerado automaticamente da {self.numero_completo}'
        )
        
        if conta_id:
            lancamento.conta_id = conta_id
        
        db.session.add(lancamento)
        db.session.flush()
        
        self.lancamento_id = lancamento.id
        
        return lancamento
