# -*- coding: utf-8 -*-
"""
ERP JSP - Modulo GERADORES
Consumiveis e equivalentes da Fase G2.

O vinculo com Produto e apenas referencial nesta fase.
Nenhuma movimentacao de estoque ocorre aqui.
"""

from sqlalchemy import CheckConstraint, Index

from app.extensoes import db
from app.models import BaseModel


class GeradorConsumivel(BaseModel):
    """Consumivel especificado para um grupo gerador."""

    __tablename__ = "gerador_consumiveis"

    TIPO_FILTRO_OLEO = "FILTRO_OLEO"
    TIPO_FILTRO_COMBUSTIVEL = "FILTRO_COMBUSTIVEL"
    TIPO_PRE_FILTRO_COMBUSTIVEL = "PRE_FILTRO_COMBUSTIVEL"
    TIPO_SEPARADOR_AGUA = "SEPARADOR_AGUA"
    TIPO_FILTRO_AR_PRIMARIO = "FILTRO_AR_PRIMARIO"
    TIPO_FILTRO_AR_SECUNDARIO = "FILTRO_AR_SECUNDARIO"
    TIPO_FILTRO_BLOW_BY = "FILTRO_BLOW_BY"
    TIPO_OLEO = "OLEO"
    TIPO_LIQUIDO_ARREFECIMENTO = "LIQUIDO_ARREFECIMENTO"
    TIPO_CORREIA = "CORREIA"
    TIPO_BATERIA = "BATERIA"
    TIPO_OUTRO = "OUTRO"

    TIPOS_VALIDOS = (
        TIPO_FILTRO_OLEO,
        TIPO_FILTRO_COMBUSTIVEL,
        TIPO_PRE_FILTRO_COMBUSTIVEL,
        TIPO_SEPARADOR_AGUA,
        TIPO_FILTRO_AR_PRIMARIO,
        TIPO_FILTRO_AR_SECUNDARIO,
        TIPO_FILTRO_BLOW_BY,
        TIPO_OLEO,
        TIPO_LIQUIDO_ARREFECIMENTO,
        TIPO_CORREIA,
        TIPO_BATERIA,
        TIPO_OUTRO,
    )

    gerador_id = db.Column(
        db.Integer,
        db.ForeignKey(
            "geradores.id",
            ondelete="RESTRICT",
        ),
        nullable=False,
        index=True,
    )

    produto_id = db.Column(
        db.Integer,
        db.ForeignKey(
            "produtos.id",
            ondelete="RESTRICT",
        ),
        nullable=True,
        index=True,
    )

    tipo = db.Column(
        db.String(40),
        nullable=False,
        index=True,
    )

    fabricante_original = db.Column(
        db.String(150),
        nullable=True,
    )

    referencia_original = db.Column(
        db.String(150),
        nullable=True,
        index=True,
    )

    descricao = db.Column(
        db.Text,
        nullable=True,
    )

    quantidade = db.Column(
        db.Numeric(12, 3),
        nullable=True,
    )

    unidade = db.Column(
        db.String(20),
        nullable=True,
    )

    observacoes = db.Column(
        db.Text,
        nullable=True,
    )

    gerador = db.relationship(
        "Gerador",
        backref=db.backref(
            "consumiveis",
            lazy="dynamic",
        ),
    )

    produto = db.relationship(
        "Produto",
        backref=db.backref(
            "gerador_consumiveis",
            lazy="dynamic",
        ),
    )

    __table_args__ = (
        CheckConstraint(
            "tipo IN ("
            "'FILTRO_OLEO', "
            "'FILTRO_COMBUSTIVEL', "
            "'PRE_FILTRO_COMBUSTIVEL', "
            "'SEPARADOR_AGUA', "
            "'FILTRO_AR_PRIMARIO', "
            "'FILTRO_AR_SECUNDARIO', "
            "'FILTRO_BLOW_BY', "
            "'OLEO', "
            "'LIQUIDO_ARREFECIMENTO', "
            "'CORREIA', "
            "'BATERIA', "
            "'OUTRO'"
            ")",
            name="ck_gerador_consumivel_tipo",
        ),
        CheckConstraint(
            "quantidade IS NULL OR quantidade > 0",
            name="ck_gerador_consumivel_quantidade",
        ),
        Index(
            "ix_gerador_consumiveis_gerador_tipo",
            "gerador_id",
            "tipo",
        ),
        Index(
            "ix_gerador_consumiveis_gerador_ativo",
            "gerador_id",
            "ativo",
        ),
    )

    def __repr__(self):
        return (
            f"<GeradorConsumivel "
            f"id={self.id} "
            f"gerador={self.gerador_id} "
            f"tipo={self.tipo!r}>"
        )


class GeradorConsumivelEquivalente(BaseModel):
    """Referencia equivalente de um consumivel do gerador."""

    __tablename__ = "gerador_consumivel_equivalentes"

    consumivel_id = db.Column(
        db.Integer,
        db.ForeignKey(
            "gerador_consumiveis.id",
            ondelete="RESTRICT",
        ),
        nullable=False,
        index=True,
    )

    fabricante = db.Column(
        db.String(150),
        nullable=True,
    )

    referencia = db.Column(
        db.String(150),
        nullable=False,
        index=True,
    )

    descricao = db.Column(
        db.Text,
        nullable=True,
    )

    observacoes = db.Column(
        db.Text,
        nullable=True,
    )

    consumivel = db.relationship(
        "GeradorConsumivel",
        backref=db.backref(
            "equivalentes",
            lazy="dynamic",
        ),
    )

    __table_args__ = (
        Index(
            "ix_gerador_consumivel_equiv_consumivel_ativo",
            "consumivel_id",
            "ativo",
        ),
    )

    def __repr__(self):
        return (
            f"<GeradorConsumivelEquivalente "
            f"id={self.id} "
            f"consumivel={self.consumivel_id} "
            f"referencia={self.referencia!r}>"
        )
