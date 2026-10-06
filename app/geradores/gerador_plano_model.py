# -*- coding: utf-8 -*-
"""
ERP JSP - Modulo GERADORES
Planos de manutencao da Fase G3.

A execucao da manutencao e os checklists pertencem
as fases seguintes. Aqui ficam somente:

- definicao do plano;
- heranca entre planos;
- periodicidade;
- vinculo do plano ao gerador;
- bases para programacao por data e horimetro.
"""

from sqlalchemy import CheckConstraint, Index

from app.extensoes import db
from app.models import BaseModel


class PlanoManutencao(BaseModel):
    """Definicao reutilizavel de um plano de manutencao."""

    __tablename__ = "planos_manutencao"

    TIPO_BASICA = "BASICA"
    TIPO_INTERMEDIARIA = "INTERMEDIARIA"
    TIPO_AVANCADA = "AVANCADA"

    TIPOS_VALIDOS = (
        TIPO_BASICA,
        TIPO_INTERMEDIARIA,
        TIPO_AVANCADA,
    )

    codigo = db.Column(
        db.String(50),
        nullable=False,
        unique=True,
        index=True,
    )

    nome = db.Column(
        db.String(150),
        nullable=False,
        index=True,
    )

    tipo = db.Column(
        db.String(30),
        nullable=False,
        index=True,
    )

    descricao = db.Column(
        db.Text,
        nullable=True,
    )

    plano_pai_id = db.Column(
        db.Integer,
        db.ForeignKey(
            "planos_manutencao.id",
            ondelete="RESTRICT",
        ),
        nullable=True,
        index=True,
    )

    intervalo_horas = db.Column(
        db.Numeric(14, 2),
        nullable=True,
    )

    intervalo_meses = db.Column(
        db.Integer,
        nullable=True,
    )

    observacoes = db.Column(
        db.Text,
        nullable=True,
    )

    plano_pai = db.relationship(
        "PlanoManutencao",
        remote_side="PlanoManutencao.id",
        foreign_keys=[plano_pai_id],
        backref=db.backref(
            "planos_filhos",
            lazy="dynamic",
        ),
    )

    __table_args__ = (
        CheckConstraint(
            "tipo IN ("
            "'BASICA', "
            "'INTERMEDIARIA', "
            "'AVANCADA'"
            ")",
            name="ck_plano_manutencao_tipo",
        ),
        CheckConstraint(
            "intervalo_horas IS NULL OR intervalo_horas > 0",
            name="ck_plano_manutencao_intervalo_horas",
        ),
        CheckConstraint(
            "intervalo_meses IS NULL OR intervalo_meses > 0",
            name="ck_plano_manutencao_intervalo_meses",
        ),
        CheckConstraint(
            "intervalo_horas IS NOT NULL "
            "OR intervalo_meses IS NOT NULL",
            name="ck_plano_manutencao_periodicidade",
        ),
        CheckConstraint(
            "plano_pai_id IS NULL OR plano_pai_id <> id",
            name="ck_plano_manutencao_pai_diferente",
        ),
        Index(
            "ix_planos_manutencao_tipo_ativo",
            "tipo",
            "ativo",
        ),
    )

    def __repr__(self):
        return (
            f"<PlanoManutencao "
            f"id={self.id} "
            f"codigo={self.codigo!r} "
            f"tipo={self.tipo!r}>"
        )


class GeradorPlanoManutencao(BaseModel):
    """Vinculo entre um grupo gerador e um plano de manutencao."""

    __tablename__ = "gerador_planos_manutencao"

    gerador_id = db.Column(
        db.Integer,
        db.ForeignKey(
            "geradores.id",
            ondelete="RESTRICT",
        ),
        nullable=False,
        index=True,
    )

    plano_id = db.Column(
        db.Integer,
        db.ForeignKey(
            "planos_manutencao.id",
            ondelete="RESTRICT",
        ),
        nullable=False,
        index=True,
    )

    data_base_programacao = db.Column(
        db.Date,
        nullable=True,
    )

    horimetro_base_programacao = db.Column(
        db.Numeric(14, 2),
        nullable=True,
    )

    observacoes = db.Column(
        db.Text,
        nullable=True,
    )

    gerador = db.relationship(
        "Gerador",
        backref=db.backref(
            "planos_manutencao",
            lazy="dynamic",
        ),
    )

    plano = db.relationship(
        "PlanoManutencao",
        backref=db.backref(
            "geradores_vinculados",
            lazy="dynamic",
        ),
    )

    __table_args__ = (
        CheckConstraint(
            "horimetro_base_programacao IS NULL "
            "OR horimetro_base_programacao >= 0",
            name="ck_gerador_plano_horimetro_base",
        ),
        Index(
            "ix_gerador_planos_gerador_plano",
            "gerador_id",
            "plano_id",
        ),
        Index(
            "ix_gerador_planos_gerador_ativo",
            "gerador_id",
            "ativo",
        ),
    )

    def __repr__(self):
        return (
            f"<GeradorPlanoManutencao "
            f"id={self.id} "
            f"gerador={self.gerador_id} "
            f"plano={self.plano_id}>"
        )
