# -*- coding: utf-8 -*-
"""
ERP JSP v3.0 - Model de Cliente
================================

Define a estrutura de dados para clientes.
Inclui validações e relacionamentos.

Autor: JSP Soluções
Data: 2025
"""

from app.extensoes import db
from app.models import BaseModel

class Cliente(BaseModel):
    """
    Model para representar clientes do sistema.
    
    Armazena informações completas dos clientes,
    incluindo dados pessoais e de contato.
    """
    __tablename__ = 'clientes'
    
    # Dados principais
    nome = db.Column(db.String(100), nullable=False, index=True)
    tipo = db.Column(db.String(20), nullable=False, default='PF')  # PF ou PJ
    
    # Documentos
    cpf_cnpj = db.Column(db.String(20), unique=True, index=True)
    rg_ie = db.Column(db.String(20))
    
    # Contato
    email = db.Column(db.String(120), index=True)
    telefone = db.Column(db.String(20))
    celular = db.Column(db.String(20))
    
    # Endereço
    cep = db.Column(db.String(10))
    endereco = db.Column(db.String(200))
    numero = db.Column(db.String(10))
    complemento = db.Column(db.String(50))
    bairro = db.Column(db.String(50))
    cidade = db.Column(db.String(50))
    estado = db.Column(db.String(2))
    
    # Observações
    observacoes = db.Column(db.Text)
    
    def __repr__(self):
        """Representação string do cliente."""
        return f'<Cliente {self.nome}>'
    
    @property
    def nome_display(self):
        """Nome formatado para exibição."""
        return self.nome.title() if self.nome else ''
    
    @property
    def documento_formatado(self):
        """Documento formatado (CPF/CNPJ)."""
        if not self.cpf_cnpj:
            return ''
        
        doc = ''.join(filter(str.isdigit, self.cpf_cnpj))
        
        if len(doc) == 11:  # CPF
            return f'{doc[:3]}.{doc[3:6]}.{doc[6:9]}-{doc[9:]}'
        elif len(doc) == 14:  # CNPJ
            return f'{doc[:2]}.{doc[2:5]}.{doc[5:8]}/{doc[8:12]}-{doc[12:]}'
        
        return self.cpf_cnpj
    
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
    
    @classmethod
    def buscar_por_documento(cls, documento):
        """
        Busca cliente por CPF/CNPJ.
        
        Args:
            documento (str): CPF ou CNPJ
            
        Returns:
            Cliente: Cliente encontrado ou None
        """
        doc_limpo = ''.join(filter(str.isdigit, documento))
        return cls.query.filter_by(cpf_cnpj=doc_limpo, ativo=True).first()
    
    @classmethod
    def buscar_por_nome(cls, nome):
        """
        Busca clientes por nome (busca parcial).
        
        Args:
            nome (str): Nome ou parte do nome
            
        Returns:
            list: Lista de clientes encontrados
        """
        return cls.query.filter(
            cls.nome.ilike(f'%{nome}%'),
            cls.ativo == True
        ).all()
    
    def validar_documento(self):
        """
        Valida CPF/CNPJ.
        
        Returns:
            bool: True se válido
        """
        if not self.cpf_cnpj:
            return True
        
        doc = ''.join(filter(str.isdigit, self.cpf_cnpj))
        
        if self.tipo == 'PF':
            return len(doc) == 11
        elif self.tipo == 'PJ':
            return len(doc) == 14
        
        return False