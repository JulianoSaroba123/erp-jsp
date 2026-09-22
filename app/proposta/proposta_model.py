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
    
    @property
    def vencida(self):
        """Alias para proposta_vencida para compatibilidade com templates."""
        return self.proposta_vencida
    
    @property
    def dias_para_vencimento(self):
        """Retorna quantos dias faltam para a proposta vencer."""
        valida_ate = self.valida_ate
        if not valida_ate or self.status in ['aprovada', 'rejeitada', 'cancelada']:
            return None
        dias = (valida_ate - date.today()).days
        return dias if dias >= 0 else None
    
    @property
    def condicao_pagamento(self):
        """Alias para forma_pagamento para compatibilidade com templates."""
        return self.forma_pagamento
    
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
        """Aprova a proposta e sincroniza seus recebiveis.

        A operacao e idempotente:
        - proposta ja aprovada pode ser sincronizada novamente;
        - parcelas ja vinculadas nao geram duplicidade;
        - aprovacao e financeiro fecham na mesma transacao.
        """
        status_atual = (
            str(self.status or "")
            .strip()
            .lower()
        )

        if status_atual not in {
            "pendente",
            "enviada",
            "aprovada",
        }:
            return self

        self.status = "aprovada"

        if not self.data_aprovacao:
            self.data_aprovacao = datetime.now()

        db.session.add(self)
        db.session.flush()

        from app.financeiro.proposta_financeiro_service import (
            sincronizar_lancamentos_proposta,
        )

        sincronizar_lancamentos_proposta(self)

        db.session.commit()

        return self
    
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
        """Gera parcelas sem destruir identidade financeira existente.

        Enquanto a proposta ainda nao possui financeiro vinculado,
        o comportamento permanece compativel com o fluxo legado.

        Depois que uma parcela origina LancamentoFinanceiro,
        sua identidade passa a ser historico comercial/financeiro e
        nao pode mais ser apagada e recriada silenciosamente.
        """
        try:
            if (
                not hasattr(self, "numero_parcelas")
                or not hasattr(
                    self,
                    "intervalo_parcelas",
                )
            ):
                return []

            if (
                self.forma_pagamento != "parcelado"
                or not self.numero_parcelas
            ):
                return []

        except Exception:
            return []

        parcelas_existentes = (
            ParcelaProposta.query
            .filter_by(
                proposta_id=self.id,
                ativo=True,
            )
            .order_by(
                ParcelaProposta.numero_parcela,
                ParcelaProposta.id,
            )
            .all()
        )

        # D25F03-A5:
        # se qualquer parcela ja estiver ligada ao Financeiro,
        # o parcelamento vira documento historico protegido.
        if parcelas_existentes:
            from app.financeiro.financeiro_model import (
                LancamentoFinanceiro,
            )

            ids_parcelas = [
                parcela.id
                for parcela in parcelas_existentes
                if parcela.id is not None
            ]

            vinculado = (
                LancamentoFinanceiro.query
                .filter(
                    LancamentoFinanceiro
                    .proposta_id
                    == self.id,
                    LancamentoFinanceiro
                    .proposta_parcela_id
                    .in_(ids_parcelas),
                    LancamentoFinanceiro
                    .ativo
                    .is_(True),
                )
                .first()
            )

            if vinculado is not None:
                return parcelas_existentes

        # Ainda sem financeiro:
        # o fluxo legado pode reconstruir o parcelamento.
        ParcelaProposta.query.filter_by(
            proposta_id=self.id
        ).delete(
            synchronize_session=False
        )

        valor_total = Decimal(
            str(self.valor_total or 0)
        )

        percentual_entrada = Decimal(
            str(self.entrada or 0)
        )

        valor_entrada = (
            valor_total
            * percentual_entrada
            / Decimal("100")
        )

        valor_restante = (
            valor_total
            - valor_entrada
        )

        numero_parcelas = int(
            self.numero_parcelas or 1
        )

        valor_parcela = (
            valor_restante
            / numero_parcelas
            if numero_parcelas > 0
            else Decimal("0")
        )

        data_base = (
            self.data_primeira_parcela
            or date.today()
        )

        intervalo = int(
            self.intervalo_parcelas
            or 30
        )

        parcelas_criadas = []

        if valor_entrada > 0:
            entrada = ParcelaProposta(
                proposta_id=self.id,
                numero_parcela=0,
                valor_parcela=float(
                    valor_entrada
                ),
                data_vencimento=data_base,
                descricao=(
                    f"Entrada "
                    f"({percentual_entrada}%)"
                ),
                status="pendente",
            )

            db.session.add(entrada)
            parcelas_criadas.append(
                entrada
            )

        for numero in range(
            1,
            numero_parcelas + 1,
        ):
            data_vencimento = (
                data_base
                + timedelta(
                    days=intervalo * numero
                )
            )

            if numero == numero_parcelas:
                total_anterior = sum(
                    Decimal(
                        str(
                            parcela.valor_parcela
                            or 0
                        )
                    )
                    for parcela
                    in parcelas_criadas
                )

                valor_atual = (
                    valor_total
                    - total_anterior
                )

            else:
                valor_atual = valor_parcela

            parcela = ParcelaProposta(
                proposta_id=self.id,
                numero_parcela=numero,
                valor_parcela=float(
                    valor_atual
                ),
                data_vencimento=(
                    data_vencimento
                ),
                descricao=(
                    f"Parcela "
                    f"{numero}/"
                    f"{numero_parcelas}"
                ),
                status="pendente",
            )

            db.session.add(parcela)
            parcelas_criadas.append(
                parcela
            )

        db.session.commit()

        return parcelas_criadas

    def gerar_ordem_servico(self):
        """Converte proposta aprovada em OS preservando o financeiro.

        Regras D25F03:
        - uma proposta gera no maximo uma OS ativa;
        - recebiveis nascem na proposta, nao novamente na OS;
        - entrada tambem vira parcela tecnica da OS;
        - lancamentos existentes sao vinculados a OS/parcela correspondente;
        - recebimentos anteriores permanecem preservados.
        """
        if not self.pode_converter:
            return None

        from app.ordem_servico.ordem_servico_model import (
            OrdemServico,
            OrdemServicoItem,
            OrdemServicoProduto,
            OrdemServicoParcela,
        )
        from app.financeiro.financeiro_model import (
            LancamentoFinanceiro,
        )
        from app.financeiro.proposta_financeiro_service import (
            sincronizar_lancamentos_proposta,
        )

        # Idempotencia tambem no dominio:
        # nao depende apenas da protecao da rota HTTP.
        existente = OrdemServico.query.filter_by(
            proposta_id=self.id,
            ativo=True,
        ).first()

        if existente is not None:
            return existente

        # Garante que os recebiveis da proposta existem
        # ANTES da transferencia de responsabilidade para a OS.
        sincronizar_lancamentos_proposta(self)
        db.session.flush()

        parcelas_proposta = sorted(
            [
                parcela
                for parcela in (
                    getattr(
                        self,
                        "parcelas_pagamento",
                        [],
                    )
                    or []
                )
                if bool(
                    getattr(
                        parcela,
                        "ativo",
                        True,
                    )
                )
            ],
            key=lambda parcela: (
                int(
                    getattr(
                        parcela,
                        "numero_parcela",
                        0,
                    )
                    or 0
                ),
                parcela.id or 0,
            ),
        )

        parcela_entrada = next(
            (
                parcela
                for parcela in parcelas_proposta
                if int(
                    parcela.numero_parcela
                    or 0
                ) == 0
            ),
            None,
        )

        parcelas_normais = [
            parcela
            for parcela in parcelas_proposta
            if int(
                parcela.numero_parcela
                or 0
            ) > 0
        ]

        def parcela_recebida(parcela):
            status = (
                str(
                    getattr(
                        parcela,
                        "status",
                        "",
                    )
                    or ""
                )
                .strip()
                .lower()
            )

            return (
                status
                in {"pago", "recebido"}
                or getattr(
                    parcela,
                    "data_pagamento",
                    None,
                )
                is not None
            )

        valor_entrada = (
            float(
                parcela_entrada.valor_parcela
                or 0
            )
            if parcela_entrada is not None
            else 0.0
        )

        data_primeira_parcela = (
            parcelas_normais[0].data_vencimento
            if parcelas_normais
            else None
        )

        if parcelas_proposta:
            condicao_pgto = "parcelado"
        else:
            condicao_pgto = "a_vista"

        recebidas = sum(
            1
            for parcela in parcelas_proposta
            if parcela_recebida(parcela)
        )

        if not parcelas_proposta:
            status_pagamento = "pendente"
        elif recebidas == 0:
            status_pagamento = "pendente"
        elif recebidas == len(
            parcelas_proposta
        ):
            status_pagamento = "pago"
        else:
            status_pagamento = "parcial"

        nova_os = OrdemServico(
            numero=OrdemServico.gerar_proximo_numero(),
            proposta_id=self.id,
            cliente_id=self.cliente_id,
            titulo=(
                self.titulo
                or "Ordem de Servi?o"
            ),
            descricao=self.descricao or "",
            observacoes=(
                "OS gerada automaticamente da "
                f"Proposta {self.codigo}"
            ),
            tipo_os="comercial",
            status="pendente",
            prioridade=self.prioridade or "normal",
            data_abertura=date.today(),
            data_prevista=(
                date.today()
                + timedelta(days=7)
            ),
            solicitante=(
                self.cliente.nome
                if self.cliente
                else None
            ),
            tecnico_responsavel=(
                self.vendedor
                or "Juliano"
            ),
            tipo_servico="a_vista",
            valor_servico=0,
            valor_pecas=0,
            valor_desconto=float(
                self.desconto
                or 0
            ),
            valor_total=float(
                self.valor_total
                or 0
            ),
            prazo_garantia=90,
            condicao_pagamento=condicao_pgto,
            numero_parcelas=max(
                1,
                len(parcelas_normais),
            ),
            valor_entrada=valor_entrada,
            data_primeira_parcela=(
                data_primeira_parcela
            ),
            status_pagamento=(
                status_pagamento
            ),
        )

        db.session.add(nova_os)
        db.session.flush()

        # ----------------------------------------------------
        # ITENS
        # ----------------------------------------------------

        for produto in self.itens_produto:
            if not produto.ativo:
                continue

            item = OrdemServicoProduto(
                ordem_servico_id=nova_os.id,
                produto_id=produto.produto_id,
                descricao=produto.descricao,
                quantidade=produto.quantidade,
                valor_unitario=(
                    produto.valor_unitario
                ),
                valor_total=(
                    produto.valor_total
                ),
            )

            db.session.add(item)

        for servico in self.itens_servico:
            if not servico.ativo:
                continue

            item = OrdemServicoItem(
                ordem_servico_id=nova_os.id,
                descricao=servico.descricao,
                tipo_servico=(
                    servico.tipo_servico
                    or "fechado"
                ),
                quantidade=servico.quantidade,
                valor_unitario=(
                    servico.valor_unitario
                ),
                valor_total=(
                    servico.valor_total
                ),
            )

            db.session.add(item)

        db.session.flush()

        nova_os.atualizar_valores_automaticos()

        # ----------------------------------------------------
        # PARCELAS
        #
        # A entrada tambem e representada na OS como parcela 0.
        # Assim status_pagamento consegue enxergar:
        # entrada recebida + saldo pendente = PARCIAL.
        # ----------------------------------------------------

        os_por_proposta_parcela = {}

        for parcela_prop in parcelas_proposta:
            recebida = parcela_recebida(
                parcela_prop
            )

            os_parcela = OrdemServicoParcela(
                ordem_servico_id=nova_os.id,
                numero_parcela=(
                    parcela_prop.numero_parcela
                ),
                data_vencimento=(
                    parcela_prop.data_vencimento
                ),
                valor=(
                    parcela_prop.valor_parcela
                ),
                pago=recebida,
                data_pagamento=(
                    parcela_prop.data_pagamento
                    if recebida
                    else None
                ),
                ativo=True,
            )

            db.session.add(os_parcela)
            db.session.flush()

            os_por_proposta_parcela[
                parcela_prop.id
            ] = os_parcela

        # ----------------------------------------------------
        # TRANSFERENCIA DOS VINCULOS FINANCEIROS
        #
        # Nao cria novos LancamentoFinanceiro.
        # Apenas acrescenta a rastreabilidade da OS nos
        # recebiveis que ja nasceram na proposta.
        # ----------------------------------------------------

        lancamentos = (
            LancamentoFinanceiro.query
            .filter_by(
                proposta_id=self.id,
                ativo=True,
            )
            .all()
        )

        for lancamento in lancamentos:
            lancamento.ordem_servico_id = (
                nova_os.id
            )

            os_parcela = (
                os_por_proposta_parcela.get(
                    lancamento
                    .proposta_parcela_id
                )
            )

            if os_parcela is not None:
                lancamento.ordem_servico_parcela_id = (
                    os_parcela.id
                )

        db.session.flush()

        # Status da OS deve refletir todas as parcelas,
        # inclusive a entrada numero 0.
        if parcelas_proposta:
            if recebidas == 0:
                nova_os.status_pagamento = (
                    "pendente"
                )
            elif recebidas == len(
                parcelas_proposta
            ):
                nova_os.status_pagamento = (
                    "pago"
                )
            else:
                nova_os.status_pagamento = (
                    "parcial"
                )

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
