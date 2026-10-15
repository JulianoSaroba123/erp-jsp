# -*- coding: utf-8 -*-
"""G5-F3: execução digital versionada por vínculo OS-gerador."""
from sqlalchemy import CheckConstraint, Index, UniqueConstraint

from app.extensoes import db
from app.models import BaseModel


class GeradorChecklistExecucao(BaseModel):
    __tablename__ = "gerador_checklist_execucoes"

    ESTADO_RASCUNHO = "RASCUNHO"
    ESTADO_CONCLUIDO = "CONCLUIDO"

    vinculo_id = db.Column(
        db.Integer, db.ForeignKey("gerador_os_vinculos.id", ondelete="RESTRICT"),
        nullable=False, index=True,
    )
    tipo_plano = db.Column(db.String(30), nullable=False)
    versao_catalogo = db.Column(db.String(30), nullable=False)
    estado = db.Column(
        db.String(20), nullable=False,
        default=ESTADO_RASCUNHO, server_default=ESTADO_RASCUNHO, index=True,
    )
    data_servico = db.Column(db.Date, nullable=True)
    modelo_snapshot = db.Column(db.JSON, nullable=False)
    identificacao_snapshot = db.Column(db.JSON, nullable=False)
    respostas_snapshot = db.Column(db.JSON, nullable=False)
    observacoes_gerais = db.Column(db.Text, nullable=True)
    criado_por_id = db.Column(
        db.Integer, db.ForeignKey("usuarios.id", ondelete="SET NULL"), nullable=True
    )
    atualizado_por_id = db.Column(
        db.Integer, db.ForeignKey("usuarios.id", ondelete="SET NULL"), nullable=True
    )
    concluido_por_id = db.Column(
        db.Integer, db.ForeignKey("usuarios.id", ondelete="SET NULL"), nullable=True
    )
    concluido_em = db.Column(db.DateTime, nullable=True)

    vinculo = db.relationship(
        "GeradorOSVinculo",
        backref=db.backref("checklists_g5", lazy="dynamic"),
    )
    __table_args__ = (
        UniqueConstraint(
            "vinculo_id", "tipo_plano", name="uq_gerador_checklist_vinculo_tipo"
        ),
        CheckConstraint(
            "tipo_plano IN ('BASICA','INTERMEDIARIA','AVANCADA')",
            name="ck_gerador_checklist_tipo",
        ),
        CheckConstraint(
            "estado IN ('RASCUNHO','CONCLUIDO')",
            name="ck_gerador_checklist_estado",
        ),
        Index(
            "ix_gerador_checklist_execucoes_vinculo_estado",
            "vinculo_id", "estado",
        ),
    )
