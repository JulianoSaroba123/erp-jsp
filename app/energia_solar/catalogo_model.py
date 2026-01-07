"""
Modelos de Catálogo para Energia Solar
"""
from app.extensoes import db
from datetime import datetime


class KitSolar(db.Model):
    """Modelo para catálogo de kits completos de energia solar"""
    __tablename__ = 'kit_solar'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Identificação
    fabricante = db.Column(db.String(100), nullable=False)
    descricao = db.Column(db.String(500), nullable=False)
    outras_informacoes = db.Column(db.Text)
    
    # Especificações do Kit
    potencia_kwp = db.Column(db.Float, nullable=False)  # kWp
    preco = db.Column(db.Float, nullable=False)
    
    # Componentes - Placas
    placa_id = db.Column(db.Integer, db.ForeignKey('placa_solar.id'), nullable=False)
    qtd_placas = db.Column(db.Integer, nullable=False, default=1)
    
    # Componentes - Inversores
    inversor_id = db.Column(db.Integer, db.ForeignKey('inversor_solar.id'), nullable=False)
    qtd_inversores = db.Column(db.Integer, nullable=False, default=1)
    
    # Relacionamentos
    placa = db.relationship('PlacaSolar', backref='kits', lazy=True)
    inversor = db.relationship('InversorSolar', backref='kits', lazy=True)
    
    # Metadados
    data_cadastro = db.Column(db.DateTime, default=datetime.utcnow)
    data_atualizacao = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    ativo = db.Column(db.Boolean, default=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'fabricante': self.fabricante,
            'descricao': self.descricao,
            'outras_informacoes': self.outras_informacoes,
            'potencia_kwp': self.potencia_kwp,
            'preco': self.preco,
            'qtd_placas': self.qtd_placas,
            'qtd_inversores': self.qtd_inversores,
            'placa': self.placa.to_dict() if self.placa else None,
            'inversor': self.inversor.to_dict() if self.inversor else None
        }
    
    def __repr__(self):
        return f'<KitSolar {self.fabricante} - {self.potencia_kwp}kWp>'


class PlacaSolar(db.Model):
    """Modelo para catálogo de placas solares"""
    __tablename__ = 'placa_solar'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Identificação
    modelo = db.Column(db.String(100), nullable=False)
    fabricante = db.Column(db.String(100), nullable=False)
    
    # Especificações Técnicas
    potencia = db.Column(db.Float, nullable=False)  # Watts
    comprimento = db.Column(db.Float)  # mm
    largura = db.Column(db.Float)  # mm
    espessura = db.Column(db.Float)  # mm
    peso = db.Column(db.Float)  # kg
    num_celulas = db.Column(db.Integer)  # 60, 72, 144, etc
    
    # Características Elétricas
    tensao_circuito_aberto = db.Column(db.Float)  # Voc
    corrente_curto_circuito = db.Column(db.Float)  # Isc
    tensao_maxima_potencia = db.Column(db.Float)  # Vmp
    corrente_maxima_potencia = db.Column(db.Float)  # Imp
    eficiencia = db.Column(db.Float)  # %
    
    # Coeficientes de Temperatura
    coef_temp_potencia = db.Column(db.Float)  # %/°C
    temp_operacao_nominal = db.Column(db.Float)  # NOCT
    
    # Garantias
    garantia_produto = db.Column(db.Integer)  # anos
    garantia_desempenho = db.Column(db.Integer)  # anos
    degradacao_ano1 = db.Column(db.Float)  # %
    degradacao_anual = db.Column(db.Float)  # %
    
    # Comercial
    preco_custo = db.Column(db.Float)
    preco_venda = db.Column(db.Float)
    fornecedor = db.Column(db.String(200))
    datasheet = db.Column(db.String(500))  # Caminho ou URL do PDF
    
    # Controle
    ativo = db.Column(db.Boolean, default=True)
    data_cadastro = db.Column(db.DateTime, default=datetime.utcnow)
    observacoes = db.Column(db.Text)
    
    def to_dict(self):
        """Converte para dicionário para JSON"""
        return {
            'id': self.id,
            'modelo': self.modelo,
            'fabricante': self.fabricante,
            'potencia': self.potencia,
            'comprimento': self.comprimento,
            'largura': self.largura,
            'espessura': self.espessura,
            'eficiencia': self.eficiencia,
            'num_celulas': self.num_celulas,
            'garantia_produto': self.garantia_produto,
            'garantia_desempenho': self.garantia_desempenho,
            'preco_venda': self.preco_venda,
            'preco_custo': self.preco_custo
        }
    
    def __repr__(self):
        return f'<PlacaSolar {self.fabricante} {self.modelo} - {self.potencia}W>'
    
    def area_m2(self):
        """Calcula área em m²"""
        if self.comprimento and self.largura:
            return (self.comprimento * self.largura) / 1000000
        return 2.0  # padrão


class InversorSolar(db.Model):
    """Modelo para catálogo de inversores solares"""
    __tablename__ = 'inversor_solar'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Identificação
    modelo = db.Column(db.String(100), nullable=False)
    fabricante = db.Column(db.String(100), nullable=False)
    tipo = db.Column(db.String(50))  # String, Micro, Híbrido
    
    # Especificações Elétricas
    potencia_nominal = db.Column(db.Float, nullable=False)  # kW
    potencia_maxima = db.Column(db.Float)  # kW
    tensao_entrada_min = db.Column(db.Float)  # V
    tensao_entrada_max = db.Column(db.Float)  # V
    tensao_mppt_min = db.Column(db.Float)  # V
    tensao_mppt_max = db.Column(db.Float)  # V
    corrente_entrada_max = db.Column(db.Float)  # A
    num_mppt = db.Column(db.Integer)  # Número de rastreadores
    strings_por_mppt = db.Column(db.Integer)
    
    # Saída
    tensao_saida = db.Column(db.String(50))  # 127V, 220V, 380V
    fases = db.Column(db.String(20))  # Monofásico, Bifásico, Trifásico
    corrente_saida_max = db.Column(db.Float)  # A
    frequencia = db.Column(db.String(20))  # 60Hz
    
    # Características
    eficiencia_maxima = db.Column(db.Float)  # %
    eficiencia_europeia = db.Column(db.Float)  # %
    consumo_noturno = db.Column(db.Float)  # W
    
    # Proteções
    grau_protecao = db.Column(db.String(20))  # IP65, IP67
    temp_operacao_min = db.Column(db.Float)  # °C
    temp_operacao_max = db.Column(db.Float)  # °C
    
    # Físico
    peso = db.Column(db.Float)  # kg
    dimensoes = db.Column(db.String(100))  # LxAxP
    
    # Garantia
    garantia_anos = db.Column(db.Integer)
    
    # Comercial
    preco_custo = db.Column(db.Float)
    preco_venda = db.Column(db.Float)
    fornecedor = db.Column(db.String(200))
    datasheet = db.Column(db.String(500))  # Caminho ou URL do PDF
    
    # Controle
    ativo = db.Column(db.Boolean, default=True)
    data_cadastro = db.Column(db.DateTime, default=datetime.utcnow)
    observacoes = db.Column(db.Text)
    
    def __repr__(self):
        return f'<InversorSolar {self.fabricante} {self.modelo} - {self.potencia_nominal}kW>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'modelo': self.modelo,
            'fabricante': self.fabricante,
            'tipo': self.tipo,
            'potencia_nominal': self.potencia_nominal,
            'potencia_maxima': self.potencia_maxima,
            'tensao_entrada_min': self.tensao_entrada_min,
            'tensao_entrada_max': self.tensao_entrada_max,
            'tensao_mppt_min': self.tensao_mppt_min,
            'tensao_mppt_max': self.tensao_mppt_max,
            'num_mppt': self.num_mppt,
            'strings_por_mppt': self.strings_por_mppt,
            'eficiencia_maxima': self.eficiencia_maxima,
            'fases': self.fases,
            'garantia_anos': self.garantia_anos,
            'grau_protecao': self.grau_protecao,
            'preco_venda': self.preco_venda,
            'preco_custo': self.preco_custo
        }


class ProjetoSolar(db.Model):
    """Modelo para projetos completos de energia solar"""
    __tablename__ = 'projeto_solar'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Aba 1 - Cliente e Localização
    cliente_id = db.Column(db.Integer, db.ForeignKey('clientes.id'))
    nome_cliente = db.Column(db.String(200))  # Fallback se não tiver cliente cadastrado
    cep = db.Column(db.String(10))
    endereco = db.Column(db.String(300))
    numero = db.Column(db.String(20))  # Número do endereço
    cidade = db.Column(db.String(100))
    estado = db.Column(db.String(2))
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)
    irradiacao_solar = db.Column(db.Float)  # kWh/m²/dia
    
    # Aba 2 - Consumo e Dimensionamento
    metodo_calculo = db.Column(db.String(50))  # 'kwh_direto', 'historico_12m', 'valor_conta'
    consumo_kwh_mes = db.Column(db.Float)  # kWh/mês
    historico_consumo = db.Column(db.JSON)  # {jan: 300, fev: 280, ...}
    valor_conta_luz = db.Column(db.Float)  # R$
    tarifa_kwh = db.Column(db.Float)  # R$/kWh
    tipo_instalacao = db.Column(db.String(20), default='monofasica')  # monofasica, bifasica, trifasica
    
    # Dimensionamento
    potencia_kwp = db.Column(db.Float)  # kWp calculado
    geracao_estimada_mes = db.Column(db.Float)  # kWh/mês
    simultaneidade = db.Column(db.Float, default=0.80)  # %
    perdas_sistema = db.Column(db.Float, default=0.20)  # %
    
    # Aba 3 - Equipamentos
    modo_equipamento = db.Column(db.String(20))  # 'kit' ou 'individual'
    kit_id = db.Column(db.Integer, db.ForeignKey('kit_solar.id'))
    placa_id = db.Column(db.Integer, db.ForeignKey('placa_solar.id'))
    inversor_id = db.Column(db.Integer, db.ForeignKey('inversor_solar.id'))
    qtd_placas = db.Column(db.Integer)
    qtd_inversores = db.Column(db.Integer)
    
    # Aba 4 - Layout da Instalação
    orientacao = db.Column(db.String(20))  # Norte, Sul, Leste, Oeste
    inclinacao = db.Column(db.Float)  # graus
    direcao = db.Column(db.String(20))  # Azimute
    linhas_placas = db.Column(db.Integer)
    colunas_placas = db.Column(db.Integer)
    area_necessaria = db.Column(db.Float)  # m²
    
    # Aba 5 - Componentes Adicionais
    string_box = db.Column(db.Boolean, default=False)
    disjuntor_cc = db.Column(db.String(50))
    disjuntor_ca = db.Column(db.String(50))
    cabo_cc = db.Column(db.String(50))  # bitola
    cabo_ca = db.Column(db.String(50))  # bitola
    estrutura_fixacao = db.Column(db.String(100))
    componentes_extras = db.Column(db.JSON)  # [{nome: '', qtd: 0, preco: 0}]
    
    # Aba 6 - Financeiro e Lei 14.300
    custo_equipamentos = db.Column(db.Float)
    custo_instalacao = db.Column(db.Float)
    custo_projeto = db.Column(db.Float)
    custo_total = db.Column(db.Float)
    margem_lucro = db.Column(db.Float)  # %
    valor_venda = db.Column(db.Float)
    
    # Lei 14.300/2022
    lei_14300_ano = db.Column(db.Integer)  # 2023, 2024, 2025, etc
    modalidade_gd = db.Column(db.String(10))  # 'GD I', 'GD II'
    aliquota_fio_b = db.Column(db.Float)  # %
    economia_anual = db.Column(db.Float)  # R$/ano
    payback_anos = db.Column(db.Float)  # anos
    
    # Controle
    status = db.Column(db.String(50), default='rascunho')  # rascunho, aprovado, instalado
    observacoes = db.Column(db.Text)
    data_criacao = db.Column(db.DateTime, default=datetime.utcnow)
    data_atualizacao = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    usuario_criador = db.Column(db.String(100))
    
    def to_dict(self):
        return {
            'id': self.id,
            'cliente_id': self.cliente_id,
            'nome_cliente': self.nome_cliente,
            'endereco': self.endereco,
            'cidade': self.cidade,
            'estado': self.estado,
            'consumo_kwh_mes': self.consumo_kwh_mes,
            'potencia_kwp': self.potencia_kwp,
            'qtd_placas': self.qtd_placas,
            'qtd_inversores': self.qtd_inversores,
            'custo_total': self.custo_total,
            'valor_venda': self.valor_venda,
            'status': self.status,
            'payback_anos': self.payback_anos
        }
    
    def __repr__(self):
        return f'<ProjetoSolar {self.id} - {self.nome_cliente} - {self.potencia_kwp}kWp>'
