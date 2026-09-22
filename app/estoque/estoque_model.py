# -*- coding: utf-8 -*-
"""Modelos de movimentacao de estoque."""

from decimal import Decimal

from sqlalchemy import CheckConstraint, UniqueConstraint

from app.extensoes import db
from app.models import BaseModel


class MovimentacaoEstoque(BaseModel):
    """Registro auditavel de entrada/saida de estoque."""

    __tablename__ = "movimentacoes_estoque"

    TIPO_ENTRADA = "ENTRADA"
    TIPO_SAIDA = "SAIDA"

    ORIGEM_PEDIDO = "PEDIDO"

    produto_id = db.Column(
        db.Integer,
        db.ForeignKey(
            "produtos.id",
            ondelete="RESTRICT",
        ),
        nullable=False,
        index=True,
    )

    pedido_id = db.Column(
        db.Integer,
        db.ForeignKey(
            "pedidos.id",
            ondelete="RESTRICT",
        ),
        nullable=True,
        index=True,
    )

    tipo = db.Column(
        db.String(20),
        nullable=False,
        index=True,
    )

    origem = db.Column(
        db.String(30),
        nullable=False,
        index=True,
    )

    quantidade = db.Column(
        db.Numeric(12, 3),
        nullable=False,
    )

    estoque_anterior = db.Column(
        db.Numeric(12, 3),
        nullable=False,
    )

    estoque_posterior = db.Column(
        db.Numeric(12, 3),
        nullable=False,
    )

    documento = db.Column(
        db.String(50),
        nullable=True,
        index=True,
    )

    observacoes = db.Column(
        db.Text,
        nullable=True,
    )

    produto = db.relationship(
        "Produto",
        backref=db.backref(
            "movimentacoes_estoque",
            lazy="dynamic",
        ),
    )

    pedido = db.relationship(
        "Pedido",
        backref=db.backref(
            "movimentacoes_estoque",
            lazy="dynamic",
        ),
    )

    __table_args__ = (
        CheckConstraint(
            "tipo IN ('ENTRADA', 'SAIDA')",
            name="ck_mov_estoque_tipo",
        ),
        CheckConstraint(
            "quantidade > 0",
            name="ck_mov_estoque_quantidade_positiva",
        ),
        CheckConstraint(
            "estoque_anterior >= 0",
            name="ck_mov_estoque_saldo_anterior",
        ),
        CheckConstraint(
            "estoque_posterior >= 0",
            name="ck_mov_estoque_saldo_posterior",
        ),
        UniqueConstraint(
            "pedido_id",
            "produto_id",
            "tipo",
            "origem",
            name="uq_mov_estoque_pedido_produto_tipo_origem",
        ),
    )

    def __repr__(self):
        return (
            f"<MovimentacaoEstoque "
            f"{self.tipo} produto={self.produto_id} "
            f"quantidade={self.quantidade}>"
        )
