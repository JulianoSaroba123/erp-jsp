"""Documento NFS-e da nova fundacao fiscal do ERP JSP.

Este model representa o ciclo de vida fiscal de uma NFS-e vinculada a uma OS.
Nao realiza transmissao e nao gera lancamento financeiro.
"""

from app.extensoes import db
from app.models import BaseModel


STATUS_NFSE = {
    "RASCUNHO",
    "PREPARADA",
    "PENDENTE_ENVIO",
    "PROCESSANDO",
    "AUTORIZADA",
    "REJEITADA",
    "CANCELADA",
}

AMBIENTES_NFSE = {
    "HOMOLOGACAO",
    "PRODUCAO",
}


class NfseDocumento(BaseModel):
    """Documento fiscal NFS-e vinculado a uma Ordem de Servico."""

    __tablename__ = "nfse_documento"

    ordem_servico_id = db.Column(
        db.Integer,
        db.ForeignKey("ordem_servico.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    configuracao_fiscal_id = db.Column(
        db.Integer,
        db.ForeignKey("configuracao_fiscal.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    status = db.Column(
        db.String(30),
        nullable=False,
        default="RASCUNHO",
        server_default="RASCUNHO",
        index=True,
    )

    # Snapshot minimo da integracao no momento da preparacao.
    ambiente = db.Column(
        db.String(20),
        nullable=False,
        default="HOMOLOGACAO",
        server_default="HOMOLOGACAO",
    )

    provider = db.Column(db.String(50))

    # Parcela financeira que originou esta NFS-e.
    #
    # Nullable para preservar documentos legados criados antes
    # da emissao fiscal por parcela.
    ordem_servico_parcela_id = db.Column(
        db.Integer,
        db.ForeignKey(
            "ordem_servico_parcelas.id",
            ondelete="RESTRICT",
        ),
        nullable=True,
        index=True,
    )

    ordem_servico_parcela = db.relationship(
        "OrdemServicoParcela",
        foreign_keys=[ordem_servico_parcela_id],
        backref=db.backref(
            "nfse_documentos",
            lazy="select",
        ),
    )

    # Valor fiscal imutavel da intencao de emissao.
    # Para emissao parcelada corresponde ao valor da parcela.
    valor_servicos = db.Column(
        db.Numeric(12, 2),
        nullable=True,
    )

    # Idempotencia da intencao fiscal.
    chave_idempotencia = db.Column(
        db.String(160),
        unique=True,
    )

    # Identificacao RPS / NFS-e.
    serie_rps = db.Column(db.String(20))
    numero_rps = db.Column(db.Integer)

    numero_nfse = db.Column(db.String(50))
    protocolo = db.Column(db.String(100))
    codigo_verificacao = db.Column(db.String(100))
    chave_acesso = db.Column(db.String(100))

    # Retorno operacional.
    mensagem_status = db.Column(db.Text)

    # Artefato fiscal preparado e imutavel para transmissao.
    xml_envio = db.Column(db.LargeBinary)
    xml_envio_sha256 = db.Column(db.String(64))
    preparado_em = db.Column(db.DateTime(timezone=True))

    __table_args__ = (
        db.UniqueConstraint(
            "ordem_servico_parcela_id",
            name="uq_nfse_documento_parcela",
        ),
        db.CheckConstraint(
            "valor_servicos IS NULL OR valor_servicos > 0",
            name="ck_nfse_documento_valor_servicos",
        ),
        db.CheckConstraint(
            "status IN ("
            "'RASCUNHO', "
            "'PREPARADA', "
            "'PENDENTE_ENVIO', "
            "'PROCESSANDO', "
            "'AUTORIZADA', "
            "'REJEITADA', "
            "'CANCELADA'"
            ")",
            name="ck_nfse_documento_status",
        ),
        db.CheckConstraint(
            "ambiente IN ('HOMOLOGACAO', 'PRODUCAO')",
            name="ck_nfse_documento_ambiente",
        ),
        db.CheckConstraint(
            "numero_rps IS NULL OR numero_rps >= 1",
            name="ck_nfse_documento_numero_rps",
        ),
        db.UniqueConstraint(
            "serie_rps",
            "numero_rps",
            name="uq_nfse_documento_serie_numero_rps",
        ),
    )

    def __repr__(self):
        return (
            f"<NfseDocumento id={self.id} "
            f"os={self.ordem_servico_id} "
            f"status={self.status}>"
        )

    @property
    def transmitida(self):
        """Indica se o documento ja alcancou estado fiscal externo final."""
        return self.status in {
            "AUTORIZADA",
            "REJEITADA",
            "CANCELADA",
        }

    @property
    def pode_ser_editada(self):
        """Documento ainda pode receber preparacao local."""
        return self.status in {
            "RASCUNHO",
            "PREPARADA",
            "REJEITADA",
        }
