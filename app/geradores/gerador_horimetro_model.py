# -*- coding: utf-8 -*-
"""
ERP JSP - Modulo GERADORES
Historico de horimetro da Fase G3.

Regras:
- preservar todas as leituras;
- nao substituir historico;
- permitir queda da leitura fisica somente por evento justificado;
- manter horas acumuladas logicas para programacao de manutencao.
"""

from sqlalchemy import CheckConstraint, Index

from app.extensoes import db
from app.models import BaseModel


class GeradorHorimetro(BaseModel):
    """Registro historico de leitura do horimetro de um gerador."""

    __tablename__ = "gerador_horimetros"

    EVENTO_NORMAL = "NORMAL"
    EVENTO_SUBSTITUICAO = "SUBSTITUICAO"
    EVENTO_RESET = "RESET"
    EVENTO_FALHA_INSTRUMENTO = "FALHA_INSTRUMENTO"

    EVENTOS_VALIDOS = (
        EVENTO_NORMAL,
        EVENTO_SUBSTITUICAO,
        EVENTO_RESET,
        EVENTO_FALHA_INSTRUMENTO,
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

    leitura_anterior = db.Column(
        db.Numeric(14, 2),
        nullable=True,
    )

    leitura_atual = db.Column(
        db.Numeric(14, 2),
        nullable=False,
    )

    horas_acumuladas = db.Column(
        db.Numeric(14, 2),
        nullable=False,
    )

    data_leitura = db.Column(
        db.DateTime,
        nullable=False,
        index=True,
    )

    responsavel = db.Column(
        db.String(150),
        nullable=False,
    )

    usuario_id = db.Column(
        db.Integer,
        db.ForeignKey(
            "usuarios.id",
            ondelete="RESTRICT",
        ),
        nullable=True,
        index=True,
    )

    tipo_evento = db.Column(
        db.String(30),
        nullable=False,
        default=EVENTO_NORMAL,
        server_default=EVENTO_NORMAL,
        index=True,
    )

    justificativa = db.Column(
        db.Text,
        nullable=True,
    )

    observacoes = db.Column(
        db.Text,
        nullable=True,
    )

    gerador = db.relationship(
        "Gerador",
        backref=db.backref(
            "historico_horimetro",
            lazy="dynamic",
        ),
    )

    usuario = db.relationship(
        "Usuario",
        backref=db.backref(
            "leituras_horimetro_geradores",
            lazy="dynamic",
        ),
    )

    __table_args__ = (
        CheckConstraint(
            "leitura_anterior IS NULL OR leitura_anterior >= 0",
            name="ck_gerador_horimetro_anterior",
        ),
        CheckConstraint(
            "leitura_atual >= 0",
            name="ck_gerador_horimetro_atual",
        ),
        CheckConstraint(
            "horas_acumuladas >= 0",
            name="ck_gerador_horimetro_acumulado",
        ),
        CheckConstraint(
            "tipo_evento IN ("
            "'NORMAL', "
            "'SUBSTITUICAO', "
            "'RESET', "
            "'FALHA_INSTRUMENTO'"
            ")",
            name="ck_gerador_horimetro_evento",
        ),
        Index(
            "ix_gerador_horimetros_gerador_data",
            "gerador_id",
            "data_leitura",
        ),
        Index(
            "ix_gerador_horimetros_gerador_ativo",
            "gerador_id",
            "ativo",
        ),
    )

    def __repr__(self):
        return (
            f"<GeradorHorimetro "
            f"id={self.id} "
            f"gerador={self.gerador_id} "
            f"leitura={self.leitura_atual}>"
        )
