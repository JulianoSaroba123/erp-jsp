"""H4-F15 - contrato de segurança do segundo POST corrigido."""

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
    / "sefin_nacional_h4f15_segundo_post.py"
)


def _modulo():
    nome = "h4f15_segundo_post_testado"
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
                "ERP JSP H4-F15 TESTE",
            ),
            x509.NameAttribute(
                NameOID.COMMON_NAME,
                "H4-F15",
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
        15,
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
            "versaoAplicativo": "SefinNacional_1.6.0",
            "dataHoraProcessamento": (
                "2026-11-11T19:15:01-03:00"
            ),
            "idDPS": (
                "DPS355450826629878800017299999999999999999998"
            )[:45],
            "erros": [
                {
                    "Codigo": "E-TESTE",
                    "Descricao": "Rejeicao controlada H4-F15",
                    "Complemento": "Detalhe de teste",
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
        b"<NFSeTesteH4F15/>"
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
            "versaoAplicativo": "SefinNacional_1.6.0",
            "dataHoraProcessamento": (
                "2026-11-11T19:15:01-03:00"
            ),
            "idDps": (
                "DPS355450826629878800017299999999999999999998"
            )[:45],
            "chaveAcesso": "8" * 50,
            "nfseXmlGZipB64": nfse_b64,
            "alertas": [],
        },
        separators=(",", ":"),
    ).encode(
        "utf-8"
    )


def test_h4f15_001_exige_confirmacao_propria(
    tmp_path,
):
    modulo = _modulo()

    with pytest.raises(
        modulo.SegundoPostSefinInvalido,
        match="H4-F15",
    ):
        modulo.executar_post_unico(
            confirmacao="POST_UNICO_PRODREST",
            caminho_marcador=(
                tmp_path
                / "marcador.json"
            ),
            agora=_agora(),
            material_a1=_material(),
        )


def test_h4f15_002_pregate_valida_payload_corrigido():
    modulo = _modulo()

    dry_run = modulo.h4f14.executar_dry_run_corrigido(
        agora=_agora(),
        material_a1=_material(),
    )

    modulo._validar_xml_corrigido(
        dry_run.xml_assinado
    )

    xml = dry_run.xml_assinado.decode(
        "utf-8"
    )

    assert "<nDPS>999999999999998</nDPS>" in xml
    assert "<pTotTribSN>2.31</pTotTribSN>" in xml
    assert "<indTotTrib>" not in xml
    assert "<pAliq>" not in xml
    assert "<IM>" not in xml
    assert "<xNome>" not in xml


def test_h4f15_003_pregate_bloqueia_payload_antigo():
    modulo = _modulo()

    xml = (
        b"<DPS>"
        b"<nDPS>999999999999999</nDPS>"
        b"<indTotTrib>0</indTotTrib>"
        b"</DPS>"
    )

    with pytest.raises(
        modulo.SegundoPostSefinInvalido,
        match="Pre-gate",
    ):
        modulo._validar_xml_corrigido(
            xml
        )


def test_h4f15_004_executa_um_unico_post_corrigido(
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
        / "h4f15.json"
    )

    resultado = modulo.executar_post_unico(
        confirmacao=modulo.CONFIRMACAO_EXIGIDA,
        session=SessaoFake(),
        caminho_marcador=marcador,
        agora=_agora(),
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

    corpo = json.loads(
        chamada[
            "data"
        ].decode(
            "utf-8"
        )
    )

    xml = gzip.decompress(
        base64.b64decode(
            corpo[
                "dpsXmlGZipB64"
            ],
            validate=True,
        )
    ).decode(
        "utf-8"
    )

    assert "<nDPS>999999999999998</nDPS>" in xml
    assert "<pTotTribSN>2.31</pTotTribSN>" in xml
    assert "<nDPS>999999999999999</nDPS>" not in xml

    assert resultado.status_code == 400
    assert resultado.classificacao == "REJEICAO_NEGOCIO"
    assert resultado.retry_automatico is False


def test_h4f15_005_marcador_e_distinto_do_h4f12():
    modulo = _modulo()

    id_dps = "DPS3554508TESTE"

    caminho_h4f15 = modulo._caminho_marcador_padrao(
        id_dps
    )

    caminho_h4f12 = modulo.h4f12._caminho_marcador_padrao(
        id_dps
    )

    assert caminho_h4f15 != caminho_h4f12
    assert "h4f15" in caminho_h4f15.name
    assert "h4f12" in caminho_h4f12.name


def test_h4f15_006_segunda_execucao_mesmo_marcador_e_bloqueada(
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
        / "h4f15.json"
    )

    kwargs = {
        "confirmacao": modulo.CONFIRMACAO_EXIGIDA,
        "session": SessaoFake(),
        "caminho_marcador": marcador,
        "agora": _agora(),
        "material_a1": _material(),
    }

    modulo.executar_post_unico(
        **kwargs
    )

    with pytest.raises(
        modulo.SegundoPostSefinInvalido,
        match="ja existe",
    ):
        modulo.executar_post_unico(
            **kwargs
        )

    assert len(
        chamadas
    ) == 1


def test_h4f15_007_timeout_nao_faz_retry(
    tmp_path,
):
    modulo = _modulo()
    chamadas = []

    class SessaoFake:
        def request(self, **kwargs):
            chamadas.append(
                kwargs
            )
            raise requests.exceptions.Timeout(
                "timeout teste"
            )

    marcador = (
        tmp_path
        / "h4f15.json"
    )

    with pytest.raises(
        modulo.SegundoPostSefinInvalido,
        match="NAO retransmitir",
    ):
        modulo.executar_post_unico(
            confirmacao=modulo.CONFIRMACAO_EXIGIDA,
            session=SessaoFake(),
            caminho_marcador=marcador,
            agora=_agora(),
            material_a1=_material(),
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


def test_h4f15_008_rejeicao_e_preservada_no_marcador(
    tmp_path,
):
    modulo = _modulo()

    class SessaoFake:
        def request(self, **kwargs):
            return SimpleNamespace(
                status_code=400,
                content=_json_400(),
            )

    marcador = (
        tmp_path
        / "h4f15.json"
    )

    resultado = modulo.executar_post_unico(
        confirmacao=modulo.CONFIRMACAO_EXIGIDA,
        session=SessaoFake(),
        caminho_marcador=marcador,
        agora=_agora(),
        material_a1=_material(),
    )

    assert resultado.resposta_normalizada is not None
    assert resultado.resposta_normalizada.erros[
        0
    ].codigo == "E-TESTE"

    dados = json.loads(
        marcador.read_text(
            encoding="utf-8"
        )
    )

    assert dados[
        "resposta_erro"
    ][
        "erros"
    ][
        0
    ][
        "Codigo"
    ] == "E-TESTE"


def test_h4f15_009_201_normaliza_nfse_gerada(
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
            / "h4f15.json"
        ),
        agora=_agora(),
        material_a1=_material(),
    )

    normalizada = resultado.resposta_normalizada

    assert resultado.status_code == 201
    assert resultado.classificacao == "NFSE_GERADA"
    assert normalizada is not None
    assert normalizada.sucesso is True
    assert normalizada.chave_acesso == (
        "8" * 50
    )
    assert normalizada.nfse_xml == (
        b"<?xml version='1.0' encoding='UTF-8'?>"
        b"<NFSeTesteH4F15/>"
    )


def test_h4f15_010_marcador_pre_rede_contem_dps_e_percentual(
    tmp_path,
):
    modulo = _modulo()
    marcador = (
        tmp_path
        / "h4f15.json"
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
            assert dados[
                "etapa"
            ] == "H4-F15"
            assert dados[
                "numero_dps"
            ] == "999999999999998"
            assert dados[
                "ptottribsn"
            ] == "2.31"

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
    )


def test_h4f15_011_nao_importa_app_flask_ou_banco():
    texto = SCRIPT.read_text(
        encoding="utf-8"
    ).lower()

    assert "from app" not in texto
    assert "import app" not in texto
    assert "create_app" not in texto
    assert "sqlalchemy" not in texto
    assert "db.session" not in texto
