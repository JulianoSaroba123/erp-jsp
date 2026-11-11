"""H4-F12 - contrato de seguranca do primeiro POST /nfse."""

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
import pytest
import requests


SCRIPT = (
    Path(__file__).resolve().parents[1]
    / "sefin_nacional_h4f12_primeiro_post.py"
)


def _modulo():
    nome = "h4f12_primeiro_post_testado"
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
                "ERP JSP H4-F12 TESTE",
            ),
            x509.NameAttribute(
                NameOID.COMMON_NAME,
                "H4-F12",
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
        30,
        0,
        tzinfo=timezone(
            timedelta(
                hours=-3
            )
        ),
    )


def _json_400():
    return json.dumps(
        {
            "tipoAmbiente": 2,
            "versaoAplicativo": "SEFIN-TESTE",
            "dataHoraProcessamento": (
                "2026-11-11T18:30:01-03:00"
            ),
            "idDPS": (
                "DPS355450826629878800017299999999999999999999"
            )[:45],
            "erros": [
                {
                    "Codigo": "TESTE",
                    "Descricao": (
                        "Rejeicao de negocio controlada"
                    ),
                    "Complemento": None,
                }
            ],
        },
        separators=(",", ":"),
    ).encode(
        "utf-8"
    )


def _json_201():
    nfse_xml = (
        b"<?xml version='1.0' encoding='UTF-8'?>"
        b"<NFSeTeste/>"
    )

    nfse_b64 = base64.b64encode(
        gzip.compress(
            nfse_xml,
            compresslevel=9,
            mtime=0,
        )
    ).decode(
        "ascii"
    )

    return json.dumps(
        {
            "tipoAmbiente": 2,
            "versaoAplicativo": "SEFIN-TESTE",
            "dataHoraProcessamento": (
                "2026-11-11T18:30:01-03:00"
            ),
            "idDps": (
                "DPS355450826629878800017299999999999999999999"
            )[:45],
            "chaveAcesso": "9" * 50,
            "nfseXmlGZipB64": nfse_b64,
            "alertas": [],
        },
        separators=(",", ":"),
    ).encode(
        "utf-8"
    )


def test_h4f12_001_exige_confirmacao_exata(
    tmp_path,
):
    modulo = _modulo()

    with pytest.raises(
        modulo.PrimeiroPostSefinInvalido,
        match="Confirmacao explicita",
    ):
        modulo.executar_post_unico(
            confirmacao="NAO",
            caminho_marcador=(
                tmp_path
                / "marcador.json"
            ),
            agora=_agora(),
            material_a1=_material(),
            percentual_tot_trib_sn="6.00",
        )


def test_h4f12_002_executa_um_unico_post_sem_retry(
    tmp_path,
):
    modulo = _modulo()

    chamadas = []

    class SessaoFake:
        def request(self, **kwargs):
            chamadas.append(
                kwargs
            )
            return SimpleNamespace(
                status_code=400,
                content=_json_400(),
            )

    marcador = (
        tmp_path
        / "marcador.json"
    )

    resultado = modulo.executar_post_unico(
        confirmacao=modulo.CONFIRMACAO_EXIGIDA,
        session=SessaoFake(),
        caminho_marcador=marcador,
        agora=_agora(),
        material_a1=_material(),
        percentual_tot_trib_sn="6.00",
    )

    assert len(
        chamadas
    ) == 1

    chamada = chamadas[
        0
    ]

    assert chamada[
        "method"
    ] == "POST"
    assert chamada[
        "url"
    ] == modulo.ENDPOINT_ESPERADO
    assert chamada[
        "allow_redirects"
    ] is False
    assert chamada[
        "verify"
    ] is True
    assert chamada[
        "data"
    ]
    assert chamada[
        "headers"
    ][
        "Content-Type"
    ] == "application/json"

    assert resultado.status_code == 400
    assert resultado.classificacao == (
        "REJEICAO_NEGOCIO"
    )
    assert resultado.post_nfse_executado is True
    assert resultado.retry_automatico is False
    assert resultado.banco_acessado is False
    assert resultado.flask_inicializado is False

    dados = json.loads(
        marcador.read_text(
            encoding="utf-8"
        )
    )

    assert dados[
        "fase"
    ] == "RESPOSTA_RECEBIDA"
    assert dados[
        "status_code"
    ] == 400
    assert dados[
        "retry_automatico"
    ] is False
    assert dados[
        "resposta_erro"
    ][
        "erros"
    ][
        0
    ][
        "Codigo"
    ] == "TESTE"
    assert dados[
        "resposta_erro"
    ][
        "erros"
    ][
        0
    ][
        "Descricao"
    ] == "Rejeicao de negocio controlada"


def test_h4f12_003_segunda_execucao_mesmo_marcador_e_bloqueada(
    tmp_path,
):
    modulo = _modulo()

    chamadas = []

    class SessaoFake:
        def request(self, **kwargs):
            chamadas.append(
                kwargs
            )
            return SimpleNamespace(
                status_code=400,
                content=_json_400(),
            )

    marcador = (
        tmp_path
        / "marcador.json"
    )

    kwargs = {
        "confirmacao": modulo.CONFIRMACAO_EXIGIDA,
        "session": SessaoFake(),
        "caminho_marcador": marcador,
        "agora": _agora(),
        "material_a1": _material(),
        "percentual_tot_trib_sn": "6.00",
    }

    modulo.executar_post_unico(
        **kwargs
    )

    with pytest.raises(
        modulo.PrimeiroPostSefinInvalido,
        match="ja existe",
    ):
        modulo.executar_post_unico(
            **kwargs
        )

    assert len(
        chamadas
    ) == 1


def test_h4f12_004_timeout_nao_repete_e_marca_ambiguo(
    tmp_path,
):
    modulo = _modulo()

    chamadas = []

    class SessaoFake:
        def request(self, **kwargs):
            chamadas.append(
                kwargs
            )
            raise requests.Timeout(
                "timeout teste"
            )

    marcador = (
        tmp_path
        / "marcador.json"
    )

    with pytest.raises(
        modulo.PrimeiroPostSefinInvalido,
        match="NAO retransmitir",
    ):
        modulo.executar_post_unico(
            confirmacao=modulo.CONFIRMACAO_EXIGIDA,
            session=SessaoFake(),
            caminho_marcador=marcador,
            agora=_agora(),
            material_a1=_material(),
            percentual_tot_trib_sn="6.00",
        )

    assert len(
        chamadas
    ) == 1

    dados = json.loads(
        marcador.read_text(
            encoding="utf-8"
        )
    )

    assert dados[
        "fase"
    ] == "RESULTADO_AMBIGUO"
    assert dados[
        "retry_automatico"
    ] is False


def test_h4f12_005_201_e_normalizado_com_nfse(
    tmp_path,
):
    modulo = _modulo()

    class SessaoFake:
        def request(self, **kwargs):
            return SimpleNamespace(
                status_code=201,
                content=_json_201(),
            )

    resultado = modulo.executar_post_unico(
        confirmacao=modulo.CONFIRMACAO_EXIGIDA,
        session=SessaoFake(),
        caminho_marcador=(
            tmp_path
            / "marcador.json"
        ),
        agora=_agora(),
        material_a1=_material(),
        percentual_tot_trib_sn="6.00",
    )

    assert resultado.status_code == 201
    assert resultado.classificacao == (
        "NFSE_GERADA"
    )
    assert resultado.resposta_normalizada is not None
    assert resultado.resposta_normalizada.sucesso is True
    assert resultado.resposta_normalizada.nfse_xml == (
        b"<?xml version='1.0' encoding='UTF-8'?>"
        b"<NFSeTeste/>"
    )


def test_h4f12_006_400_e_normalizado_com_erros(
    tmp_path,
):
    modulo = _modulo()

    class SessaoFake:
        def request(self, **kwargs):
            return SimpleNamespace(
                status_code=400,
                content=_json_400(),
            )

    resultado = modulo.executar_post_unico(
        confirmacao=modulo.CONFIRMACAO_EXIGIDA,
        session=SessaoFake(),
        caminho_marcador=(
            tmp_path
            / "marcador.json"
        ),
        agora=_agora(),
        material_a1=_material(),
        percentual_tot_trib_sn="6.00",
    )

    normalizada = (
        resultado.resposta_normalizada
    )

    assert normalizada is not None
    assert normalizada.sucesso is False
    assert len(
        normalizada.erros
    ) == 1
    assert normalizada.erros[
        0
    ].codigo == "TESTE"


@pytest.mark.parametrize(
    ("status", "esperado"),
    [
        (
            201,
            "NFSE_GERADA",
        ),
        (
            400,
            "REJEICAO_NEGOCIO",
        ),
        (
            401,
            "AUTENTICACAO_REJEITADA",
        ),
        (
            403,
            "AUTENTICACAO_REJEITADA",
        ),
        (
            500,
            "SERVICO_INDISPONIVEL_OU_TRANSITORIO",
        ),
        (
            503,
            "SERVICO_INDISPONIVEL_OU_TRANSITORIO",
        ),
    ],
)
def test_h4f12_007_classificacao_status(
    status,
    esperado,
):
    modulo = _modulo()

    assert modulo._classificar_status(
        status
    ) == esperado


def test_h4f12_008_script_nao_importa_app_flask_ou_banco():
    texto = SCRIPT.read_text(
        encoding="utf-8"
    ).lower()

    assert "from app" not in texto
    assert "import app" not in texto
    assert "create_app" not in texto
    assert "sqlalchemy" not in texto
    assert "db.session" not in texto


def test_h4f12_009_marcador_e_criado_antes_da_rede(
    tmp_path,
):
    modulo = _modulo()

    marcador = (
        tmp_path
        / "marcador.json"
    )

    class SessaoFake:
        def request(self, **kwargs):
            assert marcador.exists()

            dados = json.loads(
                marcador.read_text(
                    encoding="utf-8"
                )
            )

            assert dados[
                "fase"
            ] == "PRE_REDE"

            return SimpleNamespace(
                status_code=400,
                content=_json_400(),
            )

    modulo.executar_post_unico(
        confirmacao=modulo.CONFIRMACAO_EXIGIDA,
        session=SessaoFake(),
        caminho_marcador=marcador,
        agora=_agora(),
        material_a1=_material(),
        percentual_tot_trib_sn="6.00",
    )
