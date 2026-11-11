"""H4-F13 - contrato da consulta read-only de NFS-e em Produção."""

import base64
from contextlib import contextmanager
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


SCRIPT = (
    Path(__file__).resolve().parents[1]
    / "sefin_nacional_h4f13_consulta_nfse_producao.py"
)


def _modulo():
    nome = "h4f13_consulta_nfse_producao_testado"
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
                "ERP JSP H4-F13 TESTE",
            ),
            x509.NameAttribute(
                NameOID.COMMON_NAME,
                "H4-F13",
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


def _xml():
    return b"""<?xml version="1.0" encoding="UTF-8"?>
<NFSe xmlns="http://www.sped.fazenda.gov.br/nfse">
  <infNFSe>
    <DPS>
      <infDPS>
        <prest>
          <regTrib>
            <opSimpNac>3</opSimpNac>
            <regApTribSN>1</regApTribSN>
            <regEspTrib>0</regEspTrib>
          </regTrib>
        </prest>
        <serv>
          <cServ>
            <cTribNac>140101</cTribNac>
            <cNBS>101061900</cNBS>
          </cServ>
          <locPrest>
            <cLocPrestacao>3541653</cLocPrestacao>
          </locPrest>
        </serv>
        <valores>
          <vServPrest>
            <vServ>500.00</vServ>
          </vServPrest>
          <trib>
            <tribMun>
              <tribISSQN>1</tribISSQN>
              <tpRetISSQN>1</tpRetISSQN>
            </tribMun>
            <totTrib>
              <pTotTribSN>7.70</pTotTribSN>
            </totTrib>
          </trib>
        </valores>
      </infDPS>
    </DPS>
  </infNFSe>
</NFSe>
"""


def _resposta_json():
    valor = base64.b64encode(
        gzip.compress(
            _xml(),
            compresslevel=9,
            mtime=0,
        )
    ).decode(
        "ascii"
    )

    return json.dumps(
        {
            "nfseXmlGZipB64": valor,
        },
        separators=(",", ":"),
    ).encode(
        "utf-8"
    )


def test_h4f13_001_script_e_somente_get():
    texto = SCRIPT.read_text(
        encoding="utf-8"
    )

    assert 'method="GET"' in texto
    assert 'method="POST"' not in texto
    assert ".post(" not in texto
    assert "/eventos" not in texto
    assert "create_app" not in texto
    assert "sqlalchemy" not in texto
    assert "db.session" not in texto


def test_h4f13_002_exige_chave_com_50_digitos():
    modulo = _modulo()

    with pytest.raises(
        modulo.ConsultaNfseProducaoInvalida,
        match="50 digitos",
    ):
        modulo._chave_acesso(
            "123"
        )

    assert modulo._chave_acesso(
        "9" * 50
    ) == (
        "9" * 50
    )


def test_h4f13_003_extrai_xml_de_json_gzip_base64():
    modulo = _modulo()

    xml = modulo._extrair_xml(
        conteudo=_resposta_json(),
        content_type="application/json",
    )

    assert xml == _xml()


def test_h4f13_004_aceita_xml_direto():
    modulo = _modulo()

    xml = modulo._extrair_xml(
        conteudo=_xml(),
        content_type="application/xml",
    )

    assert xml == _xml()


def test_h4f13_005_inspeciona_campos_tributarios():
    modulo = _modulo()

    campos = modulo._inspecionar_xml(
        _xml()
    )

    assert campos[
        "pTotTribSN"
    ] == "7.70"
    assert campos[
        "indTotTrib"
    ] is None
    assert campos[
        "pAliq"
    ] is None
    assert campos[
        "IM"
    ] is None
    assert campos[
        "xNome"
    ] is None
    assert campos[
        "cTribNac"
    ] == "140101"
    assert campos[
        "cNBS"
    ] == "101061900"
    assert campos[
        "cLocPrestacao"
    ] == "3541653"
    assert campos[
        "opSimpNac"
    ] == "3"
    assert campos[
        "regApTribSN"
    ] == "1"
    assert campos[
        "regEspTrib"
    ] == "0"
    assert campos[
        "tpRetISSQN"
    ] == "1"
    assert campos[
        "tribISSQN"
    ] == "1"
    assert campos[
        "vServ"
    ] == "500.00"


def test_h4f13_006_executa_um_unico_get_sem_mutacao(
    monkeypatch,
):
    modulo = _modulo()

    chamadas = []

    @contextmanager
    def materializar(*args, **kwargs):
        yield (
            "cert-teste.pem",
            "key-teste.pem",
        )

    monkeypatch.setattr(
        modulo.h4f9,
        "_materializar_mtls",
        materializar,
    )

    class SessaoFake:
        def request(self, **kwargs):
            chamadas.append(
                kwargs
            )
            return SimpleNamespace(
                status_code=200,
                content=_resposta_json(),
                headers={
                    "Content-Type": "application/json",
                },
            )

    resultado = modulo.consultar_nfse(
        chave_acesso="9" * 50,
        session=SessaoFake(),
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
    assert chamada[
        "url"
    ] == (
        modulo.BASE_PRODUCAO
        + "/nfse/"
        + "9" * 50
    )
    assert chamada[
        "allow_redirects"
    ] is False
    assert chamada[
        "verify"
    ] is True
    assert "data" not in chamada
    assert "json" not in chamada
    assert "files" not in chamada

    assert resultado[
        "post_executado"
    ] is False
    assert resultado[
        "evento_executado"
    ] is False
    assert resultado[
        "banco_acessado"
    ] is False
    assert resultado[
        "flask_inicializado"
    ] is False


def test_h4f13_007_status_nao_200_nao_faz_retry(
    monkeypatch,
):
    modulo = _modulo()

    chamadas = []

    @contextmanager
    def materializar(*args, **kwargs):
        yield (
            "cert-teste.pem",
            "key-teste.pem",
        )

    monkeypatch.setattr(
        modulo.h4f9,
        "_materializar_mtls",
        materializar,
    )

    class SessaoFake:
        def request(self, **kwargs):
            chamadas.append(
                kwargs
            )
            return SimpleNamespace(
                status_code=404,
                content=b"",
                headers={},
            )

    with pytest.raises(
        modulo.ConsultaNfseProducaoInvalida,
        match="HTTP 404",
    ):
        modulo.consultar_nfse(
            chave_acesso="9" * 50,
            session=SessaoFake(),
            material_a1=_material(),
        )

    assert len(
        chamadas
    ) == 1


def test_h4f13_008_nao_persiste_xml_ou_resposta():
    texto = SCRIPT.read_text(
        encoding="utf-8"
    )

    assert ".write_bytes(" not in texto
    assert ".write_text(" not in texto
    assert "open(" not in texto
