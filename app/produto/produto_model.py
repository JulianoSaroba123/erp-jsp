# -*- coding: utf-8 -*-
"""
ERP JSP v3.0 - Model de Produto
================================

Define a estrutura de dados para produtos.
Inclui controle de estoque e preços.

Autor: JSP Soluções
Data: 2025
"""

from app.extensoes import db
from app.models import BaseModel
from decimal import Decimal

class Produto(BaseModel):
    """
    Model para representar produtos do sistema.
    
    Armazena informações completas dos produtos,
    incluindo controle de estoque e preços.
    """
    __tablename__ = 'produtos'
    
    # Dados principais
    nome = db.Column(db.String(100), nullable=False, index=True)
    descricao = db.Column(db.Text)
    codigo = db.Column(db.String(50), unique=True, index=True)
    codigo_barras = db.Column(db.String(50), unique=True, index=True)
    
    # Categoria e classificação
    categoria = db.Column(db.String(50), index=True)
    subcategoria = db.Column(db.String(50))
    marca = db.Column(db.String(50))
    modelo = db.Column(db.String(50))
    
    # Unidades
    unidade_medida = db.Column(db.String(10), default='UN')  # UN, KG, M, L, etc.
    peso = db.Column(db.Numeric(10, 3))
    dimensoes = db.Column(db.String(50))  # Ex: 10x20x30 cm
    
    # Preços
    preco_custo = db.Column(db.Numeric(10, 2), default=0)
    preco_venda = db.Column(db.Numeric(10, 2), default=0)
    margem_lucro = db.Column(db.Numeric(5, 2), default=0)  # Percentual
    markup = db.Column(db.Numeric(5, 2), default=0)  # Percentual de markup sobre o custo
    
    # Estoque
    estoque_atual = db.Column(db.Integer, default=0)
    estoque_minimo = db.Column(db.Integer, default=0)
    estoque_maximo = db.Column(db.Integer, default=0)
    controla_estoque = db.Column(db.Boolean, default=True)
    
    # Fornecedor principal (FK opcional - pode não existir no início)
    fornecedor_id = db.Column(db.Integer, nullable=True)
    # FK removida temporariamente para evitar erro 500 se tabela fornecedores não existe
    # TODO: Adicionar FK após garantir que tabela fornecedores existe:
    # db.ForeignKey('fornecedores.id')
    
    # Status
    status = db.Column(db.String(20), default='ativo')  # ativo, inativo, descontinuado
    
    # Observações
    observacoes = db.Column(db.Text)
    
    def __repr__(self):
        """Representação string do produto."""
        return f'<Produto {self.nome}>'
    
    @property
    def nome_display(self):
        """Nome formatado para exibição."""
        return self.nome.title() if self.nome else ''
    
    @property
    def codigo_display(self):
        """Código formatado para exibição."""
        return self.codigo or f'P{self.id:06d}'
    
    @property
    def preco_custo_formatado(self):
        """Preço de custo formatado."""
        if self.preco_custo:
            return f'R$ {float(self.preco_custo):.2f}'.replace('.', ',')
        return 'R$ 0,00'
    
    @property
    def preco_venda_formatado(self):
        """Preço de venda formatado."""
        if self.preco_venda:
            return f'R$ {float(self.preco_venda):.2f}'.replace('.', ',')
        return 'R$ 0,00'
    
    @property
    def margem_lucro_calculada(self):
        """Calcula a margem de lucro baseada nos preços."""
        if self.preco_custo and self.preco_venda and self.preco_custo > 0:
            custo = float(self.preco_custo)
            venda = float(self.preco_venda)
            margem = ((venda - custo) / custo) * 100
            return round(margem, 2)
        return 0
    
    @property
    def markup_formatado(self):
        """Markup formatado para exibição."""
        if self.markup:
            return f'{float(self.markup):.2f}%'.replace('.', ',')
        return '0,00%'
    
    def calcular_preco_venda_por_markup(self):
        """Calcula o preço de venda baseado no markup sobre o custo."""
        if self.preco_custo and self.markup:
            custo = float(self.preco_custo)
            markup_percent = float(self.markup)
            preco_venda = custo * (1 + markup_percent / 100)
            return round(preco_venda, 2)
        return 0
    
    def calcular_markup_por_preco_venda(self):
        """Calcula o markup baseado nos preços de custo e venda."""
        if self.preco_custo and self.preco_venda and self.preco_custo > 0:
            custo = float(self.preco_custo)
            venda = float(self.preco_venda)
            markup = ((venda - custo) / custo) * 100
            return round(markup, 2)
        return 0
    
    @property
    def situacao_estoque(self):
        """Retorna a situação do estoque (baixo, normal, alto)."""
        if not self.controla_estoque:
            return 'sem_controle'
        
        if self.estoque_atual <= self.estoque_minimo:
            return 'baixo'
        elif self.estoque_atual >= self.estoque_maximo:
            return 'alto'
        else:
            return 'normal'
    
    @property
    def valor_estoque(self):
        """Valor total do estoque (custo * quantidade)."""
        if self.preco_custo and self.estoque_atual:
            return float(self.preco_custo) * self.estoque_atual
        return 0
    
    @classmethod
    def buscar_por_codigo(cls, codigo):
        """
        Busca produto por código.
        
        Args:
            codigo (str): Código do produto
            
        Returns:
            Produto: Produto encontrado ou None
        """
        return cls.query.filter_by(codigo=codigo, ativo=True).first()
    
    @classmethod
    def buscar_por_codigo_barras(cls, codigo_barras):
        """
        Busca produto por código de barras.
        
        Args:
            codigo_barras (str): Código de barras
            
        Returns:
            Produto: Produto encontrado ou None
        """
        return cls.query.filter_by(codigo_barras=codigo_barras, ativo=True).first()
    
    @classmethod
    def buscar_por_nome(cls, nome):
        """
        Busca produtos por nome (busca parcial).
        
        Args:
            nome (str): Nome ou parte do nome
            
        Returns:
            list: Lista de produtos encontrados
        """
        return cls.query.filter(
            cls.nome.ilike(f'%{nome}%'),
            cls.ativo == True
        ).all()
    
    @classmethod
    def buscar_por_categoria(cls, categoria):
        """
        Busca produtos por categoria.
        
        Args:
            categoria (str): Categoria do produto
            
        Returns:
            list: Lista de produtos da categoria
        """
        return cls.query.filter_by(categoria=categoria, ativo=True).all()
    
    @classmethod
    def produtos_estoque_baixo(cls):
        """
        Retorna produtos com estoque baixo.
        
        Returns:
            list: Lista de produtos com estoque <= mínimo
        """
        return cls.query.filter(
            cls.controla_estoque == True,
            cls.estoque_atual <= cls.estoque_minimo,
            cls.ativo == True
        ).all()
    
    def atualizar_estoque(self, quantidade, operacao='entrada'):
        """
        Atualiza o estoque do produto.
        
        Args:
            quantidade (int): Quantidade a ser movimentada
            operacao (str): 'entrada' ou 'saida'
            
        Returns:
            bool: True se atualizado com sucesso
        """
        if not self.controla_estoque:
            return True
        
        if operacao == 'entrada':
            self.estoque_atual += quantidade
        elif operacao == 'saida':
            if self.estoque_atual >= quantidade:
                self.estoque_atual -= quantidade
            else:
                return False  # Estoque insuficiente
        
        return True
    
    def calcular_preco_venda(self, margem_percentual):
        """
        Calcula o preço de venda baseado no custo e margem.
        
        Args:
            margem_percentual (float): Margem de lucro em %
        """
        if self.preco_custo:
            custo = float(self.preco_custo)
            self.preco_venda = Decimal(custo * (1 + margem_percentual / 100))
            self.margem_lucro = Decimal(margem_percentual)