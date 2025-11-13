# -*- coding: utf-8 -*-
"""
ERP JSP v3.0 - Model de Fornecedor
===================================

Define a estrutura de dados para fornecedores.
Inclui validações e relacionamentos.

Autor: JSP Soluções
Data: 2025
"""

from app.extensoes import db
from app.models import BaseModel

class Fornecedor(BaseModel):
    """
    Model para representar fornecedores do sistema.
    
    Armazena informações completas dos fornecedores,
    incluindo dados empresariais e de contato.
    """
    __tablename__ = 'fornecedores'
    
    # Dados principais
    nome = db.Column(db.String(150), nullable=False, index=True)
    nome_fantasia = db.Column(db.String(150))
    tipo = db.Column(db.String(20), nullable=False, default='PJ')  # PJ ou PF
    
    # Documentos
    cnpj_cpf = db.Column(db.String(20), unique=True, index=True)  # Campo principal de documento
    rg_ie = db.Column(db.String(20))  # RG para PF ou IE para PJ
    inscricao_estadual = db.Column(db.String(20))
    inscricao_municipal = db.Column(db.String(20))
    im = db.Column(db.String(20))  # Inscrição Municipal
    
    # Contato
    email = db.Column(db.String(150), index=True)
    email_financeiro = db.Column(db.String(150))  # Email separado para financeiro
    telefone = db.Column(db.String(20))
    celular = db.Column(db.String(20))
    whatsapp = db.Column(db.String(20))  # WhatsApp
    site = db.Column(db.String(200))
    website = db.Column(db.String(200))  # Compatibilidade
    
    # Contato comercial
    contato_nome = db.Column(db.String(100))
    contato_cargo = db.Column(db.String(100))
    contato_email = db.Column(db.String(150))
    contato_telefone = db.Column(db.String(20))
    
    # Endereço
    cep = db.Column(db.String(10))
    endereco = db.Column(db.String(200))
    numero = db.Column(db.String(20))
    complemento = db.Column(db.String(100))
    bairro = db.Column(db.String(100))
    cidade = db.Column(db.String(100))
    estado = db.Column(db.String(2))
    pais = db.Column(db.String(50), default='Brasil')
    
    # Dados comerciais e segmentação
    segmento = db.Column(db.String(100))  # Segmento de atuação
    porte_empresa = db.Column(db.String(20))  # Micro, Pequena, Média, Grande
    origem = db.Column(db.String(50))  # Como conheceu a empresa
    classificacao = db.Column(db.String(20))  # A, B, C, Premium, etc.
    categoria = db.Column(db.String(50))  # Ex: Equipamentos, Serviços, Matéria-prima
    condicoes_pagamento = db.Column(db.String(100))
    prazo_entrega = db.Column(db.String(50))
    
    # Configurações financeiras
    limite_credito = db.Column(db.Numeric(10, 2))
    prazo_pagamento_padrao = db.Column(db.Integer)
    desconto_padrao = db.Column(db.Numeric(5, 2))
    
    # Datas importantes
    data_nascimento = db.Column(db.Date)  # Para pessoa física
    data_fundacao = db.Column(db.Date)  # Para pessoa jurídica
    
    # Dados pessoais (PF)
    genero = db.Column(db.String(20))  # Masculino, Feminino, Outros
    estado_civil = db.Column(db.String(20))  # Solteiro, Casado, etc.
    profissao = db.Column(db.String(100))  # Profissão (para PF)
    
    # Campos específicos para fornecedores
    forma_entrega = db.Column(db.String(50))  # Própria, Transportadora, etc.
    tempo_entrega_medio = db.Column(db.Integer)  # Dias médios de entrega
    certificacoes = db.Column(db.Text)  # ISO, certificações especiais
    categoria_fiscal = db.Column(db.String(20))  # Simples, Normal, MEI, etc.
    
    # Dados bancários
    banco_principal = db.Column(db.String(100))
    agencia = db.Column(db.String(20))
    conta = db.Column(db.String(30))
    pix = db.Column(db.String(100))
    
    # Gestão interna
    observacoes = db.Column(db.Text)
    observacoes_internas = db.Column(db.Text)
    status = db.Column(db.String(20), default='Ativo')
    motivo_bloqueio = db.Column(db.String(200))
    
    def __repr__(self):
        """Representação string do fornecedor."""
        return f'<Fornecedor {self.nome}>'
    
    @property
    def cpf_cnpj_display(self):
        """Compatibilidade: retorna cnpj_cpf."""
        return self.cnpj_cpf
    
    @property
    def nome_display(self):
        """Nome formatado para exibição."""
        if self.nome_fantasia and self.nome_fantasia != self.nome:
            return f"{self.nome_fantasia} ({self.nome})"
        return self.nome.title() if self.nome else ''
    
    @property
    def documento_formatado(self):
        """Documento formatado (CNPJ/CPF)."""
        documento = self.cnpj_cpf
        if not documento:
            return ''
        
        doc = ''.join(filter(str.isdigit, documento))
        
        if len(doc) == 14:  # CNPJ
            return f'{doc[:2]}.{doc[2:5]}.{doc[5:8]}/{doc[8:12]}-{doc[12:]}'
        elif len(doc) == 11:  # CPF
            return f'{doc[:3]}.{doc[3:6]}.{doc[6:9]}-{doc[9:]}'
        
        return documento
    
    @property
    def endereco_completo(self):
        """Endereço completo formatado."""
        partes = []
        
        if self.endereco:
            endereco_base = self.endereco
            if self.numero:
                endereco_base += f', {self.numero}'
            if self.complemento:
                endereco_base += f' - {self.complemento}'
            partes.append(endereco_base)
        
        if self.bairro:
            partes.append(self.bairro)
        
        if self.cidade and self.estado:
            partes.append(f'{self.cidade}/{self.estado}')
        elif self.cidade:
            partes.append(self.cidade)
        
        if self.cep:
            partes.append(f'CEP: {self.cep}')
        
        return ' - '.join(partes) if partes else ''
    
    @property
    def contato_principal(self):
        """Retorna o contato principal formatado."""
        if self.contato_nome:
            contato = self.contato_nome
            if self.contato_cargo:
                contato += f' ({self.contato_cargo})'
            return contato
        return None
    
    @classmethod
    def buscar_por_documento(cls, documento):
        """
        Busca fornecedor por CNPJ/CPF.
        
        Args:
            documento (str): CNPJ ou CPF
            
        Returns:
            Fornecedor: Fornecedor encontrado ou None
        """
        doc_limpo = ''.join(filter(str.isdigit, documento))
        return cls.query.filter(
            cls.cnpj_cpf == doc_limpo,
            cls.ativo == True
        ).first()
    
    @classmethod
    def buscar_por_nome(cls, nome):
        """
        Busca fornecedores por nome (busca parcial).
        
        Args:
            nome (str): Nome ou parte do nome
            
        Returns:
            list: Lista de fornecedores encontrados
        """
        return cls.query.filter(
            db.or_(
                cls.nome.ilike(f'%{nome}%'),
                cls.nome_fantasia.ilike(f'%{nome}%')
            ),
            cls.ativo == True
        ).all()
    
    @classmethod
    def buscar_por_categoria(cls, categoria):
        """
        Busca fornecedores por categoria.
        
        Args:
            categoria (str): Categoria do fornecedor
            
        Returns:
            list: Lista de fornecedores da categoria
        """
        return cls.query.filter_by(categoria=categoria, ativo=True).all()
    
    def validar_documento(self):
        """
        Valida CNPJ/CPF.
        
        Returns:
            bool: True se válido
        """
        documento = self.cnpj_cpf
        if not documento:
            return True
        
        doc = ''.join(filter(str.isdigit, documento))
        
        if self.tipo == 'PJ':
            return len(doc) == 14
        elif self.tipo == 'PF':
            return len(doc) == 11
        
        return False
    
    @classmethod
    def buscar_ativos(cls):
        """Busca todos os fornecedores ativos."""
        return cls.query.filter_by(ativo=True).order_by(cls.nome).all()
    
    @classmethod
    def buscar_por_classificacao(cls, classificacao):
        """Busca fornecedores por classificação."""
        return cls.query.filter_by(classificacao=classificacao, ativo=True).all()
    
    @property
    def nome_completo(self):
        """Nome completo para exibição."""
        if self.nome_fantasia and self.nome_fantasia != self.nome:
            return f"{self.nome_fantasia} ({self.nome})"
        return self.nome
    
    @property
    def is_pessoa_juridica(self):
        """Verifica se é pessoa jurídica."""
        return self.tipo == 'PJ'
    
    @property
    def is_pessoa_fisica(self):
        """Verifica se é pessoa física."""
        return self.tipo == 'PF'