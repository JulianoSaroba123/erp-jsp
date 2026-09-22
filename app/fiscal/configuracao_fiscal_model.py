"""Configuracao fiscal da empresa.

Fundacao fiscal do ERP JSP.

Esta estrutura armazena somente parametros fiscais e de integracao.
Credenciais, certificados e senhas nao devem ser persistidos aqui.
"""

from app.extensoes import db
from app.models import BaseModel


REGIMES_TRIBUTARIOS = {
    "MEI",
    "SIMPLES_NACIONAL",
    "LUCRO_PRESUMIDO",
    "LUCRO_REAL",
    "OUTRO",
}

AMBIENTES_FISCAIS = {
    "HOMOLOGACAO",
    "PRODUCAO",
}


class ConfiguracaoFiscal(BaseModel):
    """Configuracao fiscal vinculada ao cadastro institucional da empresa."""

    __tablename__ = "configuracao_fiscal"

    configuracao_id = db.Column(
        db.Integer,
        db.ForeignKey("configuracao.id", ondelete="RESTRICT"),
        nullable=False,
        unique=True,
    )

    # Identificacao fiscal
    inscricao_municipal = db.Column(db.String(50))
    regime_tributario = db.Column(db.String(30))
    optante_simples_nacional = db.Column(
        db.Boolean,
        nullable=False,
        default=False,
        server_default="false",
    )

    # Tributacao de servicos
    cnae_principal = db.Column(db.String(20))
    codigo_servico_municipal = db.Column(db.String(30))
    codigo_lc116 = db.Column(db.String(20))
    aliquota_iss_padrao = db.Column(db.Numeric(5, 2))
    municipio_ibge = db.Column(db.String(7))

    # Regime tributario da DPS Nacional
    #
    # Campos especificos do leiaute nacional.
    # Permanecem nullable no banco para nao fabricar
    # informacao fiscal em configuracoes preexistentes.
    op_simp_nac = db.Column(
        db.String(1),
        nullable=True,
    )

    reg_ap_trib_sn = db.Column(
        db.String(1),
        nullable=True,
    )

    reg_esp_trib = db.Column(
        db.String(1),
        nullable=True,
    )

    # Integracao NFS-e
    ambiente = db.Column(
        db.String(20),
        nullable=False,
        default="HOMOLOGACAO",
        server_default="HOMOLOGACAO",
    )
    provider = db.Column(db.String(50))
    serie_rps = db.Column(
        db.String(20),
        nullable=False,
        default="1",
        server_default="1",
    )
    proximo_rps = db.Column(
        db.Integer,
        nullable=False,
        default=1,
        server_default="1",
    )
    integracao_ativa = db.Column(
        db.Boolean,
        nullable=False,
        default=False,
        server_default="false",
    )

    __table_args__ = (
        db.CheckConstraint(
            "ambiente IN ('HOMOLOGACAO', 'PRODUCAO')",
            name="ck_config_fiscal_ambiente",
        ),
        db.CheckConstraint(
            "aliquota_iss_padrao IS NULL OR "
            "(aliquota_iss_padrao >= 0 AND aliquota_iss_padrao <= 100)",
            name="ck_config_fiscal_aliquota_iss",
        ),
        db.CheckConstraint(
            "proximo_rps >= 1",
            name="ck_config_fiscal_proximo_rps",
        ),
    )

    def __repr__(self):
        return (
            f"<ConfiguracaoFiscal configuracao_id={self.configuracao_id} "
            f"ambiente={self.ambiente}>"
        )

    @property
    def pronta_para_nfse(self):
        """Indica se os dados minimos locais para preparar NFS-e existem."""
        return all(
            (
                self.inscricao_municipal,
                self.municipio_ibge,
                self.codigo_servico_municipal,
                self.ambiente,
            )
        )
