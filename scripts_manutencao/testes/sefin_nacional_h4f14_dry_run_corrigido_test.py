"""H4-F14 - contrato do dry-run corrigido sem nova transmissão."""

from datetime import datetime, timedelta, timezone
import importlib.util
from pathlib import Path
import sys
from types import SimpleNamespace

from cryptography import x509
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID


SCRIPT = (
    Path(__file__).resolve().parents[1]
    / "sefin_nacional_h4f14_dry_run_corrigido.py"
)


def _modulo():
    nome = "h4f14_dry_run_corrigido_testado"
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
                "ERP JSP H4-F14 TESTE",
            ),
            x509.NameAttribute(
                NameOID.COMMON_NAME,
                "H4-F14",
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
        19,
        0,
        0,
        tzinfo=timezone(
            timedelta(
                hours=-3
            )
        ),
    )


def test_h4f14_001_percentual_confirmado_e_231():
    modulo = _modulo()

    assert modulo.PTOTTRIBSN_CONFIRMADO == "2.31"


def test_h4f14_002_nova_dps_nao_reutiliza_numero_primeiro_post():
    modulo = _modulo()

    assert (
        modulo.NUMERO_DPS_H4F14
        != modulo.h4f11.NUMERO_DPS_DRY_RUN
    )


def test_h4f14_003_dry_run_completo_valida_xsd_e_assinatura():
    modulo = _modulo()

    resultado = modulo.executar_dry_run_corrigido(
        agora=_agora(),
        material_a1=_material(),
    )

    assert resultado.xsd_antes_ok is True
    assert resultado.assinatura_ok is True
    assert resultado.xsd_depois_ok is True
    assert resultado.rede_utilizada is False
    assert resultado.post_nfse_executado is False
    assert resultado.transmissao_executada is False


def test_h4f14_004_xml_espelha_campos_confirmados_nfse_valida():
    modulo = _modulo()

    resultado = modulo.executar_dry_run_corrigido(
        agora=_agora(),
        material_a1=_material(),
    )

    xml = resultado.xml_assinado.decode(
        "utf-8"
    )

    assert "<pTotTribSN>2.31</pTotTribSN>" in xml
    assert "<indTotTrib>" not in xml
    assert "<pAliq>" not in xml
    assert "<IM>" not in xml
    assert "<xNome>" not in xml
    assert "<cTribNac>140101</cTribNac>" in xml
    assert "<cNBS>101061900</cNBS>" in xml
    assert "<cLocPrestacao>3541653</cLocPrestacao>" in xml
    assert "<opSimpNac>3</opSimpNac>" in xml
    assert "<regApTribSN>1</regApTribSN>" in xml
    assert "<regEspTrib>0</regEspTrib>" in xml
    assert "<tpRetISSQN>1</tpRetISSQN>" in xml
    assert "<tribISSQN>1</tribISSQN>" in xml


def test_h4f14_005_xml_identifica_novo_numero_dps():
    modulo = _modulo()

    resultado = modulo.executar_dry_run_corrigido(
        agora=_agora(),
        material_a1=_material(),
    )

    xml = resultado.xml_assinado.decode(
        "utf-8"
    )

    assert (
        "<nDPS>"
        + modulo.NUMERO_DPS_H4F14
        + "</nDPS>"
    ) in xml
    assert (
        "<nDPS>"
        + modulo.h4f11.NUMERO_DPS_DRY_RUN
        + "</nDPS>"
    ) not in xml


def test_h4f14_006_descricao_identifica_etapa_corrigida():
    modulo = _modulo()

    resultado = modulo.executar_dry_run_corrigido(
        agora=_agora(),
        material_a1=_material(),
    )

    xml = resultado.xml_assinado.decode(
        "utf-8"
    )

    assert "HOMOLOGACAO CONTROLADA H4-F14" in xml
    assert "ERP-JSP-H4F14" in xml


def test_h4f14_007_script_nao_possui_transporte():
    texto = SCRIPT.read_text(
        encoding="utf-8"
    ).lower()

    assert "import requests" not in texto
    assert "urllib.request" not in texto
    assert "http.client" not in texto
    assert "import socket" not in texto
    assert ".post(" not in texto
    assert 'method="post"' not in texto


def test_h4f14_008_nao_persiste_xml():
    texto = SCRIPT.read_text(
        encoding="utf-8"
    )

    assert ".write_bytes(" not in texto
    assert ".write_text(" not in texto
    assert "open(" not in texto
