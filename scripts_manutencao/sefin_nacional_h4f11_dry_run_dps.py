"""H4-F11 - dry-run real de DPS Nacional em Homologacao.

Gera, valida, assina com A1 real e empacota uma DPS controlada.
NAO usa rede. NAO acessa banco. NAO importa o pacote app.
NAO executa POST /nfse e NAO transmite documento fiscal.
"""

from __future__ import annotations

import base64
from datetime import datetime
import gzip
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys
from types import SimpleNamespace
from zoneinfo import ZoneInfo


RAIZ = Path(__file__).resolve().parents[1]
SCRIPT_H4F9 = (
    Path(__file__).resolve().parent
    / "sefin_nacional_h4f9_preflight_real.py"
)

ARQUIVO_DPS_CANONICA = (
    RAIZ
    / "app"
    / "fiscal"
    / "providers"
    / "sefin_nacional_dps.py"
)
ARQUIVO_SERIALIZER = (
    RAIZ
    / "app"
    / "fiscal"
    / "xml"
    / "dps_serializer.py"
)
ARQUIVO_SIGNER = (
    RAIZ
    / "app"
    / "fiscal"
    / "xml"
    / "dps_signer.py"
)
ARQUIVO_VALIDATOR = (
    RAIZ
    / "app"
    / "fiscal"
    / "xml"
    / "dps_xsd_validator.py"
)

CNPJ_PRESTADOR = "66298788000172"
IM_PRESTADOR = "14180"
MUNICIPIO_TIETE = "3554508"
MUNICIPIO_QUADRA = "3541653"
SERIE_DRY_RUN = "9999"
NUMERO_DPS_DRY_RUN = "999999999999999"
CODIGO_TRIBUTACAO_NACIONAL = "140101"
CODIGO_NBS = "101061900"
VALOR_CONTROLADO = "1.00"
ENV_PTOTTRIBSN = "NFSE_H4F11_PTOTTRIBSN"

DESCRICAO_DRY_RUN = (
    "HOMOLOGACAO CONTROLADA H4-F11 - "
    "PRE-EMISSAO SEM TRANSMISSAO"
)


class DryRunDpsInvalido(RuntimeError):
    """Falha segura durante o dry-run local da DPS."""


class ResultadoDryRun:
    def __init__(
        self,
        *,
        id_dps,
        xml_nao_assinado,
        xml_assinado,
        corpo_json,
        fingerprint_certificado,
        xsd_antes_ok,
        assinatura_ok,
        xsd_depois_ok,
    ):
        self.id_dps = str(id_dps)
        self.xml_nao_assinado = bytes(xml_nao_assinado)
        self.xml_assinado = bytes(xml_assinado)
        self.corpo_json = bytes(corpo_json)
        self.fingerprint_certificado = str(
            fingerprint_certificado
        )
        self.xsd_antes_ok = bool(xsd_antes_ok)
        self.assinatura_ok = bool(assinatura_ok)
        self.xsd_depois_ok = bool(xsd_depois_ok)
        self.rede_utilizada = False
        self.banco_acessado = False
        self.flask_inicializado = False
        self.post_nfse_executado = False
        self.transmissao_executada = False


def _carregar_modulo(
    nome: str,
    caminho: Path,
):
    spec = importlib.util.spec_from_file_location(
        nome,
        caminho,
    )

    if spec is None or spec.loader is None:
        raise DryRunDpsInvalido(
            f"Nao foi possivel carregar modulo local: {nome}."
        )

    modulo = importlib.util.module_from_spec(
        spec
    )

    # Necessario para modulos que usam dataclass.
    sys.modules[
        nome
    ] = modulo

    spec.loader.exec_module(
        modulo
    )

    return modulo


h4f9 = _carregar_modulo(
    "h4f9_preflight_real_h4f11",
    SCRIPT_H4F9,
)
dps_model = _carregar_modulo(
    "sefin_dps_model_h4f11",
    ARQUIVO_DPS_CANONICA,
)
serializer = _carregar_modulo(
    "sefin_dps_serializer_h4f11",
    ARQUIVO_SERIALIZER,
)
signer = _carregar_modulo(
    "sefin_dps_signer_h4f11",
    ARQUIVO_SIGNER,
)
validator = _carregar_modulo(
    "sefin_dps_validator_h4f11",
    ARQUIVO_VALIDATOR,
)


def _agora_homologacao() -> datetime:
    return datetime.now(
        ZoneInfo(
            "America/Sao_Paulo"
        )
    ).replace(
        microsecond=0
    )


def _percentual_tot_trib_sn() -> str:
    valor = str(
        os.environ.get(
            ENV_PTOTTRIBSN,
            "",
        )
        or ""
    ).strip()

    if not valor:
        raise DryRunDpsInvalido(
            "Percentual pTotTribSN nao informado. "
            "Defina NFSE_H4F11_PTOTTRIBSN com a aliquota nominal "
            "vigente e confirmada do Simples Nacional."
        )

    return valor


def _montar_dps(
    *,
    agora: datetime,
    percentual_tot_trib_sn: str,
):
    return dps_model.montar_dps_canonica(
        ambiente="HOMOLOGACAO",
        versao_layout="1.01",
        data_emissao=agora,
        versao_aplicativo="ERP-JSP-H4F11",
        serie=SERIE_DRY_RUN,
        numero_dps=NUMERO_DPS_DRY_RUN,
        competencia=agora.date(),
        tipo_emitente="1",
        municipio_emissao_ibge=MUNICIPIO_TIETE,
        prestador={
            "tipo_documento": "CNPJ",
            "documento": CNPJ_PRESTADOR,
            # A NFS-e Nacional ja aceita da JSP nao exibiu IM.
            # Evita E0120 quando nao ha registro complementar no CNC.
            "inscricao_municipal": None,
            "municipio_ibge": MUNICIPIO_TIETE,
            # tpEmit=1: xNome deve ser omitido (E0121).
            "nome": None,
            "regime_tributario": {
                "op_simp_nac": "3",
                "reg_ap_trib_sn": "1",
                "reg_esp_trib": "0",
            },
        },
        tomador=None,
        servico={
            "codigo_lista_nacional": (
                CODIGO_TRIBUTACAO_NACIONAL
            ),
            "codigo_tributacao_municipal": None,
            "nbs": CODIGO_NBS,
            "descricao": DESCRICAO_DRY_RUN,
            "municipio_incidencia_ibge": MUNICIPIO_TIETE,
            "municipio_prestacao_ibge": MUNICIPIO_QUADRA,
        },
        valores={
            "valor_servicos": VALOR_CONTROLADO,
            "valor_recebido": None,
            "desconto_incondicionado": "0.00",
            "desconto_condicionado": "0.00",
            "deducoes": "0.00",
        },
        iss={
            "tributacao_issqn": "1",
            "tipo_retencao": "1",
            "aliquota": None,
        },
        totais_tributos={
            "percentual_simples": percentual_tot_trib_sn,
        },
        ibs_cbs=None,
    )


def _validar_xsd(
    xml: bytes,
) -> None:
    resultado = validator.validar_xml_dps_xsd(
        xml,
        h4f9.CAMINHO_XSD,
    )

    if not resultado.valido:
        raise DryRunDpsInvalido(
            "DPS invalida perante XSD PRODREST: "
            + "; ".join(
                resultado.erros
            )
        )


def _montar_corpo_json(
    xml_assinado: bytes,
) -> bytes:
    comprimido = gzip.compress(
        xml_assinado,
        compresslevel=9,
        mtime=0,
    )

    corpo = {
        "dpsXmlGZipB64": (
            base64.b64encode(
                comprimido
            ).decode(
                "ascii"
            )
        ),
    }

    resultado = json.dumps(
        corpo,
        ensure_ascii=False,
        separators=(",", ":"),
    ).encode(
        "utf-8"
    )

    # Prova local de reversibilidade do envelope.
    recuperado = gzip.decompress(
        base64.b64decode(
            corpo["dpsXmlGZipB64"],
            validate=True,
        )
    )

    if recuperado != xml_assinado:
        raise DryRunDpsInvalido(
            "Envelope GZip/Base64 nao recupera o XML assinado."
        )

    return resultado


def executar_dry_run(
    *,
    agora: datetime | None = None,
    material_a1=None,
    percentual_tot_trib_sn: str | None = None,
) -> ResultadoDryRun:
    """Executa toda a pre-emissao em memoria, sem rede."""

    momento = (
        agora
        if agora is not None
        else _agora_homologacao()
    )

    if (
        momento.tzinfo is None
        or momento.utcoffset() is None
    ):
        raise DryRunDpsInvalido(
            "Data/hora do dry-run deve possuir timezone."
        )

    percentual = (
        percentual_tot_trib_sn
        if percentual_tot_trib_sn is not None
        else _percentual_tot_trib_sn()
    )

    dps = _montar_dps(
        agora=momento,
        percentual_tot_trib_sn=percentual,
    )

    xml_nao_assinado = (
        serializer.montar_xml_dps_serializado(
            dps,
            ambiente="HOMOLOGACAO",
        )
    )

    _validar_xsd(
        xml_nao_assinado
    )

    if material_a1 is None:
        h4f9._validar_variaveis_minimas()

        (
            chave_privada,
            certificado,
            cadeia,
            _,
        ) = h4f9._carregar_material_a1()

        material = SimpleNamespace(
            chave_privada=chave_privada,
            certificado=certificado,
            cadeia=cadeia,
        )
    else:
        material = material_a1
        certificado = getattr(
            material,
            "certificado",
            None,
        )

    if certificado is None:
        raise DryRunDpsInvalido(
            "Certificado A1 nao informado para o dry-run."
        )

    xml_assinado = signer.assinar_xml_dps(
        xml_nao_assinado,
        material_certificado=material,
    )

    signer.validar_assinatura_xml_dps(
        xml_assinado,
        certificado_esperado=certificado,
    )

    _validar_xsd(
        xml_assinado
    )

    corpo_json = _montar_corpo_json(
        xml_assinado
    )

    fingerprint = certificado.fingerprint(
        h4f9.hashes.SHA256()
    ).hex().upper()

    return ResultadoDryRun(
        id_dps=dps[
            "identificacao"
        ][
            "id"
        ],
        xml_nao_assinado=xml_nao_assinado,
        xml_assinado=xml_assinado,
        corpo_json=corpo_json,
        fingerprint_certificado=fingerprint,
        xsd_antes_ok=True,
        assinatura_ok=True,
        xsd_depois_ok=True,
    )


def _sha256(
    dados: bytes,
) -> str:
    return hashlib.sha256(
        dados
    ).hexdigest().upper()


def _mascarar_id(
    id_dps: str,
) -> str:
    valor = str(
        id_dps or ""
    )

    if len(valor) < 16:
        return "<invalido>"

    return (
        valor[:10]
        + "..."
        + valor[-8:]
    )


def executar() -> int:
    resultado = executar_dry_run()

    print(
        "=== H4-F11 | DRY-RUN REAL DPS HOMOLOGACAO ==="
    )
    print(
        "STATUS: OK"
    )
    print(
        "DPS ID: "
        + _mascarar_id(
            resultado.id_dps
        )
    )
    print(
        "SERIE DRY-RUN: "
        + SERIE_DRY_RUN
    )
    print(
        "NUMERO DPS DRY-RUN: "
        + NUMERO_DPS_DRY_RUN
    )
    print(
        "VALOR CONTROLADO: R$ "
        + VALOR_CONTROLADO.replace(
            ".",
            ",",
        )
    )
    print(
        "PTOTTRIBSN: "
        + _percentual_tot_trib_sn().replace(
            ".",
            ",",
        )
        + "%"
    )
    print(
        "XSD ANTES ASSINATURA: "
        + str(
            resultado.xsd_antes_ok
        )
    )
    print(
        "ASSINATURA A1: "
        + str(
            resultado.assinatura_ok
        )
    )
    print(
        "XSD DEPOIS ASSINATURA: "
        + str(
            resultado.xsd_depois_ok
        )
    )
    print(
        "XML ASSINADO SHA256: "
        + _sha256(
            resultado.xml_assinado
        )
    )
    print(
        "CORPO JSON SHA256: "
        + _sha256(
            resultado.corpo_json
        )
    )
    print(
        "XML ASSINADO BYTES: "
        + str(
            len(
                resultado.xml_assinado
            )
        )
    )
    print(
        "CORPO JSON BYTES: "
        + str(
            len(
                resultado.corpo_json
            )
        )
    )
    print(
        "CERTIFICADO SHA256: "
        + h4f9._mascarar_fingerprint(
            resultado.fingerprint_certificado
        )
    )
    print(
        "FLASK INICIALIZADO: False"
    )
    print(
        "BANCO ACESSADO: False"
    )
    print(
        "REDE UTILIZADA: False"
    )
    print(
        "POST /nfse: NAO EXECUTADO"
    )
    print(
        "TRANSMISSAO: NAO EXECUTADA"
    )

    return 0


def main() -> int:
    try:
        return executar()
    except (
        DryRunDpsInvalido,
        h4f9.PreflightStandaloneInvalido,
        dps_model.DpsCanonicaInvalida,
        serializer.SerializacaoDpsInvalida,
        signer.AssinaturaXmlDpsInvalida,
        validator.ValidacaoXsdDpsInvalida,
    ) as exc:
        print(
            "=== H4-F11 | DRY-RUN REAL DPS HOMOLOGACAO ==="
        )
        print(
            "STATUS: FALHA"
        )
        print(
            "MOTIVO: "
            + str(
                exc
            )
        )
        print(
            "REDE UTILIZADA: False"
        )
        print(
            "POST /nfse: NAO EXECUTADO"
        )
        print(
            "TRANSMISSAO: NAO EXECUTADA"
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(
        main()
    )
