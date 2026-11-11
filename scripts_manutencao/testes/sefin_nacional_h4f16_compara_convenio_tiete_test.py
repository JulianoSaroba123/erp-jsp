"""H4-F16 - contrato da comparação read-only do convênio de Tietê."""

from datetime import datetime, timedelta, timezone
import importlib.util
import json
from pathlib import Path
import sys
from types import SimpleNamespace

from cryptography import x509
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID
import pytest
import requests


SCRIPT = (
    Path(__file__).resolve().parents[1]
    / "sefin_nacional_h4f16_compara_convenio_tiete.py"
)


def _modulo():
    nome = "h4f16_compara_convenio_testado"
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
                "ERP JSP H4-F16 TESTE",
            ),
            x509.NameAttribute(
                NameOID.COMMON_NAME,
                "H4-F16",
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


def _resp(
    status,
    dados,
):
    return SimpleNamespace(
        status_code=status,
        content=(
            json.dumps(
                dados,
                separators=(",", ":"),
            ).encode(
                "utf-8"
            )
            if dados is not None
            else b""
        ),
    )


def test_h4f16_001_script_e_somente_get():
    texto = SCRIPT.read_text(
        encoding="utf-8"
    )

    assert 'method="GET"' in texto
    assert 'method="POST"' not in texto
    assert ".post(" not in texto
    assert "create_app" not in texto
    assert "sqlalchemy" not in texto
    assert "db.session" not in texto


def test_h4f16_002_urls_apontam_para_parametrizacao_oficial():
    modulo = _modulo()

    assert modulo.URL_PRODREST == (
        "https://adn.producaorestrita.nfse.gov.br"
        "/parametrizacao/3554508/convenio"
    )
    assert modulo.URL_PRODUCAO == (
        "https://adn.nfse.gov.br"
        "/parametrizacao/3554508/convenio"
    )


def test_h4f16_003_compara_200_200():
    modulo = _modulo()

    class SessaoProdRest:
        def request(self, **kwargs):
            return _resp(
                200,
                {
                    "mensagem": "Convenio ativo em teste",
                    "tipoAmbiente": 2,
                },
            )

    class SessaoProducao:
        def request(self, **kwargs):
            return _resp(
                200,
                {
                    "mensagem": "Convenio ativo em producao",
                    "tipoAmbiente": 1,
                },
            )

    resultado = modulo.executar_comparacao(
        session_prodrest=SessaoProdRest(),
        session_producao=SessaoProducao(),
        material_a1=_material(),
    )

    assert resultado[
        "diagnostico"
    ] == "CONVENIO_RESPONDE_NOS_DOIS_AMBIENTES"
    assert resultado[
        "post_executado"
    ] is False
    assert resultado[
        "emissao_executada"
    ] is False


def test_h4f16_004_detecta_divergencia_404_200():
    modulo = _modulo()

    class SessaoProdRest:
        def request(self, **kwargs):
            return _resp(
                404,
                {
                    "mensagem": (
                        "Municipio inexistente no cadastro de convenio."
                    ),
                },
            )

    class SessaoProducao:
        def request(self, **kwargs):
            return _resp(
                200,
                {
                    "mensagem": "Convenio ativo",
                },
            )

    resultado = modulo.executar_comparacao(
        session_prodrest=SessaoProdRest(),
        session_producao=SessaoProducao(),
    )

    assert resultado[
        "diagnostico"
    ] == "DIVERGENCIA_AMBIENTAL_PROVAVEL"


def test_h4f16_005_preserva_mensagem_da_api():
    modulo = _modulo()

    resumo = modulo._resumo_resposta(
        ambiente="PRODUCAO_RESTRITA",
        resposta=_resp(
            400,
            {
                "Mensagem": "Convênio ainda não ativo",
                "tipoAmbiente": 2,
            },
        ),
    )

    assert resumo[
        "mensagem"
    ] == "Convênio ainda não ativo"
    assert resumo[
        "status_code"
    ] == 400


def test_h4f16_006_request_nao_envia_corpo():
    modulo = _modulo()
    chamadas = []

    class Sessao:
        def request(self, **kwargs):
            chamadas.append(
                kwargs
            )
            return _resp(
                200,
                {
                    "mensagem": "OK",
                },
            )

    modulo._consultar(
        url=modulo.URL_PRODREST,
        ambiente="PRODUCAO_RESTRITA",
        session=Sessao(),
        material_a1=_material(),
    )

    assert len(
        chamadas
    ) == 1

    chamada = chamadas[
        0
    ]

    assert chamada[
        "method"
    ] == "GET"
    assert "data" not in chamada
    assert "json" not in chamada
    assert chamada[
        "verify"
    ] is True
    assert chamada[
        "allow_redirects"
    ] is False
    assert chamada[
        "cert"
    ]


def test_h4f16_007_timeout_e_controlado():
    modulo = _modulo()

    class Sessao:
        def request(self, **kwargs):
            raise requests.exceptions.Timeout(
                "timeout teste"
            )

    with pytest.raises(
        modulo.ComparacaoConvenioInvalida,
        match="timeout",
    ):
        modulo._consultar(
            url=modulo.URL_PRODREST,
            ambiente="PRODUCAO_RESTRITA",
            session=Sessao(),
            material_a1=_material(),
        )


def test_h4f16_008_codigo_tiete_e_3554508():
    modulo = _modulo()

    assert modulo.CODIGO_MUNICIPIO == "3554508"
