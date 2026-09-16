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

    __table_args__ = (
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
