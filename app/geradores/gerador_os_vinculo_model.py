# -*- coding: utf-8 -*-
"""G5-F2: vínculo explícito de uma OS com um ou vários grupos geradores.

Não altera a tabela de OS nem cria movimentação financeira, fiscal ou de estoque.
"""
from sqlalchemy import CheckConstraint, Index, UniqueConstraint

from app.extensoes import db
from app.models import BaseModel


class GeradorOSVinculo(BaseModel):
    __tablename__ = "gerador_os_vinculos"

    ordem_servico_id = db.Column(
        db.Integer,
        db.ForeignKey("ordem_servico.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    gerador_id = db.Column(
        db.Integer,
        db.ForeignKey("geradores.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    criado_por_id = db.Column(
        db.Integer,
        db.ForeignKey("usuarios.id", ondelete="SET NULL"),
        nullable=True,
    )

    ordem_servico = db.relationship(
        "OrdemServico", foreign_keys=[ordem_servico_id],
        backref=db.backref("geradores_vinculados_g5", lazy="dynamic"),
    )
    gerador = db.relationship(
        "Gerador", foreign_keys=[gerador_id],
        backref=db.backref("ordens_servico_vinculadas_g5", lazy="dynamic"),
    )

    __table_args__ = (
        UniqueConstraint(
            "ordem_servico_id", "gerador_id",
            name="uq_gerador_os_vinculo_par",
        ),
        CheckConstraint(
            "ordem_servico_id > 0 AND gerador_id > 0",
            name="ck_gerador_os_vinculos_ids_positivos",
        ),
        Index(
            "ix_gerador_os_vinculos_os_ativo",
            "ordem_servico_id", "ativo",
        ),
    )
