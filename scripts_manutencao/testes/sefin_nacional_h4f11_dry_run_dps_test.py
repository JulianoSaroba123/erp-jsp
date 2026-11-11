"""H4-F11 - contrato do dry-run real de DPS sem transmissao."""

import base64
from datetime import datetime, timedelta, timezone
import gzip
import importlib.util
import json
from pathlib import Path
import sys
from types import SimpleNamespace

from cryptography import x509
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID


SCRIPT = (
    Path(__file__).resolve().parents[1]
    / "sefin_nacional_h4f11_dry_run_dps.py"
)


def _modulo():
    nome = "h4f11_dry_run_dps_testado"
    spec = importlib.util.spec_from_file_location(
        nome,
        SCRIPT,
    )
    modulo = importlib.util.module_from_spec(
        spec
    )
    sys.modules[
        nome
    ] = modulo
    spec.loader.exec_module(
        modulo
    )
    return modulo


def _material():
    chave = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
    )

    agora = datetime.now(
        timezone.utc
    )

    nome = x509.Name(
        [
            x509.NameAttribute(
                NameOID.COUNTRY_NAME,
                "BR",
            ),
            x509.NameAttribute(
                NameOID.ORGANIZATION_NAME,
                "ERP JSP H4-F11 TESTE",
            ),
            x509.NameAttribute(
                NameOID.COMMON_NAME,
                "H4-F11",
            ),
        ]
    )

    certificado = (
        x509.CertificateBuilder()
        .subject_name(
            nome
        )
        .issuer_name(
            nome
        )
        .public_key(
            chave.public_key()
        )
        .serial_number(
            x509.random_serial_number()
        )
        .not_valid_before(
            (
                agora
                - timedelta(
                    days=1
                )
            ).replace(
                tzinfo=None
            )
        )
        .not_valid_after(
            (
                agora
                + timedelta(
                    days=30
                )
            ).replace(
                tzinfo=None
            )
        )
        .sign(
            chave,
            hashes.SHA256(),
        )
    )

    return SimpleNamespace(
        chave_privada=chave,
        certificado=certificado,
        cadeia=(),
    )


def _agora():
    return datetime(
        2026,
        11,
        11,
        18,
        0,
        0,
        tzinfo=timezone(
            timedelta(
                hours=-3
            )
        ),
    )


def test_h4f11_001_script_nao_possui_transporte_operacional():
    texto = SCRIPT.read_text(
        encoding="utf-8"
    ).lower()

    assert "import requests" not in texto
    assert "from requests" not in texto
    assert "urllib.request" not in texto
    assert "http.client" not in texto
    assert "import socket" not in texto
    assert 'method="post"' not in texto
    assert ".post(" not in texto
    assert "from app" not in texto
    assert "import app" not in texto


def test_h4f11_002_dados_controlados_usam_identidade_fiscal_jsp():
    modulo = _modulo()

    dps = modulo._montar_dps(
        agora=_agora(),
        percentual_tot_trib_sn="6.00",
    )

    assert dps[
        "identificacao"
    ][
        "ambiente"
    ] == "HOMOLOGACAO"

    assert dps[
        "prestador"
    ][
        "documento"
    ] == "66298788000172"

    assert dps[
        "prestador"
    ][
        "inscricao_municipal"
    ] == "14180"

    assert dps[
        "prestador"
    ][
        "regime_tributario"
    ] == {
        "op_simp_nac": "3",
        "reg_ap_trib_sn": "1",
        "reg_esp_trib": "0",
    }

    assert dps[
        "servico"
    ][
        "codigo_lista_nacional"
    ] == "140101"

    assert dps[
        "servico"
    ][
        "codigo_tributacao_municipal"
    ] is None

    assert dps[
        "servico"
    ][
        "nbs"
    ] == "101061900"

    assert dps[
        "servico"
    ][
        "municipio_prestacao_ibge"
    ] == "3541653"

    assert dps[
        "valores"
    ][
        "valor_servicos"
    ] == "1.00"

    assert dps[
        "iss"
    ] == {
        "tributacao_issqn": "1",
        "tipo_retencao": "1",
        "aliquota": None,
    }

    assert dps[
        "totais_tributos"
    ] == {
        "percentual_simples": "6.00",
    }

    assert dps[
        "tomador"
    ] is None

    assert dps[
        "ibs_cbs"
    ] == {}


def test_h4f11_003_id_dps_controlado_e_valido():
    modulo = _modulo()

    dps = modulo._montar_dps(
        agora=_agora(),
        percentual_tot_trib_sn="6.00",
    )

    identificador = dps[
        "identificacao"
    ][
        "id"
    ]

    assert identificador.startswith(
        "DPS35545082"
    )
    assert len(
        identificador
    ) == 45
    assert dps[
        "identificacao"
    ][
        "serie"
    ] == "9999"
    assert dps[
        "identificacao"
    ][
        "numero_dps"
    ] == "999999999999999"


def test_h4f11_004_dry_run_completo_valida_xsd_e_assinatura():
    modulo = _modulo()
    material = _material()

    resultado = modulo.executar_dry_run(
        agora=_agora(),
        material_a1=material,
        percentual_tot_trib_sn="6.00",
    )

    assert resultado.xsd_antes_ok is True
    assert resultado.assinatura_ok is True
    assert resultado.xsd_depois_ok is True

    certificado = (
        modulo.signer.validar_assinatura_xml_dps(
            resultado.xml_assinado,
            certificado_esperado=material.certificado,
        )
    )

    assert (
        certificado.serial_number
        == material.certificado.serial_number
    )

    assert resultado.rede_utilizada is False
    assert resultado.banco_acessado is False
    assert resultado.flask_inicializado is False
    assert resultado.post_nfse_executado is False
    assert resultado.transmissao_executada is False


def test_h4f11_005_envelope_json_recupera_xml_assinado_exato():
    modulo = _modulo()

    resultado = modulo.executar_dry_run(
        agora=_agora(),
        material_a1=_material(),
        percentual_tot_trib_sn="6.00",
    )

    corpo = json.loads(
        resultado.corpo_json.decode(
            "utf-8"
        )
    )

    assert list(
        corpo
    ) == [
        "dpsXmlGZipB64",
    ]

    recuperado = gzip.decompress(
        base64.b64decode(
            corpo[
                "dpsXmlGZipB64"
            ],
            validate=True,
        )
    )

    assert recuperado == resultado.xml_assinado


def test_h4f11_006_corpo_gzip_e_deterministico_para_mesmo_xml():
    modulo = _modulo()

    material = _material()

    resultado = modulo.executar_dry_run(
        agora=_agora(),
        material_a1=material,
        percentual_tot_trib_sn="6.00",
    )

    primeiro = modulo._montar_corpo_json(
        resultado.xml_assinado
    )
    segundo = modulo._montar_corpo_json(
        resultado.xml_assinado
    )

    assert primeiro == segundo


def test_h4f11_007_xml_assinado_nao_e_persistido_pelo_script():
    texto = SCRIPT.read_text(
        encoding="utf-8"
    )

    assert ".write_bytes(" not in texto
    assert ".write_text(" not in texto
    assert "open(" not in texto


def test_h4f11_008_dry_run_rejeita_datetime_sem_timezone():
    modulo = _modulo()

    try:
        modulo.executar_dry_run(
            agora=datetime(
                2026,
                11,
                11,
                18,
                0,
                0,
            ),
            material_a1=_material(),
        )
    except modulo.DryRunDpsInvalido as exc:
        assert "timezone" in str(
            exc
        )
    else:
        raise AssertionError(
            "Datetime sem timezone deveria ser bloqueado."
        )



def test_h4f11_009_script_exige_percentual_simples_confirmado(
    monkeypatch,
):
    modulo = _modulo()

    monkeypatch.delenv(
        modulo.ENV_PTOTTRIBSN,
        raising=False,
    )

    try:
        modulo._percentual_tot_trib_sn()
    except modulo.DryRunDpsInvalido as exc:
        mensagem = str(
            exc
        )
    else:
        raise AssertionError(
            "pTotTribSN ausente deveria bloquear o dry-run."
        )

    assert "pTotTribSN" in mensagem
    assert modulo.ENV_PTOTTRIBSN in mensagem


def test_h4f11_010_xml_usa_ptottribsn_e_omite_paliq():
    modulo = _modulo()

    dps = modulo._montar_dps(
        agora=_agora(),
        percentual_tot_trib_sn="6.00",
    )

    xml = modulo.serializer.montar_xml_dps_serializado(
        dps,
        ambiente="HOMOLOGACAO",
    ).decode(
        "utf-8"
    )

    assert "<pTotTribSN>6.00</pTotTribSN>" in xml
    assert "<indTotTrib>" not in xml
    assert "<pAliq>" not in xml
    assert "<cTribNac>140101</cTribNac>" in xml
    assert "<cNBS>101061900</cNBS>" in xml
    assert "<cLocPrestacao>3541653</cLocPrestacao>" in xml
