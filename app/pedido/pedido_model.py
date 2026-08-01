# -*- coding: utf-8 -*-
"""
ERP JSP v3.0 - Model de Pedidos
================================

Fundacao do dominio Pedido para evolucao comercial sem impacto
nos fluxos atuais Proposta -> OS e OS -> Financeiro.
"""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import CheckConstraint, event

from app.extensoes import db
from app.models import BaseModel


class Pedido(BaseModel):
    __tablename__ = "pedidos"

    STATUS_RASCUNHO = "RASCUNHO"
    STATUS_AGUARDANDO_CONFIRMACAO = "AGUARDANDO_CONFIRMACAO"
    STATUS_CONFIRMADO = "CONFIRMADO"
    STATUS_EM_EXECUCAO = "EM_EXECUCAO"
    STATUS_CONCLUIDO = "CONCLUIDO"
    STATUS_CANCELADO = "CANCELADO"

    STATUS_CHOICES = [
        (STATUS_RASCUNHO, "Rascunho"),
        (STATUS_AGUARDANDO_CONFIRMACAO, "Aguardando Confirmacao"),
        (STATUS_CONFIRMADO, "Confirmado"),
        (STATUS_EM_EXECUCAO, "Em Execucao"),
        (STATUS_CONCLUIDO, "Concluido"),
        (STATUS_CANCELADO, "Cancelado"),
    ]
    STATUS_LABELS = dict(STATUS_CHOICES)

    numero = db.Column(db.String(20), unique=True, nullable=False, index=True)

    cliente_id = db.Column(
        db.Integer,
        db.ForeignKey("clientes.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    proposta_id = db.Column(
        db.Integer,
        db.ForeignKey("propostas.id", ondelete="RESTRICT"),
        nullable=True,
        unique=True,
        index=True,
    )

    data_pedido = db.Column(db.Date, nullable=False, default=date.today)
    status = db.Column(db.String(30), nullable=False, default=STATUS_RASCUNHO, index=True)
    responsavel = db.Column(db.String(100))
    solicitante = db.Column(db.String(150))
    telefone_contato = db.Column(db.String(25))
    email_contato = db.Column(db.String(150))
    prazo_previsto = db.Column(db.Date)
    condicoes_pagamento = db.Column(db.Text)

    subtotal = db.Column(db.Numeric(12, 2), nullable=False, default=Decimal("0.00"))
    desconto = db.Column(db.Numeric(12, 2), nullable=False, default=Decimal("0.00"))
    valor_total = db.Column(db.Numeric(12, 2), nullable=False, default=Decimal("0.00"))

    observacoes = db.Column(db.Text)

    cliente = db.relationship("Cliente", backref=db.backref("pedidos", lazy="dynamic"))
    proposta = db.relationship("Proposta", backref=db.backref("pedido", uselist=False))

    __table_args__ = (
        CheckConstraint(
            "status IN ('RASCUNHO', 'AGUARDANDO_CONFIRMACAO', 'CONFIRMADO', 'EM_EXECUCAO', 'CONCLUIDO', 'CANCELADO')",
            name="ck_pedidos_status",
        ),
        CheckConstraint("subtotal >= 0", name="ck_pedidos_subtotal_nao_negativo"),
        CheckConstraint("desconto >= 0", name="ck_pedidos_desconto_nao_negativo"),
        CheckConstraint("valor_total >= 0", name="ck_pedidos_valor_total_nao_negativo"),
    )

    def __init__(self, **kwargs):
        if not kwargs.get("numero"):
            kwargs["numero"] = self.gerar_proximo_numero()
        super().__init__(**kwargs)

    def __repr__(self):
        return f"<Pedido {self.numero}>"

    @property
    def status_label(self):
        return self.STATUS_LABELS.get(self.status, self.status)

    @classmethod
    def gerar_proximo_numero(cls):
        ultimo = cls.query.filter(cls.numero.like("PED%")).order_by(cls.numero.desc()).first()
        if not ultimo:
            return "PED0001"

        sufixo = str(ultimo.numero or "").replace("PED", "", 1)
        try:
            proximo = int(sufixo) + 1
        except (ValueError, TypeError):
            proximo = 1
        return f"PED{proximo:04d}"

    def recalcular_totais(self):
        subtotal = Decimal("0.00")
        for item in self.itens.order_by(PedidoItem.ordem.asc(), PedidoItem.id.asc()).all():
            subtotal += Decimal(str(item.valor_total or 0))

        desconto = Decimal(str(self.desconto or 0)).quantize(Decimal("0.01"))
        total = (subtotal - desconto).quantize(Decimal("0.01"))
        if total < Decimal("0.00"):
            total = Decimal("0.00")

        self.subtotal = subtotal.quantize(Decimal("0.01"))
        self.valor_total = total

    def validar_valores(self):
        subtotal = Decimal(str(self.subtotal or 0)).quantize(Decimal("0.01"))
        desconto = Decimal(str(self.desconto or 0)).quantize(Decimal("0.01"))
        valor_total = Decimal(str(self.valor_total or 0)).quantize(Decimal("0.01"))

        if subtotal < Decimal("0.00"):
            raise ValueError("subtotal do pedido nao pode ser negativo")
        if desconto < Decimal("0.00"):
            raise ValueError("desconto do pedido nao pode ser negativo")
        if valor_total < Decimal("0.00"):
            raise ValueError("valor_total do pedido nao pode ser negativo")

        self.subtotal = subtotal
        self.desconto = desconto
        self.valor_total = valor_total


class PedidoItem(BaseModel):
    __tablename__ = "pedido_itens"

    TIPO_PRODUTO = "PRODUTO"
    TIPO_SERVICO = "SERVICO"

    pedido_id = db.Column(
        db.Integer,
        db.ForeignKey("pedidos.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    tipo_item = db.Column(db.String(20), nullable=False, index=True)
    produto_id = db.Column(db.Integer, db.ForeignKey("produtos.id", ondelete="RESTRICT"), nullable=True)
    servico_id = db.Column(db.Integer, db.ForeignKey("servicos.id", ondelete="RESTRICT"), nullable=True)

    descricao = db.Column(db.String(255), nullable=False)
    quantidade = db.Column(db.Numeric(12, 3), nullable=False, default=Decimal("1.000"))
    valor_unitario = db.Column(db.Numeric(12, 2), nullable=False, default=Decimal("0.00"))
    desconto = db.Column(db.Numeric(12, 2), nullable=False, default=Decimal("0.00"))
    valor_total = db.Column(db.Numeric(12, 2), nullable=False, default=Decimal("0.00"))
    ordem = db.Column(db.Integer, nullable=False, default=0)

    pedido = db.relationship(
        "Pedido",
        backref=db.backref(
            "itens",
            lazy="dynamic",
            cascade="all, delete-orphan",
            passive_deletes=True,
            order_by="PedidoItem.ordem",
        ),
    )
    produto = db.relationship("Produto", backref=db.backref("pedido_itens", lazy="dynamic"))
    servico = db.relationship("Servico", backref=db.backref("pedido_itens", lazy="dynamic"))

    __table_args__ = (
        CheckConstraint("tipo_item IN ('PRODUTO', 'SERVICO')", name="ck_pedido_itens_tipo_item"),
        CheckConstraint(
            "((produto_id IS NOT NULL AND servico_id IS NULL) OR (produto_id IS NULL AND servico_id IS NOT NULL))",
            name="ck_pedido_itens_referencia_exclusiva",
        ),
        CheckConstraint("quantidade > 0", name="ck_pedido_itens_quantidade_positiva"),
        CheckConstraint("valor_unitario >= 0", name="ck_pedido_itens_valor_unitario_nao_negativo"),
        CheckConstraint("desconto >= 0", name="ck_pedido_itens_desconto_nao_negativo"),
        CheckConstraint("valor_total >= 0", name="ck_pedido_itens_valor_total_nao_negativo"),
    )

    def __repr__(self):
        return f"<PedidoItem {self.tipo_item} #{self.id}>"

    def validar_referencia(self):
        tipo = str(self.tipo_item or "").strip().upper()
        self.tipo_item = tipo

        tem_produto = self.produto_id is not None
        tem_servico = self.servico_id is not None

        if tem_produto == tem_servico:
            raise ValueError("PedidoItem deve referenciar produto ou servico, nunca ambos/nenhum")

        if tipo == self.TIPO_PRODUTO and not tem_produto:
            raise ValueError("PedidoItem PRODUTO exige produto_id")
        if tipo == self.TIPO_SERVICO and not tem_servico:
            raise ValueError("PedidoItem SERVICO exige servico_id")

        if tipo not in {self.TIPO_PRODUTO, self.TIPO_SERVICO}:
            raise ValueError("tipo_item invalido para PedidoItem")

    def preencher_snapshot_padrao(self):
        if self.tipo_item == self.TIPO_PRODUTO and self.produto is not None:
            if not self.descricao:
                self.descricao = self.produto.nome
            if self.valor_unitario is None:
                self.valor_unitario = self.produto.preco_venda

        if self.tipo_item == self.TIPO_SERVICO and self.servico is not None:
            if not self.descricao:
                self.descricao = self.servico.nome
            if self.valor_unitario is None:
                self.valor_unitario = self.servico.valor_base

    def calcular_total(self):
        quantidade = Decimal(str(self.quantidade or 0))
        valor_unitario = Decimal(str(self.valor_unitario or 0))
        desconto = Decimal(str(self.desconto or 0))

        if quantidade <= Decimal("0"):
            raise ValueError("quantidade do item deve ser maior que zero")
        if valor_unitario < Decimal("0.00"):
            raise ValueError("valor_unitario do item nao pode ser negativo")
        if desconto < Decimal("0.00"):
            raise ValueError("desconto do item nao pode ser negativo")

        total = (quantidade * valor_unitario) - desconto
        if total < Decimal("0.00"):
            raise ValueError("valor_total do item nao pode ser negativo")

        self.quantidade = quantidade
        self.valor_unitario = valor_unitario.quantize(Decimal("0.01"))
        self.desconto = desconto.quantize(Decimal("0.01"))
        self.valor_total = total.quantize(Decimal("0.01"))


@event.listens_for(Pedido, "before_insert")
@event.listens_for(Pedido, "before_update")
def _validar_valores_pedido(_mapper, _connection, target):
    target.validar_valores()


@event.listens_for(PedidoItem, "before_insert")
@event.listens_for(PedidoItem, "before_update")
def _validar_e_calcular_pedido_item(_mapper, _connection, target):
    target.validar_referencia()
    target.preencher_snapshot_padrao()
    if not target.descricao:
        raise ValueError("descricao do item e obrigatoria")
    target.calcular_total()
