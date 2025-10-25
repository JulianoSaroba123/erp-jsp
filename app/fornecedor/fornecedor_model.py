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
    nome = db.Column(db.String(100), nullable=False, index=True)
    nome_fantasia = db.Column(db.String(100))
    tipo = db.Column(db.String(20), nullable=False, default='PJ')  # PJ ou PF
    
    # Documentos
    cnpj_cpf = db.Column(db.String(20), unique=True, index=True)
    inscricao_estadual = db.Column(db.String(20))
    inscricao_municipal = db.Column(db.String(20))
    
    # Contato
    email = db.Column(db.String(120), index=True)
    telefone = db.Column(db.String(20))
    celular = db.Column(db.String(20))
    site = db.Column(db.String(200))
    
    # Contato comercial
    contato_nome = db.Column(db.String(100))
    contato_cargo = db.Column(db.String(50))
    contato_email = db.Column(db.String(120))
    contato_telefone = db.Column(db.String(20))
    
    # Endereço
    cep = db.Column(db.String(10))
    endereco = db.Column(db.String(200))
    numero = db.Column(db.String(10))
    complemento = db.Column(db.String(50))
    bairro = db.Column(db.String(50))
    cidade = db.Column(db.String(50))
    estado = db.Column(db.String(2))
    
    # Dados comerciais
    categoria = db.Column(db.String(50))  # Ex: Equipamentos, Serviços, Matéria-prima
    condicoes_pagamento = db.Column(db.String(100))
    prazo_entrega = db.Column(db.String(50))
    
    # Observações
    observacoes = db.Column(db.Text)
    
    def __repr__(self):
        """Representação string do fornecedor."""
        return f'<Fornecedor {self.nome}>'
    
    @property
    def nome_display(self):
        """Nome formatado para exibição."""
        if self.nome_fantasia and self.nome_fantasia != self.nome:
            return f"{self.nome_fantasia} ({self.nome})"
        return self.nome.title() if self.nome else ''
    
    @property
    def documento_formatado(self):
        """Documento formatado (CNPJ/CPF)."""
        if not self.cnpj_cpf:
            return ''
        
        doc = ''.join(filter(str.isdigit, self.cnpj_cpf))
        
        if len(doc) == 14:  # CNPJ
            return f'{doc[:2]}.{doc[2:5]}.{doc[5:8]}/{doc[8:12]}-{doc[12:]}'
        elif len(doc) == 11:  # CPF
            return f'{doc[:3]}.{doc[3:6]}.{doc[6:9]}-{doc[9:]}'
        
        return self.cnpj_cpf
    
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
        return cls.query.filter_by(cnpj_cpf=doc_limpo, ativo=True).first()
    
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
        if not self.cnpj_cpf:
            return True
        
        doc = ''.join(filter(str.isdigit, self.cnpj_cpf))
        
        if self.tipo == 'PJ':
            return len(doc) == 14
        elif self.tipo == 'PF':
            return len(doc) == 11
        
        return False