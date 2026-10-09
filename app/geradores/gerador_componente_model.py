# -*- coding: utf-8 -*-
"""
ERP JSP - Modulo GERADORES
Componentes tecnicos da Fase G2.

Nesta etapa:
- Motor
- Alternador
- Controladora
- QTA / ATS

Os cadastros sao progressivos.
Nenhum dado tecnico desconhecido e obrigatorio.
Nenhuma entidade desta fase movimenta estoque.
"""

from sqlalchemy import CheckConstraint, Index

from app.extensoes import db
from app.models import BaseModel


class GeradorMotor(BaseModel):
    """Motor instalado ou historicamente vinculado ao grupo gerador."""

    __tablename__ = "gerador_motores"

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

    variante = db.Column(
        db.String(150),
        nullable=True,
    )

    numero_serie = db.Column(
        db.String(150),
        nullable=True,
        index=True,
    )

    quantidade_cilindros = db.Column(
        db.Integer,
        nullable=True,
    )

    cilindrada_l = db.Column(
        db.Numeric(10, 3),
        nullable=True,
    )

    aspiracao = db.Column(
        db.String(100),
        nullable=True,
    )

    turbo = db.Column(
        db.Boolean,
        nullable=True,
    )

    intercooler = db.Column(
        db.Boolean,
        nullable=True,
    )

    potencia = db.Column(
        db.Numeric(12, 2),
        nullable=True,
    )

    potencia_unidade = db.Column(
        db.String(20),
        nullable=True,
    )

    rpm = db.Column(
        db.Integer,
        nullable=True,
    )

    combustivel = db.Column(
        db.String(80),
        nullable=True,
    )

    capacidade_oleo_l = db.Column(
        db.Numeric(10, 2),
        nullable=True,
    )

    especificacao_oleo = db.Column(
        db.String(200),
        nullable=True,
    )

    # Mantidos como texto porque o fabricante pode fornecer
    # valor unico, faixa e unidades diferentes.
    pressao_normal_oleo = db.Column(
        db.String(100),
        nullable=True,
    )

    temperatura_normal = db.Column(
        db.String(100),
        nullable=True,
    )

    observacoes = db.Column(
        db.Text,
        nullable=True,
    )

    gerador = db.relationship(
        "Gerador",
        backref=db.backref(
            "motores",
            lazy="dynamic",
        ),
    )

    __table_args__ = (
        CheckConstraint(
            "quantidade_cilindros IS NULL "
            "OR quantidade_cilindros > 0",
            name="ck_gerador_motor_cilindros",
        ),
        CheckConstraint(
            "cilindrada_l IS NULL "
            "OR cilindrada_l >= 0",
            name="ck_gerador_motor_cilindrada",
        ),
        CheckConstraint(
            "potencia IS NULL "
            "OR potencia >= 0",
            name="ck_gerador_motor_potencia",
        ),
        CheckConstraint(
            "rpm IS NULL OR rpm > 0",
            name="ck_gerador_motor_rpm",
        ),
        CheckConstraint(
            "capacidade_oleo_l IS NULL "
            "OR capacidade_oleo_l >= 0",
            name="ck_gerador_motor_capacidade_oleo",
        ),
        Index(
            "ix_gerador_motores_gerador_ativo",
            "gerador_id",
            "ativo",
        ),
    )

    def __repr__(self):
        return (
            f"<GeradorMotor "
            f"id={self.id} "
            f"gerador={self.gerador_id} "
            f"modelo={self.modelo!r}>"
        )


class GeradorAlternador(BaseModel):
    """Alternador principal ou historicamente vinculado ao gerador."""

    __tablename__ = "gerador_alternadores"

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

    numero_serie = db.Column(
        db.String(150),
        nullable=True,
        index=True,
    )

    potencia_kva = db.Column(
        db.String(100),
        nullable=True,
    )

    tensao = db.Column(
        db.String(100),
        nullable=True,
    )

    corrente_a = db.Column(
        db.String(100),
        nullable=True,
    )

    frequencia_hz = db.Column(
        db.Numeric(8, 2),
        nullable=True,
    )

    rpm = db.Column(
        db.Integer,
        nullable=True,
    )

    numero_polos = db.Column(
        db.Integer,
        nullable=True,
    )

    fator_potencia = db.Column(
        db.Numeric(5, 3),
        nullable=True,
    )

    classe_isolacao = db.Column(
        db.String(50),
        nullable=True,
    )

    grau_protecao = db.Column(
        db.String(50),
        nullable=True,
    )

    sistema_excitacao = db.Column(
        db.String(150),
        nullable=True,
    )

    possui_avr = db.Column(
        db.Boolean,
        nullable=True,
    )

    avr_fabricante = db.Column(
        db.String(150),
        nullable=True,
    )

    avr_modelo = db.Column(
        db.String(150),
        nullable=True,
    )

    ligacao = db.Column(
        db.String(100),
        nullable=True,
    )

    observacoes = db.Column(
        db.Text,
        nullable=True,
    )

    gerador = db.relationship(
        "Gerador",
        backref=db.backref(
            "alternadores",
            lazy="dynamic",
        ),
    )

    __table_args__ = (
        CheckConstraint(
            "frequencia_hz IS NULL "
            "OR frequencia_hz > 0",
            name="ck_gerador_alternador_frequencia",
        ),
        CheckConstraint(
            "rpm IS NULL OR rpm > 0",
            name="ck_gerador_alternador_rpm",
        ),
        CheckConstraint(
            "numero_polos IS NULL "
            "OR numero_polos > 0",
            name="ck_gerador_alternador_polos",
        ),
        CheckConstraint(
            "fator_potencia IS NULL "
            "OR (fator_potencia > 0 "
            "AND fator_potencia <= 1)",
            name="ck_gerador_alternador_fp",
        ),
        Index(
            "ix_gerador_alternadores_gerador_ativo",
            "gerador_id",
            "ativo",
        ),
    )

    def __repr__(self):
        return (
            f"<GeradorAlternador "
            f"id={self.id} "
            f"gerador={self.gerador_id} "
            f"modelo={self.modelo!r}>"
        )


class GeradorControladora(BaseModel):
    """Controladora instalada no grupo gerador."""

    __tablename__ = "gerador_controladoras"

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

    versao = db.Column(
        db.String(100),
        nullable=True,
    )

    firmware = db.Column(
        db.String(100),
        nullable=True,
    )

    tensao_alimentacao = db.Column(
        db.String(100),
        nullable=True,
    )

    comunicacao = db.Column(
        db.String(250),
        nullable=True,
    )

    configuracao_relevante = db.Column(
        db.Text,
        nullable=True,
    )

    manual_referencia = db.Column(
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
            "controladoras",
            lazy="dynamic",
        ),
    )

    __table_args__ = (
        Index(
            "ix_gerador_controladoras_gerador_ativo",
            "gerador_id",
            "ativo",
        ),
    )

    def __repr__(self):
        return (
            f"<GeradorControladora "
            f"id={self.id} "
            f"gerador={self.gerador_id} "
            f"modelo={self.modelo!r}>"
        )


class GeradorQTA(BaseModel):
    """QTA/ATS associado ao grupo gerador."""

    __tablename__ = "gerador_qtas"

    TIPO_CONTATOR = "CONTATOR"
    TIPO_DISJUNTOR = "DISJUNTOR"
    TIPO_CHAVE_MOTORIZADA = "CHAVE_MOTORIZADA"
    TIPO_CHAVE_REVERSORA = "CHAVE_REVERSORA"
    TIPO_OUTRO = "OUTRO"

    TIPOS_VALIDOS = (
        TIPO_CONTATOR,
        TIPO_DISJUNTOR,
        TIPO_CHAVE_MOTORIZADA,
        TIPO_CHAVE_REVERSORA,
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

    fabricante = db.Column(
        db.String(150),
        nullable=True,
    )

    modelo = db.Column(
        db.String(150),
        nullable=True,
    )

    corrente_a = db.Column(
        db.Numeric(12, 2),
        nullable=True,
    )

    numero_polos = db.Column(
        db.Integer,
        nullable=True,
    )

    tensao = db.Column(
        db.String(100),
        nullable=True,
    )

    transferencia = db.Column(
        db.String(100),
        nullable=True,
    )

    tipo = db.Column(
        db.String(30),
        nullable=True,
        index=True,
    )

    controle = db.Column(
        db.String(250),
        nullable=True,
    )

    intertravamento = db.Column(
        db.String(250),
        nullable=True,
    )

    posicao_normal = db.Column(
        db.String(100),
        nullable=True,
    )

    observacoes = db.Column(
        db.Text,
        nullable=True,
    )

    gerador = db.relationship(
        "Gerador",
        backref=db.backref(
            "qtas",
            lazy="dynamic",
        ),
    )

    __table_args__ = (
        CheckConstraint(
            "tipo IS NULL OR tipo IN ("
            "'CONTATOR', "
            "'DISJUNTOR', "
            "'CHAVE_MOTORIZADA', "
            "'CHAVE_REVERSORA', "
            "'OUTRO'"
            ")",
            name="ck_gerador_qta_tipo",
        ),
        CheckConstraint(
            "corrente_a IS NULL "
            "OR corrente_a >= 0",
            name="ck_gerador_qta_corrente",
        ),
        CheckConstraint(
            "numero_polos IS NULL "
            "OR numero_polos > 0",
            name="ck_gerador_qta_polos",
        ),
        Index(
            "ix_gerador_qtas_gerador_ativo",
            "gerador_id",
            "ativo",
        ),
    )

    def __repr__(self):
        return (
            f"<GeradorQTA "
            f"id={self.id} "
            f"gerador={self.gerador_id} "
            f"modelo={self.modelo!r}>"
        )
