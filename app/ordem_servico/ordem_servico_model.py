# -*- coding: utf-8 -*-
"""
ERP JSP v3.0 - Model de Ordem de Serviço
========================================

Model para gerenciamento de ordens de serviço.
Controla abertura, execução e fechamento de serviços.

Autor: JSP Soluções
Data: 2025
"""

from app.extensoes import db
from app.models import BaseModel
from decimal import Decimal
from datetime import datetime, date
from sqlalchemy import func


class OrdemServico(BaseModel):
    """
    Model para Ordem de Serviço.
    
    Controla todo o ciclo de vida das ordens de serviço,
    desde a abertura até o fechamento.
    """
    
    __tablename__ = 'ordem_servico'
    
    # Campos básicos
    numero = db.Column(db.String(20), unique=True, nullable=False, index=True)
    
    # Cliente
    cliente_id = db.Column(db.Integer, db.ForeignKey('clientes.id'), nullable=False)
    cliente = db.relationship('Cliente', backref='ordens_servico')
    
    # Solicitação
    solicitante = db.Column(db.String(200))  # Nome da pessoa que solicitou o serviço
    descricao_problema = db.Column(db.Text)  # Descrição do problema ou defeito
    
    # Dados do serviço
    titulo = db.Column(db.String(200), nullable=False)
    descricao = db.Column(db.Text)
    observacoes = db.Column(db.Text)
    tipo_servico = db.Column(db.String(100))  # Tipo/categoria do serviço
    
    # Status do serviço
    status = db.Column(db.String(20), default='aberta', nullable=False)
    # Possíveis status: aberta, em_andamento, aguardando_pecas, aguardando_cliente, concluida, cancelada
    
    prioridade = db.Column(db.String(20), default='normal', nullable=False)
    # Possíveis prioridades: baixa, normal, alta, urgente

        
    # Datas
    data_abertura = db.Column(db.Date, default=date.today, nullable=False)
    data_prevista = db.Column(db.Date)
    data_inicio = db.Column(db.DateTime)
    data_conclusao = db.Column(db.DateTime)
    
    # Responsável
    tecnico_responsavel = db.Column(db.String(100))
    
    # Valores
    valor_servico = db.Column(db.Numeric(10, 2), default=0.00)
    valor_pecas = db.Column(db.Numeric(10, 2), default=0.00)
    valor_desconto = db.Column(db.Numeric(10, 2), default=0.00)
    valor_total = db.Column(db.Numeric(10, 2), default=0.00)
    
    # Garantia
    prazo_garantia = db.Column(db.Integer, default=0)  # em dias
    
    # Controles
    equipamento = db.Column(db.String(200))
    marca_modelo = db.Column(db.String(200))
    numero_serie = db.Column(db.String(100))
    defeito_relatado = db.Column(db.Text)
    diagnostico = db.Column(db.Text)
    solucao = db.Column(db.Text)
    
    # Controle de KM
    km_inicial = db.Column(db.Integer)
    km_final = db.Column(db.Integer)
    
    # Controle de Tempo
    hora_inicial = db.Column(db.Time)
    hora_final = db.Column(db.Time)
    
    # Condições de Pagamento
    condicao_pagamento = db.Column(db.String(50), default='a_vista')  # a_vista, parcelado
    numero_parcelas = db.Column(db.Integer, default=1)
    descricao_pagamento = db.Column(db.Text)  # Descrição detalhada das condições
    
    # Anexos e Documentos
    observacoes_anexos = db.Column(db.Text)  # Observações sobre anexos
    
    # Meta campos herdados de BaseModel:
    # id, data_criacao, data_atualizacao, ativo, usuario_criacao, usuario_atualizacao
    
    def __repr__(self):
        return f'<OrdemServico {self.numero}: {self.titulo}>'
    
    def __str__(self):
        return f'OS {self.numero} - {self.titulo}'
    
    @property
    def status_formatado(self):
        """Retorna status formatado para exibição."""
        status_map = {
            'aberta': 'Aberta',
            'em_andamento': 'Em Andamento',
            'aguardando_pecas': 'Aguardando Peças',
            'aguardando_cliente': 'Aguardando Cliente',
            'concluida': 'Concluída',
            'cancelada': 'Cancelada'
        }
        return status_map.get(self.status, self.status.title())
    
    @property
    def prioridade_formatada(self):
        """Retorna prioridade formatada para exibição."""
        prioridade_map = {
            'baixa': 'Baixa',
            'normal': 'Normal',
            'alta': 'Alta',
            'urgente': 'Urgente'
        }
        return prioridade_map.get(self.prioridade, self.prioridade.title())
    
    @property
    def km_total(self):
        """Calcula KM total percorrido."""
        if self.km_inicial and self.km_final and self.km_final > self.km_inicial:
            return self.km_final - self.km_inicial
        return 0
    
    @property
    def tempo_total_decimal(self):
        """Calcula tempo total em decimal (horas)."""
        if self.hora_inicial and self.hora_final:
            from datetime import datetime, timedelta
            
            # Converte time para datetime para cálculo
            hoje = datetime.today().date()
            inicio = datetime.combine(hoje, self.hora_inicial)
            fim = datetime.combine(hoje, self.hora_final)
            
            # Se hora final for menor, assume que passou para o dia seguinte
            if fim < inicio:
                fim += timedelta(days=1)
            
            diferenca = fim - inicio
            return diferenca.total_seconds() / 3600  # converte para horas
        return 0
    
    @property
    def tempo_total_formatado(self):
        """Retorna tempo total formatado (HH:MM)."""
        tempo_decimal = self.tempo_total_decimal
        if tempo_decimal > 0:
            horas = int(tempo_decimal)
            minutos = int((tempo_decimal - horas) * 60)
            return f"{horas:02d}:{minutos:02d}"
        return "00:00"
    
    @property
    def valor_total_servicos(self):
        """Calcula valor total dos serviços."""
        return sum(item.valor_total for item in self.servicos)
    
    @property
    def valor_total_produtos(self):
        """Calcula valor total dos produtos."""
        return sum(produto.valor_total for produto in self.produtos_utilizados)
    
    @property
    def valor_total_calculado_novo(self):
        """Calcula valor total (serviços + produtos - desconto)."""
        servicos = Decimal(str(self.valor_total_servicos or 0))
        produtos = Decimal(str(self.valor_total_produtos or 0))
        desconto = Decimal(str(self.valor_desconto or 0))
        return float(servicos + produtos - desconto)
    
    @property
    def status_cor(self):
        """Retorna cor do status para exibição."""
        cores = {
            'aberta': 'primary',
            'em_andamento': 'warning',
            'aguardando_pecas': 'info',
            'aguardando_cliente': 'secondary',
            'concluida': 'success',
            'cancelada': 'danger'
        }
        return cores.get(self.status, 'secondary')
    
    @property
    def prioridade_cor(self):
        """Retorna cor da prioridade para exibição."""
        cores = {
            'baixa': 'success',
            'normal': 'secondary',
            'alta': 'warning',
            'urgente': 'danger'
        }
        return cores.get(self.prioridade, 'secondary')
    
    @property
    def valor_total_calculado(self):
        """Calcula valor total (serviço + peças - desconto)."""
        servico = Decimal(str(self.valor_servico or 0))
        pecas = Decimal(str(self.valor_pecas or 0))
        desconto = Decimal(str(self.valor_desconto or 0))
        return float(servico + pecas - desconto)
    
    @property
    def prazo_vencido(self):
        """Verifica se o prazo está vencido."""
        if not self.data_prevista or self.status in ['concluida', 'cancelada']:
            return False
        return date.today() > self.data_prevista
    
    @property
    def dias_em_aberto(self):
        """Calcula quantos dias a OS está em aberto."""
        if self.status in ['concluida', 'cancelada']:
            return 0
        return (date.today() - self.data_abertura).days
    
    @classmethod
    def gerar_proximo_numero(cls):
        """
        Gera o próximo número de OS no formato OS2025001, OS2025002, etc.
        
        Sistema inteligente que:
        - Usa o ano atual
        - Busca o maior número existente
        - Garante sequência sem duplicatas
        - Formato: OS + ANO + SEQUENCIAL (4 dígitos)
        """
        ano_atual = date.today().year
        prefixo = f"OS{ano_atual}"
        
        # Busca a OS com maior número do ano usando ORDER BY para garantir eficiência
        ultima_os = cls.query.filter(
            cls.numero.like(f"{prefixo}%"),
            cls.ativo == True
        ).order_by(cls.numero.desc()).first()
        
        maior_numero = 0
        
        # Se encontrou alguma OS do ano, extrai o número
        if ultima_os:
            try:
                # Extrai apenas a parte numérica (remove "OS2025")
                parte_numerica = ultima_os.numero.replace(prefixo, "")
                if parte_numerica.isdigit():
                    maior_numero = int(parte_numerica)
            except (ValueError, AttributeError):
                # Se der erro, começa do 0
                maior_numero = 0
        
        # Próximo número é sempre maior + 1
        proximo_numero = maior_numero + 1
        
        # Gera o número final no formato OS2025001
        numero_os = f"{prefixo}{proximo_numero:04d}"
        
        # Verificação de segurança: garante que não existe duplicata
        tentativas = 0
        while cls.query.filter_by(numero=numero_os).first() and tentativas < 100:
            proximo_numero += 1
            numero_os = f"{prefixo}{proximo_numero:04d}"
            tentativas += 1
        
        return numero_os
    
    @classmethod
    def buscar_por_numero(cls, numero):
        """Busca OS por número."""
        return cls.query.filter_by(numero=numero, ativo=True).first()
    
    @classmethod
    def buscar_por_cliente(cls, cliente_id):
        """Busca OSs de um cliente."""
        return cls.query.filter_by(cliente_id=cliente_id, ativo=True).all()
    
    @classmethod
    def listar_por_status(cls, status):
        """Lista OSs por status."""
        return cls.query.filter_by(status=status, ativo=True).all()
    
    @classmethod
    def estatisticas_dashboard(cls):
        """Retorna estatísticas para o dashboard."""
        total = cls.query.filter_by(ativo=True).count()
        abertas = cls.query.filter_by(status='aberta', ativo=True).count()
        em_andamento = cls.query.filter_by(status='em_andamento', ativo=True).count()
        concluidas_mes = cls.query.filter(
            cls.status == 'concluida',
            cls.ativo == True,
            func.extract('month', cls.data_conclusao) == date.today().month,
            func.extract('year', cls.data_conclusao) == date.today().year
        ).count()
        
        return {
            'total': total,
            'abertas': abertas,
            'em_andamento': em_andamento,
            'concluidas_mes': concluidas_mes
        }
    
    def iniciar_servico(self):
        """Marca o início do serviço."""
        if self.status == 'aberta':
            self.status = 'em_andamento'
            self.data_inicio = datetime.now()
            self.save()
    
    def concluir_servico(self):
        """Marca a conclusão do serviço."""
        if self.status in ['aberta', 'em_andamento', 'aguardando_pecas', 'aguardando_cliente']:
            self.status = 'concluida'
            self.data_conclusao = datetime.now()
            self.save()
    
    def cancelar_servico(self):
        """Cancela o serviço."""
        if self.status != 'concluida':
            self.status = 'cancelada'
            self.save()
    
    def calcular_total(self):
        """Calcula e atualiza o valor total."""
        self.valor_total = self.valor_total_calculado
        self.save()


class OrdemServicoItem(BaseModel):
    """
    Model para itens de serviço da ordem.
    
    Representa cada serviço realizado com quantidade de horas,
    valor unitário e total.
    """
    
    __tablename__ = 'ordem_servico_itens'
    
    # Relacionamento com ordem de serviço
    ordem_servico_id = db.Column(db.Integer, db.ForeignKey('ordem_servico.id'), nullable=False)
    ordem_servico = db.relationship('OrdemServico', backref='servicos')
    
    # Dados do serviço
    descricao = db.Column(db.String(200), nullable=False)
    quantidade_horas = db.Column(db.Numeric(5, 2), default=0.00)
    valor_hora = db.Column(db.Numeric(10, 2), default=0.00)
    valor_total = db.Column(db.Numeric(10, 2), default=0.00)
    
    def __repr__(self):
        return f'<OrdemServicoItem {self.descricao}: {self.quantidade_horas}h>'
    
    def calcular_total(self):
        """Calcula valor total do item."""
        if self.quantidade_horas and self.valor_hora:
            self.valor_total = float(Decimal(str(self.quantidade_horas)) * Decimal(str(self.valor_hora)))
        else:
            self.valor_total = 0.00


class OrdemServicoProduto(BaseModel):
    """
    Model para produtos utilizados na ordem de serviço.
    
    Representa produtos/peças utilizados na execução do serviço.
    """
    
    __tablename__ = 'ordem_servico_produtos'
    
    # Relacionamento com ordem de serviço
    ordem_servico_id = db.Column(db.Integer, db.ForeignKey('ordem_servico.id'), nullable=False)
    ordem_servico = db.relationship('OrdemServico', backref='produtos_utilizados')
    
    # Relacionamento com produto (opcional - pode ser produto não cadastrado)
    produto_id = db.Column(db.Integer, db.ForeignKey('produtos.id'), nullable=True)
    produto = db.relationship('Produto', backref='ordens_servico')
    
    # Dados do produto
    descricao = db.Column(db.String(200), nullable=False)
    quantidade = db.Column(db.Numeric(10, 3), default=1.000)
    valor_unitario = db.Column(db.Numeric(10, 2), default=0.00)
    valor_total = db.Column(db.Numeric(10, 2), default=0.00)
    
    def __repr__(self):
        return f'<OrdemServicoProduto {self.descricao}: {self.quantidade}x>'
    
    def calcular_total(self):
        """Calcula valor total do produto."""
        if self.quantidade and self.valor_unitario:
            self.valor_total = float(Decimal(str(self.quantidade)) * Decimal(str(self.valor_unitario)))
        else:
            self.valor_total = 0.00


class OrdemServicoParcela(BaseModel):
    """
    Model para parcelas da ordem de serviço.
    
    Quando a ordem é parcelada, cada parcela tem sua data
    de vencimento e valor.
    """
    
    __tablename__ = 'ordem_servico_parcelas'
    
    # Relacionamento com ordem de serviço
    ordem_servico_id = db.Column(db.Integer, db.ForeignKey('ordem_servico.id'), nullable=False)
    ordem_servico = db.relationship('OrdemServico', backref='parcelas')
    
    # Dados da parcela
    numero_parcela = db.Column(db.Integer, nullable=False)
    data_vencimento = db.Column(db.Date, nullable=False)
    valor = db.Column(db.Numeric(10, 2), nullable=False)
    pago = db.Column(db.Boolean, default=False)
    data_pagamento = db.Column(db.Date)
    
    def __repr__(self):
        return f'<OrdemServicoParcela {self.numero_parcela}: R$ {self.valor}>'
    
    @property
    def status_parcela(self):
        """Retorna status da parcela."""
        if self.pago:
            return 'paga'
        elif self.data_vencimento < date.today():
            return 'vencida'
        else:
            return 'pendente'
    
    @property
    def status_cor(self):
        """Retorna cor do status da parcela."""
        cores = {
            'paga': 'success',
            'vencida': 'danger',
            'pendente': 'warning'
        }
        return cores.get(self.status_parcela, 'secondary')


class OrdemServicoAnexo(BaseModel):
    """
    Model para anexos da ordem de serviço.
    
    Armazena informações sobre arquivos anexados
    à ordem de serviço (imagens, documentos, etc.).
    """
    
    __tablename__ = 'ordem_servico_anexos'
    
    # Relacionamento com ordem de serviço
    ordem_servico_id = db.Column(db.Integer, db.ForeignKey('ordem_servico.id'), nullable=False)
    ordem_servico = db.relationship('OrdemServico', backref='anexos')
    
    # Dados do arquivo
    nome_original = db.Column(db.String(255), nullable=False)
    nome_arquivo = db.Column(db.String(255), nullable=False)  # nome salvo no servidor
    tipo_arquivo = db.Column(db.String(50), nullable=False)  # image, document
    mime_type = db.Column(db.String(100))
    tamanho = db.Column(db.Integer)  # em bytes
    caminho = db.Column(db.String(500), nullable=False)
    
    def __repr__(self):
        return f'<OrdemServicoAnexo {self.nome_original}>'
    
    @property
    def tamanho_formatado(self):
        """Retorna tamanho formatado em KB ou MB."""
        if not self.tamanho:
            return "0 KB"
        
        if self.tamanho < 1024:
            return f"{self.tamanho} B"
        elif self.tamanho < 1024 * 1024:
            return f"{self.tamanho / 1024:.1f} KB"
        else:
            return f"{self.tamanho / (1024 * 1024):.1f} MB"
    
    @property
    def icone(self):
        """Retorna ícone baseado no tipo de arquivo."""
        if self.tipo_arquivo == 'image':
            return 'fas fa-image text-success'
        elif self.mime_type:
            if 'pdf' in self.mime_type:
                return 'fas fa-file-pdf text-danger'
            elif 'word' in self.mime_type or 'document' in self.mime_type:
                return 'fas fa-file-word text-primary'
            elif 'excel' in self.mime_type or 'spreadsheet' in self.mime_type:
                return 'fas fa-file-excel text-success'
            elif 'text' in self.mime_type:
                return 'fas fa-file-alt text-secondary'
        
        return 'fas fa-file text-muted'