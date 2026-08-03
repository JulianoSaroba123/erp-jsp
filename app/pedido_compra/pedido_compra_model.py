# -*- coding: utf-8 -*-

from __future__ import annotations

from datetime import date
from decimal import Decimal

from sqlalchemy import CheckConstraint, event

from app.extensoes import db
from app.models import BaseModel


class PedidoCompra(BaseModel):
    __tablename__ = "pedidos_compra"

    STATUS_RASCUNHO = "RASCUNHO"
    STATUS_AGUARDANDO_APROVACAO = "AGUARDANDO_APROVACAO"
    STATUS_APROVADO = "APROVADO"
    STATUS_ENVIADO_FORNECEDOR = "ENVIADO_FORNECEDOR"
    STATUS_RECEBIDO_PARCIAL = "RECEBIDO_PARCIAL"
    STATUS_RECEBIDO = "RECEBIDO"
    STATUS_CANCELADO = "CANCELADO"

    FINALIDADE_ESTOQUE = "ESTOQUE"
    FINALIDADE_ORDEM_SERVICO = "ORDEM_SERVICO"
    FINALIDADE_PEDIDO_VENDA = "PEDIDO_VENDA"
    FINALIDADE_ADMINISTRATIVO = "ADMINISTRATIVO"

    STATUS_CHOICES = [
        (STATUS_RASCUNHO, "Rascunho"),
        (STATUS_AGUARDANDO_APROVACAO, "Aguardando aprovacao"),
        (STATUS_APROVADO, "Aprovado"),
        (STATUS_ENVIADO_FORNECEDOR, "Enviado ao fornecedor"),
        (STATUS_RECEBIDO_PARCIAL, "Recebido parcial"),
        (STATUS_RECEBIDO, "Recebido"),
        (STATUS_CANCELADO, "Cancelado"),
    ]
    STATUS_LABELS = dict(STATUS_CHOICES)

    FINALIDADE_CHOICES = [
        (FINALIDADE_ESTOQUE, "Estoque"),
        (FINALIDADE_ORDEM_SERVICO, "Ordem de Servico"),
        (FINALIDADE_PEDIDO_VENDA, "Pedido de Venda"),
        (FINALIDADE_ADMINISTRATIVO, "Administrativo"),
    ]
    FINALIDADE_LABELS = dict(FINALIDADE_CHOICES)

    numero = db.Column(db.String(20), unique=True, nullable=False, index=True)
    fornecedor_id = db.Column(db.Integer, db.ForeignKey("fornecedores.id", ondelete="RESTRICT"), nullable=False, index=True)
    ordem_servico_id = db.Column(db.Integer, db.ForeignKey("ordem_servico.id", ondelete="RESTRICT"), nullable=True, index=True)
    pedido_venda_id = db.Column(db.Integer, db.ForeignKey("pedidos.id", ondelete="RESTRICT"), nullable=True, index=True)

    data_emissao = db.Column(db.Date, nullable=False, default=date.today)
    previsao_entrega = db.Column(db.Date, nullable=True)
    solicitante = db.Column(db.String(150), nullable=True)
    responsavel_compra = db.Column(db.String(150), nullable=True)
    condicao_pagamento = db.Column(db.Text, nullable=True)
    observacoes = db.Column(db.Text, nullable=True)
    finalidade = db.Column(db.String(30), nullable=False, default=FINALIDADE_ESTOQUE, index=True)
    status = db.Column(db.String(30), nullable=False, default=STATUS_RASCUNHO, index=True)
    subtotal = db.Column(db.Numeric(12, 2), nullable=False, default=Decimal("0.00"))
    desconto = db.Column(db.Numeric(12, 2), nullable=False, default=Decimal("0.00"))
    total = db.Column(db.Numeric(12, 2), nullable=False, default=Decimal("0.00"))

    fornecedor = db.relationship("Fornecedor", backref=db.backref("pedidos_compra", lazy="dynamic"))
    ordem_servico = db.relationship("OrdemServico", backref=db.backref("pedidos_compra", lazy="dynamic"))
    pedido_venda = db.relationship("Pedido", backref=db.backref("pedidos_compra_relacionados", lazy="dynamic"))

    __table_args__ = (
        CheckConstraint(
            "status IN ('RASCUNHO', 'AGUARDANDO_APROVACAO', 'APROVADO', 'ENVIADO_FORNECEDOR', 'RECEBIDO_PARCIAL', 'RECEBIDO', 'CANCELADO')",
            name="ck_pedidos_compra_status",
        ),
        CheckConstraint(
            "finalidade IN ('ESTOQUE', 'ORDEM_SERVICO', 'PEDIDO_VENDA', 'ADMINISTRATIVO')",
            name="ck_pedidos_compra_finalidade",
        ),
        CheckConstraint("subtotal >= 0", name="ck_pedidos_compra_subtotal_nao_negativo"),
        CheckConstraint("desconto >= 0", name="ck_pedidos_compra_desconto_nao_negativo"),
        CheckConstraint("total >= 0", name="ck_pedidos_compra_total_nao_negativo"),
    )

    def __init__(self, **kwargs):
        if not kwargs.get("numero"):
            kwargs["numero"] = self.gerar_proximo_numero()
        super().__init__(**kwargs)

    @property
    def status_label(self):
        return self.STATUS_LABELS.get(self.status, self.status)

    @property
    def finalidade_label(self):
        return self.FINALIDADE_LABELS.get(self.finalidade, self.finalidade)

    @classmethod
    def gerar_proximo_numero(cls):
        ultimo = cls.query.filter(cls.numero.like("PC%")).order_by(cls.numero.desc()).first()
        if not ultimo:
            return "PC0001"

        sufixo = str(ultimo.numero or "").replace("PC", "", 1)
        try:
            proximo = int(sufixo) + 1
        except (TypeError, ValueError):
            proximo = 1
        return f"PC{proximo:04d}"

    def recalcular_totais(self):
        subtotal = Decimal("0.00")
        for item in self.itens.order_by(PedidoCompraItem.ordem.asc(), PedidoCompraItem.id.asc()).all():
            subtotal += Decimal(str(item.valor_total or 0))

        desconto = Decimal(str(self.desconto or 0)).quantize(Decimal("0.01"))
        total = (subtotal - desconto).quantize(Decimal("0.01"))
        if total < Decimal("0.00"):
            total = Decimal("0.00")

        self.subtotal = subtotal.quantize(Decimal("0.01"))
        self.total = total

    def validar_valores(self):
        subtotal = Decimal(str(self.subtotal or 0)).quantize(Decimal("0.01"))
        desconto = Decimal(str(self.desconto or 0)).quantize(Decimal("0.01"))
        total = Decimal(str(self.total or 0)).quantize(Decimal("0.01"))

        if self.status not in dict(self.STATUS_CHOICES):
            raise ValueError("status do pedido de compra invalido")
        if self.finalidade not in dict(self.FINALIDADE_CHOICES):
            raise ValueError("finalidade do pedido de compra invalida")
        if subtotal < Decimal("0.00"):
            raise ValueError("subtotal do pedido de compra nao pode ser negativo")
        if desconto < Decimal("0.00"):
            raise ValueError("desconto do pedido de compra nao pode ser negativo")
        if total < Decimal("0.00"):
            raise ValueError("total do pedido de compra nao pode ser negativo")

        self.subtotal = subtotal
        self.desconto = desconto
        self.total = total

    def pode_receber(self):
        return self.status in {
            self.STATUS_APROVADO,
            self.STATUS_ENVIADO_FORNECEDOR,
            self.STATUS_RECEBIDO_PARCIAL,
        }

    def atualizar_status_recebimento(self):
        itens = self.itens.filter(PedidoCompraItem.ativo.is_(True)).all()
        if not itens:
            return

        total_comprado = sum((Decimal(str(item.quantidade_comprada or 0)) for item in itens), Decimal("0.000"))
        total_recebido = sum((Decimal(str(item.quantidade_recebida or 0)) for item in itens), Decimal("0.000"))

        if total_recebido <= Decimal("0.000"):
            return
        if total_recebido >= total_comprado:
            self.status = self.STATUS_RECEBIDO
        else:
            self.status = self.STATUS_RECEBIDO_PARCIAL


class PedidoCompraItem(BaseModel):
    __tablename__ = "pedido_compra_itens"

    TIPO_PRODUTO = "PRODUTO"
    TIPO_SERVICO = "SERVICO"

    pedido_compra_id = db.Column(db.Integer, db.ForeignKey("pedidos_compra.id", ondelete="CASCADE"), nullable=False, index=True)
    tipo_item = db.Column(db.String(20), nullable=False, index=True)
    produto_id = db.Column(db.Integer, db.ForeignKey("produtos.id", ondelete="RESTRICT"), nullable=True)
    servico_id = db.Column(db.Integer, db.ForeignKey("servicos.id", ondelete="RESTRICT"), nullable=True)
    descricao = db.Column(db.String(255), nullable=False)
    unidade = db.Column(db.String(20), nullable=True)
    quantidade_comprada = db.Column(db.Numeric(12, 3), nullable=False, default=Decimal("1.000"))
    quantidade_recebida = db.Column(db.Numeric(12, 3), nullable=False, default=Decimal("0.000"))
    valor_unitario = db.Column(db.Numeric(12, 2), nullable=False, default=Decimal("0.00"))
    desconto = db.Column(db.Numeric(12, 2), nullable=False, default=Decimal("0.00"))
    valor_total = db.Column(db.Numeric(12, 2), nullable=False, default=Decimal("0.00"))
    ordem = db.Column(db.Integer, nullable=False, default=0)

    pedido_compra = db.relationship(
        "PedidoCompra",
        backref=db.backref(
            "itens",
            lazy="dynamic",
            cascade="all, delete-orphan",
            passive_deletes=True,
            order_by="PedidoCompraItem.ordem",
        ),
    )
    produto = db.relationship("Produto", backref=db.backref("pedido_compra_itens", lazy="dynamic"))
    servico = db.relationship("Servico", backref=db.backref("pedido_compra_itens", lazy="dynamic"))

    __table_args__ = (
        CheckConstraint("tipo_item IN ('PRODUTO', 'SERVICO')", name="ck_pedido_compra_itens_tipo_item"),
        CheckConstraint(
            "((produto_id IS NOT NULL AND servico_id IS NULL) OR (produto_id IS NULL AND servico_id IS NOT NULL))",
            name="ck_pedido_compra_itens_referencia_exclusiva",
        ),
        CheckConstraint("quantidade_comprada > 0", name="ck_pedido_compra_itens_quantidade_positiva"),
        CheckConstraint("quantidade_recebida >= 0", name="ck_pedido_compra_itens_quantidade_recebida_nao_negativa"),
        CheckConstraint("valor_unitario >= 0", name="ck_pedido_compra_itens_valor_unitario_nao_negativo"),
        CheckConstraint("desconto >= 0", name="ck_pedido_compra_itens_desconto_nao_negativo"),
        CheckConstraint("valor_total >= 0", name="ck_pedido_compra_itens_valor_total_nao_negativo"),
    )

    def validar_referencia(self):
        tipo = str(self.tipo_item or "").strip().upper()
        self.tipo_item = tipo

        tem_produto = self.produto_id is not None
        tem_servico = self.servico_id is not None
        if tem_produto == tem_servico:
            raise ValueError("PedidoCompraItem deve referenciar produto ou servico, nunca ambos/nenhum")
        if tipo == self.TIPO_PRODUTO and not tem_produto:
            raise ValueError("PedidoCompraItem PRODUTO exige produto_id")
        if tipo == self.TIPO_SERVICO and not tem_servico:
            raise ValueError("PedidoCompraItem SERVICO exige servico_id")
        if tipo not in {self.TIPO_PRODUTO, self.TIPO_SERVICO}:
            raise ValueError("tipo_item invalido para PedidoCompraItem")

    def preencher_snapshot_padrao(self):
        if self.tipo_item == self.TIPO_PRODUTO and self.produto is not None:
            if not self.descricao:
                self.descricao = self.produto.nome
            if not self.unidade:
                self.unidade = self.produto.unidade_medida or "UN"
            if self.valor_unitario is None:
                self.valor_unitario = self.produto.preco_custo or self.produto.preco_venda

        if self.tipo_item == self.TIPO_SERVICO and self.servico is not None:
            if not self.descricao:
                self.descricao = self.servico.nome
            if not self.unidade:
                self.unidade = "SV"
            if self.valor_unitario is None:
                self.valor_unitario = self.servico.valor_base

    def calcular_total(self):
        quantidade_comprada = Decimal(str(self.quantidade_comprada or 0))
        quantidade_recebida = Decimal(str(self.quantidade_recebida or 0))
        valor_unitario = Decimal(str(self.valor_unitario or 0))
        desconto = Decimal(str(self.desconto or 0))

        if quantidade_comprada <= Decimal("0"):
            raise ValueError("quantidade comprada deve ser maior que zero")
        if quantidade_recebida < Decimal("0"):
            raise ValueError("quantidade recebida nao pode ser negativa")
        if quantidade_recebida > quantidade_comprada:
            raise ValueError("quantidade recebida nao pode exceder a quantidade comprada")
        if valor_unitario < Decimal("0.00"):
            raise ValueError("valor_unitario nao pode ser negativo")
        if desconto < Decimal("0.00"):
            raise ValueError("desconto nao pode ser negativo")

        total = (quantidade_comprada * valor_unitario) - desconto
        if total < Decimal("0.00"):
            raise ValueError("valor_total nao pode ser negativo")

        self.quantidade_comprada = quantidade_comprada
        self.quantidade_recebida = quantidade_recebida
        self.valor_unitario = valor_unitario.quantize(Decimal("0.01"))
        self.desconto = desconto.quantize(Decimal("0.01"))
        self.valor_total = total.quantize(Decimal("0.01"))

    def registrar_recebimento(self, quantidade):
        incremento = Decimal(str(quantidade or 0))
        if incremento < Decimal("0"):
            raise ValueError("quantidade recebida nao pode ser negativa")

        nova_quantidade = Decimal(str(self.quantidade_recebida or 0)) + incremento
        if nova_quantidade > Decimal(str(self.quantidade_comprada or 0)):
            raise ValueError("quantidade recebida nao pode exceder a quantidade comprada")

        self.quantidade_recebida = nova_quantidade


@event.listens_for(PedidoCompra, "before_insert")
@event.listens_for(PedidoCompra, "before_update")
def _validar_pedido_compra(_mapper, _connection, target):
    target.validar_valores()


@event.listens_for(PedidoCompraItem, "before_insert")
@event.listens_for(PedidoCompraItem, "before_update")
def _validar_item_pedido_compra(_mapper, _connection, target):
    target.validar_referencia()
    target.preencher_snapshot_padrao()
    if not target.descricao:
        raise ValueError("descricao do item e obrigatoria")
    target.calcular_total()
