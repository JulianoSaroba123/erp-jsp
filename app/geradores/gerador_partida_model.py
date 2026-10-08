# -*- coding: utf-8 -*-
"""
ERP JSP - Modulo GERADORES
Sistema de partida da Fase G2.

Nesta etapa:
- Bateria / banco de baterias
- Carregador de bateria

As medicoes representam o estado atual da ficha tecnica.
Historico de medicoes sera tratado em fase posterior.
"""

from sqlalchemy import CheckConstraint, Index

from app.extensoes import db
from app.models import BaseModel


class GeradorBateria(BaseModel):
    """Bateria ou banco de baterias associado ao gerador."""

    __tablename__ = "gerador_baterias"

    gerador_id = db.Column(
        db.Integer,
        db.ForeignKey(
            "geradores.id",
            ondelete="RESTRICT",
        ),
        nullable=False,
        index=True,
    )

    quantidade = db.Column(
        db.Integer,
        nullable=True,
    )

    tensao_nominal_v = db.Column(
        db.Numeric(10, 2),
        nullable=True,
    )

    capacidade_ah = db.Column(
        db.Numeric(12, 2),
        nullable=True,
    )

    fabricante = db.Column(
        db.String(150),
        nullable=True,
    )

    modelo = db.Column(
        db.String(150),
        nullable=True,
    )

    data_instalacao = db.Column(
        db.Date,
        nullable=True,
    )

    tensao_repouso_v = db.Column(
        db.Numeric(10, 2),
        nullable=True,
    )

    tensao_partida_v = db.Column(
        db.Numeric(10, 2),
        nullable=True,
    )

    observacoes = db.Column(
        db.Text,
        nullable=True,
    )

    gerador = db.relationship(
        "Gerador",
        backref=db.backref(
            "baterias",
            lazy="dynamic",
        ),
    )

    __table_args__ = (
        CheckConstraint(
            "quantidade IS NULL OR quantidade > 0",
            name="ck_gerador_bateria_quantidade",
        ),
        CheckConstraint(
            "tensao_nominal_v IS NULL "
            "OR tensao_nominal_v >= 0",
            name="ck_gerador_bateria_tensao_nominal",
        ),
        CheckConstraint(
            "capacidade_ah IS NULL "
            "OR capacidade_ah >= 0",
            name="ck_gerador_bateria_capacidade",
        ),
        CheckConstraint(
            "tensao_repouso_v IS NULL "
            "OR tensao_repouso_v >= 0",
            name="ck_gerador_bateria_repouso",
        ),
        CheckConstraint(
            "tensao_partida_v IS NULL "
            "OR tensao_partida_v >= 0",
            name="ck_gerador_bateria_partida",
        ),
        Index(
            "ix_gerador_baterias_gerador_ativo",
            "gerador_id",
            "ativo",
        ),
    )

    def __repr__(self):
        return (
            f"<GeradorBateria "
            f"id={self.id} "
            f"gerador={self.gerador_id} "
            f"modelo={self.modelo!r}>"
        )


class GeradorCarregador(BaseModel):
    """Carregador de bateria associado ao grupo gerador."""

    __tablename__ = "gerador_carregadores"

    gerador_id = db.Column(
        db.Integer,
        db.ForeignKey(
            "geradores.id",
            ondelete="RESTRICT",
        ),
        nullable=False,
        index=True,
    )

    fabricante = db.Column(
        db.String(150),
        nullable=True,
    )

    modelo = db.Column(
        db.String(150),
        nullable=True,
    )

    tensao_nominal_v = db.Column(
        db.String(100),
        nullable=True,
    )

    corrente_nominal_a = db.Column(
        db.Numeric(10, 2),
        nullable=True,
    )

    tensao_medida_v = db.Column(
        db.Numeric(10, 2),
        nullable=True,
    )

    observacoes = db.Column(
        db.Text,
        nullable=True,
    )

    gerador = db.relationship(
        "Gerador",
        backref=db.backref(
            "carregadores",
            lazy="dynamic",
        ),
    )

    __table_args__ = (
        CheckConstraint(
            "corrente_nominal_a IS NULL "
            "OR corrente_nominal_a >= 0",
            name="ck_gerador_carregador_corrente",
        ),
        CheckConstraint(
            "tensao_medida_v IS NULL "
            "OR tensao_medida_v >= 0",
            name="ck_gerador_carregador_medida",
        ),
        Index(
            "ix_gerador_carregadores_gerador_ativo",
            "gerador_id",
            "ativo",
        ),
    )

    def __repr__(self):
        return (
            f"<GeradorCarregador "
            f"id={self.id} "
            f"gerador={self.gerador_id} "
            f"modelo={self.modelo!r}>"
        )
