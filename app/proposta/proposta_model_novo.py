# -*- coding: utf-8 -*-
"""
ERP JSP v3.0 - Model de Proposta Comercial
==========================================

Model para gerenciamento de propostas comerciais.
Baseado na estrutura de Ordem de Serviço.

Autor: JSP Soluções
Data: 2025
"""

from app.extensoes import db
from app.models import BaseModel
from decimal import Decimal
from datetime import datetime, date
from sqlalchemy import func


class Proposta(BaseModel):
    """
    Model para Proposta Comercial.
    
    Gerencia propostas comerciais com produtos e serviços separados.
    """
    
    __tablename__ = 'proposta'
    
    # Campos básicos
    codigo = db.Column(db.String(20), unique=True, nullable=False, index=True)
    
    # Cliente
    cliente_id = db.Column(db.Integer, db.ForeignKey('clientes.id'), nullable=False)
    cliente = db.relationship('Cliente', backref='propostas')
    
    # Dados da proposta
    titulo = db.Column(db.String(200), nullable=False)
    descricao = db.Column(db.Text)
    observacoes = db.Column(db.Text)
    
    # Status da proposta
    status = db.Column(db.String(20), default='pendente', nullable=False)
    # Possíveis status: pendente, enviada, aprovada, rejeitada, cancelada
    
    # Datas
    data_emissao = db.Column(db.Date, default=date.today, nullable=False)
    validade = db.Column(db.Integer, default=30)  # dias de validade
    data_validade = db.Column(db.Date)  # calculado automaticamente
    data_aprovacao = db.Column(db.DateTime)
    
    # Responsável
    vendedor = db.Column(db.String(100))
    
    # Valores
    valor_produtos = db.Column(db.Numeric(10, 2), default=0.00)
    valor_servicos = db.Column(db.Numeric(10, 2), default=0.00)
    desconto = db.Column(db.Numeric(5, 2), default=0.00)  # percentual
    valor_total = db.Column(db.Numeric(10, 2), default=0.00)
    
    # Condições
    condicoes_pagamento = db.Column(db.Text)
    prazo_execucao = db.Column(db.String(100))
    garantia = db.Column(db.String(100))
    forma_pagamento = db.Column(db.String(50), default='a_vista')
    
    # Meta campos herdados de BaseModel:
    # id, data_criacao, data_atualizacao, ativo, usuario_criacao, usuario_atualizacao
    
    def __repr__(self):
        return f'<Proposta {self.codigo}: {self.titulo}>'
    
    def __str__(self):
        return f'Proposta {self.codigo} - {self.titulo}'
    
    @property
    def status_formatado(self):
        """Retorna status formatado para exibição."""
        status_map = {
            'pendente': 'Pendente',
            'enviada': 'Enviada',
            'aprovada': 'Aprovada',
            'rejeitada': 'Rejeitada',
            'cancelada': 'Cancelada'
        }
        return status_map.get(self.status, self.status.title())
    
    @property
    def status_cor(self):
        """Retorna cor do status para exibição."""
        cores = {
            'pendente': 'warning',
            'enviada': 'info',
            'aprovada': 'success',
            'rejeitada': 'danger',
            'cancelada': 'secondary'
        }
        return cores.get(self.status, 'secondary')
    
    @property
    def valor_total_produtos_calculado(self):
        """Calcula valor total dos produtos."""
        return sum(item.valor_total for item in self.itens_produto if item.ativo)
    
    @property
    def valor_total_servicos_calculado(self):
        """Calcula valor total dos serviços."""
        return sum(item.valor_total for item in self.itens_servico if item.ativo)
    
    @property
    def valor_total_calculado(self):
        """Calcula valor total (produtos + serviços - desconto)."""
        produtos = Decimal(str(self.valor_total_produtos_calculado or 0))
        servicos = Decimal(str(self.valor_total_servicos_calculado or 0))
        subtotal = produtos + servicos
        desconto_valor = subtotal * (Decimal(str(self.desconto or 0)) / 100)
        return float(subtotal - desconto_valor)
    
    @property
    def valida_ate(self):
        """Retorna a data de validade calculada."""
        if self.data_emissao and self.validade:
            from datetime import timedelta
            return self.data_emissao + timedelta(days=self.validade)
        return None
    
    @property
    def proposta_vencida(self):
        """Verifica se a proposta está vencida."""
        if not self.valida_ate or self.status in ['aprovada', 'rejeitada', 'cancelada']:
            return False
        return date.today() > self.valida_ate
    
    @classmethod
    def gerar_proximo_codigo(cls):
        """Gera o próximo código de proposta."""
        ano_atual = date.today().year
        prefixo = f"PROP{ano_atual}"
        
        # Busca o último código do ano
        ultima_proposta = cls.query.filter(
            cls.codigo.like(f"{prefixo}%")
        ).order_by(cls.codigo.desc()).first()
        
        if ultima_proposta:
            try:
                ultimo_num = int(ultima_proposta.codigo.replace(prefixo, ""))
                proximo_num = ultimo_num + 1
            except ValueError:
                proximo_num = 1
        else:
            proximo_num = 1
        
        return f"{prefixo}{proximo_num:04d}"
    
    @classmethod
    def buscar_por_codigo(cls, codigo):
        """Busca proposta por código."""
        return cls.query.filter_by(codigo=codigo, ativo=True).first()
    
    @classmethod
    def buscar_por_cliente(cls, cliente_id):
        """Busca propostas de um cliente."""
        return cls.query.filter_by(cliente_id=cliente_id, ativo=True).all()
    
    @classmethod
    def listar_por_status(cls, status):
        """Lista propostas por status."""
        return cls.query.filter_by(status=status, ativo=True).all()
    
    def aprovar(self):
        """Marca a proposta como aprovada."""
        if self.status == 'pendente' or self.status == 'enviada':
            self.status = 'aprovada'
            self.data_aprovacao = datetime.now()
            self.save()
    
    def rejeitar(self):
        """Marca a proposta como rejeitada."""
        if self.status in ['pendente', 'enviada']:
            self.status = 'rejeitada'
            self.save()
    
    def cancelar(self):
        """Cancela a proposta."""
        if self.status != 'aprovada':
            self.status = 'cancelada'
            self.save()
    
    def calcular_totais(self):
        """Calcula e atualiza todos os valores."""
        self.valor_produtos = self.valor_total_produtos_calculado
        self.valor_servicos = self.valor_total_servicos_calculado
        self.valor_total = self.valor_total_calculado
        self.save()


class PropostaProduto(BaseModel):
    """
    Model para produtos da proposta.
    
    Representa cada produto incluído na proposta comercial.
    """
    
    __tablename__ = 'proposta_produto'
    
    # Relacionamento com proposta
    proposta_id = db.Column(db.Integer, db.ForeignKey('proposta.id'), nullable=False)
    proposta = db.relationship('Proposta', backref='itens_produto')
    
    # Relacionamento com produto (opcional)
    produto_id = db.Column(db.Integer, db.ForeignKey('produtos.id'), nullable=True)
    produto = db.relationship('Produto', backref='propostas')
    
    # Dados do produto
    descricao = db.Column(db.String(500), nullable=False)
    quantidade = db.Column(db.Numeric(10, 3), default=1.000)
    valor_unitario = db.Column(db.Numeric(10, 2), default=0.00)
    valor_total = db.Column(db.Numeric(10, 2), default=0.00)
    
    def __repr__(self):
        return f'<PropostaProduto {self.descricao}: {self.quantidade}x>'
    
    def calcular_total(self):
        """Calcula valor total do produto."""
        if self.quantidade and self.valor_unitario:
            self.valor_total = float(Decimal(str(self.quantidade)) * Decimal(str(self.valor_unitario)))
        else:
            self.valor_total = 0.00


class PropostaServico(BaseModel):
    """
    Model para serviços da proposta.
    
    Representa cada serviço incluído na proposta comercial.
    """
    
    __tablename__ = 'proposta_servico'
    
    # Relacionamento com proposta
    proposta_id = db.Column(db.Integer, db.ForeignKey('proposta.id'), nullable=False)
    proposta = db.relationship('Proposta', backref='itens_servico')
    
    # Dados do serviço
    descricao = db.Column(db.String(500), nullable=False)
    quantidade = db.Column(db.Numeric(10, 3), default=1.000)
    valor_unitario = db.Column(db.Numeric(10, 2), default=0.00)
    valor_total = db.Column(db.Numeric(10, 2), default=0.00)
    
    def __repr__(self):
        return f'<PropostaServico {self.descricao}: {self.quantidade}x>'
    
    def calcular_total(self):
        """Calcula valor total do serviço."""
        if self.quantidade and self.valor_unitario:
            self.valor_total = float(Decimal(str(self.quantidade)) * Decimal(str(self.valor_unitario)))
        else:
            self.valor_total = 0.00


class PropostaParcela(BaseModel):
    """
    Model para parcelas da proposta.
    
    Quando a proposta é parcelada, cada parcela tem sua data
    de vencimento e valor.
    """
    
    __tablename__ = 'proposta_parcela'
    
    # Relacionamento com proposta
    proposta_id = db.Column(db.Integer, db.ForeignKey('proposta.id'), nullable=False)
    proposta = db.relationship('Proposta', backref='parcelas')
    
    # Dados da parcela
    numero_parcela = db.Column(db.Integer, nullable=False)
    data_vencimento = db.Column(db.Date, nullable=False)
    valor = db.Column(db.Numeric(10, 2), nullable=False)
    pago = db.Column(db.Boolean, default=False)
    data_pagamento = db.Column(db.Date)
    
    def __repr__(self):
        return f'<PropostaParcela {self.numero_parcela}: R$ {self.valor}>'
    
    @property
    def status_parcela(self):
        """Retorna status da parcela."""
        if self.pago:
            return 'paga'
        elif self.data_vencimento < date.today():
            return 'vencida'
        else:
            return 'pendente'


class PropostaAnexo(BaseModel):
    """
    Model para anexos da proposta.
    
    Armazena informações sobre arquivos anexados à proposta.
    """
    
    __tablename__ = 'proposta_anexo'
    
    # Relacionamento com proposta
    proposta_id = db.Column(db.Integer, db.ForeignKey('proposta.id'), nullable=False)
    proposta = db.relationship('Proposta', backref='anexos')
    
    # Dados do arquivo
    nome_original = db.Column(db.String(255), nullable=False)
    nome_arquivo = db.Column(db.String(255), nullable=False)
    tipo_arquivo = db.Column(db.String(50), nullable=False)
    mime_type = db.Column(db.String(100))
    tamanho = db.Column(db.Integer)
    caminho = db.Column(db.String(500), nullable=False)
    
    def __repr__(self):
        return f'<PropostaAnexo {self.nome_original}>'
