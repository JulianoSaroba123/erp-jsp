# -*- coding: utf-8 -*-
"""
Modelo de Kit Fotovoltaico do Distribuidor
==========================================

Armazena kits sincronizados da API do distribuidor.

Autor: JSP Soluções
Data: 2026
"""

from app.extensoes import db
from datetime import datetime


class KitFotovoltaico(db.Model):
    """Modelo para armazenar kits fotovoltaicos do distribuidor."""
    
    __tablename__ = 'kits_fotovoltaicos'
    
    # Identificação
    id = db.Column(db.Integer, primary_key=True)
    kit_id_api = db.Column(db.String(100), unique=True, nullable=False, index=True)  # ID na API do distribuidor
    
    # Informações básicas
    nome = db.Column(db.String(200), nullable=False)
    descricao = db.Column(db.Text)
    codigo = db.Column(db.String(50))  # Código/SKU do kit
    
    # Características técnicas
    potencia = db.Column(db.Float)  # Potência em kWp
    potencia_modulo = db.Column(db.Float)  # Potência individual do módulo em W
    quantidade_modulos = db.Column(db.Integer)  # Quantidade de módulos no kit
    fabricante_modulo = db.Column(db.String(100))  # Fabricante dos módulos
    modelo_modulo = db.Column(db.String(100))  # Modelo dos módulos
    
    # Inversor
    potencia_inversor = db.Column(db.Float)  # Potência do inversor em kW
    fabricante_inversor = db.Column(db.String(100))
    modelo_inversor = db.Column(db.String(100))
    tipo_inversor = db.Column(db.String(50))  # String, Microinversor, Híbrido, etc.
    
    # Precificação
    preco = db.Column(db.Numeric(12, 2))  # Preço do kit
    moeda = db.Column(db.String(3), default='BRL')  # BRL, USD, etc.
    disponivel = db.Column(db.Boolean, default=True)  # Se está disponível para venda
    estoque = db.Column(db.Integer)  # Quantidade em estoque (se a API fornecer)
    
    # Classificação
    categoria = db.Column(db.String(50))  # Residencial, Comercial, Industrial
    tipo = db.Column(db.String(50))  # On-Grid, Off-Grid, Híbrido
    
    # Informações adicionais
    garantia_modulo = db.Column(db.Integer)  # Garantia em anos
    garantia_inversor = db.Column(db.Integer)  # Garantia em anos
    eficiencia = db.Column(db.Float)  # Eficiência do sistema
    area_necessaria = db.Column(db.Float)  # Área necessária em m²
    
    # Dados da API (JSON bruto)
    dados_completos_api = db.Column(db.JSON)  # Armazena resposta completa da API
    
    # Controle
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)
    atualizado_em = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    ultima_sincronizacao = db.Column(db.DateTime)  # Última vez que foi sincronizado da API
    ativo = db.Column(db.Boolean, default=True)
    
    def __repr__(self):
        """Representação string do kit."""
        return f'<KitFotovoltaico {self.nome} - {self.potencia}kWp>'
    
    def __str__(self):
        """String do kit para exibição."""
        return f'{self.nome} ({self.potencia}kWp)'
    
    @property
    def preco_formatado(self):
        """Retorna preço formatado."""
        if self.preco:
            return f'R$ {float(self.preco):,.2f}'.replace(',', '_').replace('.', ',').replace('_', '.')
        return 'Consulte'
    
    @property
    def potencia_formatada(self):
        """Retorna potência formatada."""
        if self.potencia:
            return f'{self.potencia:.2f} kWp'
        return '-'
    
    @property
    def status_estoque(self):
        """Retorna status de estoque."""
        if not self.disponivel:
            return 'Indisponível'
        if self.estoque is None:
            return 'Disponível'
        if self.estoque > 10:
            return 'Em estoque'
        elif self.estoque > 0:
            return f'{self.estoque} unidades'
        else:
            return 'Fora de estoque'
    
    @property
    def composicao(self):
        """Retorna descrição da composição do kit."""
        partes = []
        
        if self.quantidade_modulos and self.potencia_modulo:
            partes.append(
                f'{self.quantidade_modulos}x Módulo {self.fabricante_modulo or ""} '
                f'{self.modelo_modulo or ""} {self.potencia_modulo}W'.strip()
            )
        
        if self.modelo_inversor:
            partes.append(
                f'1x Inversor {self.fabricante_inversor or""} '
                f'{self.modelo_inversor} {self.potencia_inversor or ""}kW'.strip()
            )
        
        return ' + '.join(partes) if partes else 'Composição não informada'
    
    def to_dict(self):
        """Converte o kit para dicionário."""
        return {
            'id': self.id,
            'kit_id_api': self.kit_id_api,
            'nome': self.nome,
            'descricao': self.descricao,
            'codigo': self.codigo,
            'potencia': self.potencia,
            'potencia_formatada': self.potencia_formatada,
            'preco': float(self.preco) if self.preco else None,
            'preco_formatado': self.preco_formatado,
            'disponivel': self.disponivel,
            'estoque': self.estoque,
            'status_estoque': self.status_estoque,
            'fabricante_modulo': self.fabricante_modulo,
            'modelo_modulo': self.modelo_modulo,
            'quantidade_modulos': self.quantidade_modulos,
            'fabricante_inversor': self.fabricante_inversor,
            'modelo_inversor': self.modelo_inversor,
            'composicao': self.composicao,
            'categoria': self.categoria,
            'tipo': self.tipo,
            'criado_em': self.criado_em.isoformat() if self.criado_em else None,
            'atualizado_em': self.atualizado_em.isoformat() if self.atualizado_em else None
        }
    
    @staticmethod
    def criar_ou_atualizar_da_api(dados_api: dict):
        """
        Cria ou atualiza um kit a partir dos dados da API.
        
        Args:
            dados_api: Dicionário com dados retornados pela API
        
        Returns:
            Instância de KitFotovoltaico
        """
        kit_id = dados_api.get('id') or dados_api.get('kit_id')
        
        if not kit_id:
            raise ValueError("dados_api deve conter 'id' ou 'kit_id'")
        
        # Busca kit existente
        kit = KitFotovoltaico.query.filter_by(kit_id_api=str(kit_id)).first()
        
        if not kit:
            kit = KitFotovoltaico(kit_id_api=str(kit_id))
            db.session.add(kit)
        
        # Atualiza campos
        kit.nome = dados_api.get('nome') or dados_api.get('name', '')
        kit.descricao = dados_api.get('descricao') or dados_api.get('description', '')
        kit.codigo = dados_api.get('codigo') or dados_api.get('sku', '')
        kit.potencia = dados_api.get('potencia') or dados_api.get('power_kwp', 0)
        kit.preco = dados_api.get('preco') or dados_api.get('price', 0)
        kit.disponivel = dados_api.get('disponivel', True)
        kit.estoque = dados_api.get('estoque') or dados_api.get('stock')
        kit.categoria = dados_api.get('categoria') or dados_api.get('category')
        kit.tipo = dados_api.get('tipo') or dados_api.get('type')
        
        # Módulos
        modulos = dados_api.get('modulos') or dados_api.get('modules', {})
        if isinstance(modulos, dict):
            kit.potencia_modulo = modulos.get('potencia') or modulos.get('power')
            kit.quantidade_modulos = modulos.get('quantidade') or modulos.get('quantity')
            kit.fabricante_modulo = modulos.get('fabricante') or modulos.get('manufacturer')
            kit.modelo_modulo = modulos.get('modelo') or modulos.get('model')
        
        # Inversor
        inversor = dados_api.get('inversor') or dados_api.get('inverter', {})
        if isinstance(inversor, dict):
            kit.potencia_inversor = inversor.get('potencia') or inversor.get('power')
            kit.fabricante_inversor = inversor.get('fabricante') or inversor.get('manufacturer')
            kit.modelo_inversor = inversor.get('modelo') or inversor.get('model')
            kit.tipo_inversor = inversor.get('tipo') or inversor.get('type')
        
        # Armazena dados completos
        kit.dados_completos_api = dados_api
        kit.ultima_sincronizacao = datetime.utcnow()
        
        return kit
