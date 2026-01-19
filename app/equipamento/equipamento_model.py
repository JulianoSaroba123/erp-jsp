# -*- coding: utf-8 -*-
"""
ERP JSP v3.0 - Model de Equipamento
====================================

Define a estrutura de dados para equipamentos.
Inclui validações e relacionamentos com clientes.

Autor: JSP Soluções
Data: 2026
"""

from app.extensoes import db
from app.models import BaseModel


class Equipamento(BaseModel):
    """
    Model para representar equipamentos dos clientes.
    
    Armazena informações de equipamentos que recebem manutenção/serviços,
    permitindo histórico completo e reutilização de dados.
    
    ✨ Evita retrabalho ao cadastrar equipamentos em múltiplas OS
    """
    __tablename__ = 'equipamentos'
    
    # === DADOS PRINCIPAIS ===
    nome = db.Column(db.String(200), nullable=False, index=True)
    descricao = db.Column(db.Text)
    
    # === IDENTIFICAÇÃO DO EQUIPAMENTO ===
    marca = db.Column(db.String(100))
    modelo = db.Column(db.String(100))
    numero_serie = db.Column(db.String(100), index=True)
    
    # === RELACIONAMENTO COM CLIENTE ===
    cliente_id = db.Column(db.Integer, db.ForeignKey('clientes.id'), nullable=False)
    cliente = db.relationship('Cliente', backref='equipamentos')
    
    # === INFORMAÇÕES ADICIONAIS ===
    tipo = db.Column(db.String(100))  # Ex: Calandra, Prensa, Máquina Industrial, etc.
    localizacao = db.Column(db.String(200))  # Onde está instalado
    ano_fabricacao = db.Column(db.Integer)
    
    # === DADOS TÉCNICOS ===
    capacidade = db.Column(db.String(100))  # Ex: "500kg", "2000W", etc.
    tensao = db.Column(db.String(50))  # Ex: "220V", "380V Trifásico"
    potencia = db.Column(db.String(50))  # Ex: "15kW", "3cv"
    
    # === OBSERVAÇÕES ===
    observacoes = db.Column(db.Text)
    
    # === STATUS ===
    ativo = db.Column(db.Boolean, default=True, nullable=False)
    
    def __repr__(self):
        """Representação string do equipamento."""
        return f'<Equipamento {self.nome} - {self.marca or "S/Marca"} {self.modelo or ""}>'
    
    def to_dict(self):
        """
        Converte o equipamento para dicionário.
        
        Returns:
            dict: Dados do equipamento
        """
        return {
            'id': self.id,
            'nome': self.nome,
            'descricao': self.descricao,
            'marca': self.marca,
            'modelo': self.modelo,
            'numero_serie': self.numero_serie,
            'tipo': self.tipo,
            'cliente_id': self.cliente_id,
            'cliente_nome': self.cliente.nome if self.cliente else None,
            'localizacao': self.localizacao,
            'ano_fabricacao': self.ano_fabricacao,
            'capacidade': self.capacidade,
            'tensao': self.tensao,
            'potencia': self.potencia,
            'observacoes': self.observacoes,
            'ativo': self.ativo,
            'criado_em': self.criado_em.strftime('%d/%m/%Y %H:%M') if self.criado_em else None,
            'atualizado_em': self.atualizado_em.strftime('%d/%m/%Y %H:%M') if self.atualizado_em else None,
        }
    
    @property
    def nome_completo(self):
        """
        Retorna nome completo do equipamento (nome + marca + modelo).
        
        Returns:
            str: Nome formatado do equipamento
        """
        partes = [self.nome]
        if self.marca:
            partes.append(self.marca)
        if self.modelo:
            partes.append(self.modelo)
        return ' - '.join(partes)
    
    @staticmethod
    def buscar_por_cliente(cliente_id, apenas_ativos=True):
        """
        Busca equipamentos de um cliente específico.
        
        Args:
            cliente_id (int): ID do cliente
            apenas_ativos (bool): Se True, retorna apenas equipamentos ativos
            
        Returns:
            list: Lista de equipamentos
        """
        query = Equipamento.query.filter_by(cliente_id=cliente_id)
        
        if apenas_ativos:
            query = query.filter_by(ativo=True)
        
        return query.order_by(Equipamento.nome).all()
