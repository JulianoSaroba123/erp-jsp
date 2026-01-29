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
from datetime import datetime, date, timedelta
from sqlalchemy import func


class Proposta(BaseModel):
    """
    Model para Proposta Comercial.
    
    Gerencia propostas comerciais com produtos e serviços separados.
    """
    
    __tablename__ = 'propostas'
    
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
    status = db.Column(db.String(20), default='rascunho', nullable=False)
    # Possíveis status: rascunho, enviada, aprovada, rejeitada, cancelada
    
    # Datas
    data_emissao = db.Column(db.Date, default=date.today, nullable=False)
    validade = db.Column(db.Integer, default=30)  # dias de validade
    data_validade = db.Column(db.Date)  # calculado automaticamente
    data_aprovacao = db.Column(db.DateTime)
    
    # Responsável
    vendedor = db.Column(db.String(100))
    
    # Informações adicionais
    prioridade = db.Column(db.String(20), default='normal')  # baixa, normal, alta, urgente
    km_estimado = db.Column(db.Numeric(8, 2))  # Quilometragem estimada
    tempo_estimado = db.Column(db.String(100))  # Tempo estimado (ex: "2 horas", "1 dia")
    
    # Valores
    valor_produtos = db.Column(db.Numeric(10, 2), default=0.00)
    valor_servicos = db.Column(db.Numeric(10, 2), default=0.00)
    desconto = db.Column(db.Numeric(5, 2), default=0.00)  # percentual
    valor_total = db.Column(db.Numeric(10, 2), default=0.00)
    entrada = db.Column(db.Numeric(5, 2), default=0.00)  # percentual de entrada
    
    # Condições
    condicoes_pagamento = db.Column(db.Text)
    prazo_execucao = db.Column(db.String(500))
    garantia = db.Column(db.String(500))
    forma_pagamento = db.Column(db.String(500), default='a_vista')
    
    # Dados de Parcelamento (quando forma_pagamento = 'parcelado')
    numero_parcelas = db.Column(db.Integer, default=1)  # Quantidade de parcelas
    intervalo_parcelas = db.Column(db.Integer, default=30)  # Dias entre parcelas
    data_primeira_parcela = db.Column(db.Date)  # Data de vencimento da 1ª parcela
    
    # Meta campos herdados de BaseModel:
    # id, data_criacao, data_atualizacao, ativo, usuario_criacao, usuario_atualizacao
    
    def __repr__(self):
        return f'<Proposta {self.codigo}: {self.titulo}>'
    
    def __str__(self):
        return f'Proposta {self.codigo} - {self.titulo}'
    
    def __init__(self, **kwargs):
        """Inicializa proposta e gera código automaticamente se não fornecido."""
        # Se não foi fornecido código, gerar automaticamente
        if 'codigo' not in kwargs or not kwargs['codigo']:
            kwargs['codigo'] = self.__class__.gerar_proximo_codigo()
        
        super().__init__(**kwargs)
    
    @property
    def status_formatado(self):
        """Retorna status formatado para exibição."""
        status_map = {
            'rascunho': 'Rascunho',
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
            'rascunho': 'secondary',
            'enviada': 'info',
            'aprovada': 'success',
            'rejeitada': 'danger',
            'cancelada': 'warning'
        }
        return cores.get(self.status, 'secondary')
    
    @property
    def prioridade_formatada(self):
        """Retorna prioridade formatada para exibição."""
        prioridade_map = {
            'baixa': 'Baixa',
            'normal': 'Normal',
            'alta': 'Alta',
            'urgente': 'Urgente'
        }
        return prioridade_map.get(self.prioridade or 'normal', 'Normal')
    
    @property
    def prioridade_cor(self):
        """Retorna cor da prioridade para exibição."""
        cores = {
            'baixa': 'secondary',
            'normal': 'primary',
            'alta': 'warning',
            'urgente': 'danger'
        }
        return cores.get(self.prioridade or 'normal', 'primary')

    @property
    def pode_converter(self):
        """Indica se a proposta pode ser convertida em Ordem de Serviço.

        Critério atual: a proposta está aprovada e está ativa. Pode ser ampliado
        no futuro para checar vinculações ou flags adicionais.
        """
        try:
            if not self.status:
                return False
            return (str(self.status).strip().lower() == 'aprovada') and bool(self.ativo)
        except Exception:
            return False
    
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
            try:
                # Converter para int se for string
                dias = int(self.validade) if isinstance(self.validade, str) else self.validade
                return self.data_emissao + timedelta(days=dias)
            except (ValueError, TypeError):
                return None
        return None
    
    @property
    def proposta_vencida(self):
        """Verifica se a proposta está vencida."""
        valida_ate = self.valida_ate
        if not valida_ate or self.status in ['aprovada', 'rejeitada', 'cancelada']:
            return False
        return date.today() > valida_ate
    
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
    
    def gerar_parcelas(self):
        """
        Gera as parcelas de pagamento baseado nos dados de parcelamento.
        
        Remove parcelas existentes e cria novas baseado em:
        - numero_parcelas
        - entrada (percentual)
        - data_primeira_parcela
        - intervalo_parcelas
        - valor_total
        """
        try:
            # Verifica se os campos existem (para compatibilidade com BD antigo)
            if not hasattr(self, 'numero_parcelas') or not hasattr(self, 'intervalo_parcelas'):
                return
            
            if self.forma_pagamento != 'parcelado' or not self.numero_parcelas:
                return
        except Exception as e:
            # Se houver erro ao acessar os campos, retorna silenciosamente
            return
        
        # Remove parcelas antigas
        ParcelaProposta.query.filter_by(proposta_id=self.id).delete()
        
        # Calcula valores
        valor_total = Decimal(str(self.valor_total or 0))
        percentual_entrada = Decimal(str(self.entrada or 0))
        valor_entrada = valor_total * (percentual_entrada / 100)
        valor_restante = valor_total - valor_entrada
        numero_parcelas = int(self.numero_parcelas or 1)
        valor_parcela = valor_restante / numero_parcelas if numero_parcelas > 0 else Decimal(0)
        
        # Data da primeira parcela (ou hoje se não definida)
        data_base = self.data_primeira_parcela or date.today()
        intervalo = int(self.intervalo_parcelas or 30)
        
        parcelas_criadas = []
        
        # Cria entrada se houver
        if valor_entrada > 0:
            parcela_entrada = ParcelaProposta(
                proposta_id=self.id,
                numero_parcela=0,
                valor_parcela=float(valor_entrada),
                data_vencimento=data_base,
                descricao=f"Entrada ({percentual_entrada}%)",
                status='pendente'
            )
            db.session.add(parcela_entrada)
            parcelas_criadas.append(parcela_entrada)
        
        # Cria parcelas restantes
        for i in range(1, numero_parcelas + 1):
            # Calcula data de vencimento (entrada + intervalo * número da parcela)
            dias_apos_entrada = intervalo * i
            data_venc = data_base + timedelta(days=dias_apos_entrada)
            
            # Ajusta última parcela para incluir centavos restantes
            if i == numero_parcelas:
                # Soma todas as parcelas criadas
                total_parcelas = sum(p.valor_parcela for p in parcelas_criadas)
                valor_ajustado = float(valor_total) - total_parcelas
            else:
                valor_ajustado = float(valor_parcela)
            
            parcela = ParcelaProposta(
                proposta_id=self.id,
                numero_parcela=i,
                valor_parcela=valor_ajustado,
                data_vencimento=data_venc,
                descricao=f"Parcela {i}/{numero_parcelas}",
                status='pendente'
            )
            db.session.add(parcela)
            parcelas_criadas.append(parcela)
        
        db.session.commit()
        return parcelas_criadas
    
    def gerar_ordem_servico(self):
        """
        Gera uma nova Ordem de Serviço a partir desta proposta aprovada.
        Transfere todos os dados incluindo condições de pagamento e parcelas.
        
        Returns:
            OrdemServico: Nova OS criada ou None se não foi possível
        """
        if not self.pode_converter:
            return None
        
        from app.ordem_servico.ordem_servico_model import OrdemServico, OrdemServicoItem, OrdemServicoProduto, OrdemServicoParcela
        from datetime import timedelta
        
        # Determinar condições de pagamento da proposta
        condicao_pgto = 'a_vista'
        num_parcelas = 0
        valor_entrada = 0.0
        data_primeira_parcela = None
        
        # Verificar se há parcelas cadastradas na proposta
        if hasattr(self, 'parcelas') and self.parcelas:
            parcelas_proposta = [p for p in self.parcelas if p.ativo]
            print(f"🔍 DEBUG: Proposta {self.codigo} tem {len(parcelas_proposta)} parcelas ativas")
            
            if parcelas_proposta:
                condicao_pgto = 'parcelado'
                
                # IMPORTANTE: As parcelas da proposta começam em 1, não em 0
                # Todas as parcelas são transferidas para a OS
                num_parcelas = len(parcelas_proposta)
                
                # Pegar valor de entrada do campo da proposta (se houver)
                if self.entrada and self.entrada > 0:
                    # Entrada está em percentual, converter para valor
                    valor_entrada = float(self.valor_total or 0) * (float(self.entrada) / 100)
                    print(f"   💰 Entrada (da proposta): {self.entrada}% = R$ {valor_entrada}")
                else:
                    valor_entrada = 0.0
                
                # Data da primeira parcela
                primeira_parcela = min(parcelas_proposta, key=lambda p: p.numero_parcela)
                data_primeira_parcela = primeira_parcela.data_vencimento
                
                print(f"   📊 Total de parcelas: {num_parcelas}")
                print(f"   📅 Data 1ª parcela: {data_primeira_parcela}")
        else:
            print(f"⚠️ DEBUG: Proposta {self.codigo} NÃO tem parcelas cadastradas!")
        
        print(f"✅ DEBUG: Condições finais - Pagamento: {condicao_pgto} | Parcelas: {num_parcelas} | Entrada: R$ {valor_entrada}")
        
        # Se não tem parcelas, é à vista
        if num_parcelas == 0:
            condicao_pgto = 'a_vista'
            num_parcelas = 1
        
        # Criar nova OS com todos os campos obrigatórios
        nova_os = OrdemServico(
            # Campos obrigatórios do banco
            numero=OrdemServico.gerar_proximo_numero(),  # Gera número sequencial
            proposta_id=self.id,
            cliente_id=self.cliente_id,
            titulo=self.titulo or 'Ordem de Serviço',
            descricao=self.descricao or '',
            observacoes=f"OS gerada automaticamente da Proposta {self.codigo}",
            status='pendente',
            prioridade=self.prioridade or 'normal',
            data_abertura=date.today(),
            data_prevista=date.today() + timedelta(days=7),
            
            # Campos opcionais com valores padrão
            solicitante=self.cliente.nome if self.cliente else None,
            tecnico_responsavel=self.vendedor or 'Juliano',
            tipo_servico='a_vista',
            
            # Valores financeiros
            valor_servico=0.0,
            valor_pecas=0.0,
            valor_desconto=float(self.desconto or 0),
            valor_total=float(self.valor_total or 0),
            
            # Garantia
            prazo_garantia=90,  # 90 dias padrão
            
            # Condições de pagamento (transferidas da proposta)
            condicao_pagamento=condicao_pgto,
            numero_parcelas=num_parcelas,
            valor_entrada=valor_entrada,
            data_primeira_parcela=data_primeira_parcela,
            status_pagamento='pendente'
        )
        
        # Salvar a OS primeiro para ter o ID
        from app.extensoes import db
        db.session.add(nova_os)
        db.session.flush()  # Gera o ID sem fazer commit
        
        # Transferir produtos
        for produto in self.itens_produto:
            if produto.ativo:
                os_produto = OrdemServicoProduto(
                    ordem_servico_id=nova_os.id,
                    produto_id=produto.produto_id,
                    descricao=produto.descricao,
                    quantidade=produto.quantidade,
                    valor_unitario=produto.valor_unitario,
                    valor_total=produto.valor_total
                )
                db.session.add(os_produto)
        
        # Transferir serviços
        for servico in self.itens_servico:
            if servico.ativo:
                os_servico = OrdemServicoItem(
                    ordem_servico_id=nova_os.id,
                    descricao=servico.descricao,
                    tipo_servico=servico.tipo_servico or 'fechado',
                    quantidade=servico.quantidade,
                    valor_unitario=servico.valor_unitario,
                    valor_total=servico.valor_total
                )
                db.session.add(os_servico)
        
        # Transferir parcelas da proposta para a OS
        if hasattr(self, 'parcelas') and self.parcelas:
            parcelas_proposta = [p for p in self.parcelas if p.ativo]
            print(f"🔄 DEBUG: Transferindo {len(parcelas_proposta)} parcelas da proposta para OS")
            
            for parcela_prop in parcelas_proposta:
                os_parcela = OrdemServicoParcela(
                    ordem_servico_id=nova_os.id,
                    numero_parcela=parcela_prop.numero_parcela,
                    data_vencimento=parcela_prop.data_vencimento,
                    valor=parcela_prop.valor,
                    pago=False  # Parcela inicia como não paga
                )
                db.session.add(os_parcela)
                print(f"   ✅ Parcela {parcela_prop.numero_parcela}: R$ {parcela_prop.valor} - Venc: {parcela_prop.data_vencimento}")
        else:
            print(f"⚠️ DEBUG: Proposta não tem parcelas para transferir")
        
        # Atualizar valores da OS
        nova_os.atualizar_valores_automaticos()
        
        # Commit de tudo
        db.session.commit()
        
        return nova_os


class PropostaProduto(BaseModel):
    """
    Model para produtos da proposta.
    
    Representa cada produto incluído na proposta comercial.
    """
    
    __tablename__ = 'proposta_produto'
    
    # Relacionamento com proposta
    proposta_id = db.Column(db.Integer, db.ForeignKey('propostas.id'), nullable=False)
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
    proposta_id = db.Column(db.Integer, db.ForeignKey('propostas.id'), nullable=False)
    proposta = db.relationship('Proposta', backref='itens_servico')
    
    # Dados do serviço
    descricao = db.Column(db.String(500), nullable=False)
    tipo_servico = db.Column(db.String(20), default='hora')  # hora, dia, fechado
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
    proposta_id = db.Column(db.Integer, db.ForeignKey('propostas.id'), nullable=False)
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
    proposta_id = db.Column(db.Integer, db.ForeignKey('propostas.id'), nullable=False)
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


class ParcelaProposta(BaseModel):
    """
    Model para Parcelas de Pagamento da Proposta.
    
    Armazena o parcelamento quando forma_pagamento = 'parcelado'.
    """
    
    __tablename__ = 'parcelas_proposta'
    
    # Relacionamento
    proposta_id = db.Column(db.Integer, db.ForeignKey('propostas.id'), nullable=False)
    proposta = db.relationship('Proposta', backref='parcelas_pagamento')
    
    # Dados da parcela
    numero_parcela = db.Column(db.Integer, nullable=False)  # 1, 2, 3...
    valor_parcela = db.Column(db.Numeric(10, 2), nullable=False)
    data_vencimento = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(20), default='pendente')  # pendente, pago, cancelado
    data_pagamento = db.Column(db.Date)
    descricao = db.Column(db.String(200))  # Ex: "Parcela 1/12 - Entrada"
    
    def __repr__(self):
        return f'<Parcela {self.numero_parcela} - R$ {self.valor_parcela}>'
