# -*- coding: utf-8 -*-
"""G5-F5: trilha cronológica por checklist, sem assinatura digital presumida."""
from sqlalchemy import CheckConstraint, Index, UniqueConstraint

from app.extensoes import db
from app.models import BaseModel


class GeradorChecklistEvento(BaseModel):
    __tablename__ = "gerador_checklist_eventos"

    execucao_id = db.Column(
        db.Integer,
        db.ForeignKey("gerador_checklist_execucoes.id", ondelete="RESTRICT"),
        nullable=False, index=True,
    )
    sequencia = db.Column(db.Integer, nullable=False)
    acao = db.Column(db.String(20), nullable=False)
    estado_resultante = db.Column(db.String(20), nullable=False)
    usuario_id = db.Column(
        db.Integer, db.ForeignKey("usuarios.id", ondelete="SET NULL"),
        nullable=True,
    )
    usuario_nome = db.Column(db.String(120), nullable=False)
    registrado_em = db.Column(db.DateTime, nullable=False)
    sha256_respostas = db.Column(db.String(64), nullable=False)

    execucao = db.relationship(
        "GeradorChecklistExecucao",
        backref=db.backref("eventos_g5", lazy="dynamic"),
    )

    __table_args__ = (
        UniqueConstraint(
            "execucao_id", "sequencia", name="uq_g5_evento_execucao_sequencia",
        ),
        CheckConstraint("sequencia > 0", name="ck_g5_evento_sequencia_positiva"),
        CheckConstraint(
            "acao IN ('CRIADO','RASCUNHO_SALVO','CONCLUIDO')",
            name="ck_g5_evento_acao",
        ),
        Index(
            "ix_g5_evento_execucao_registrado",
            "execucao_id", "registrado_em",
        ),
    )
