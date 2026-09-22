import base64
import gzip
import json
from contextlib import contextmanager
from types import SimpleNamespace

import pytest

from app.fiscal.providers import sefin_nacional_emissao as emissao
from app.fiscal.xml.dps_signer import AssinaturaXmlDpsInvalida


XML_ASSINADO = (
    b'<?xml version="1.0" encoding="UTF-8"?>'
    b'<DPS xmlns="http://www.sped.fazenda.gov.br/nfse">'
    b'<infDPS Id="IDTESTE"/>'
    b'<Signature xmlns="http://www.w3.org/2000/09/xmldsig#"/>'
    b'</DPS>'
)


class ClienteFake:
    def __init__(self):
        self.chamadas = []

    def requisitar(self, **kwargs):
        self.chamadas.append(kwargs)

        return SimpleNamespace(
            status_code=201,
            conteudo=b'{"ok":true}',
            headers={},
            metodo="POST",
            url=kwargs["url"],
        )


def _assinatura_valida(monkeypatch):
    monkeypatch.setattr(
        emissao,
        "validar_assinatura_xml_dps",
        lambda xml: object(),
    )


def test_b8a3a3_001_monta_json_gzip_base64(monkeypatch):
    _assinatura_valida(monkeypatch)

    corpo = emissao.montar_corpo_emissao_nfse(
        XML_ASSINADO
    )

    dados = json.loads(
        corpo.decode("utf-8")
    )

    assert list(dados) == [
        "dpsXmlGZipB64",
    ]

    comprimido = base64.b64decode(
        dados["dpsXmlGZipB64"],
        validate=True,
    )

    recuperado = gzip.decompress(
        comprimido
    )

    assert recuperado == XML_ASSINADO


def test_b8a3a3_002_corpo_deterministico(monkeypatch):
    _assinatura_valida(monkeypatch)

    primeiro = emissao.montar_corpo_emissao_nfse(
        XML_ASSINADO
    )

    segundo = emissao.montar_corpo_emissao_nfse(
        XML_ASSINADO
    )

    assert primeiro == segundo


def test_b8a3a3_003_bloqueia_xml_sem_assinatura_valida(
    monkeypatch,
):
    def falhar(xml):
        raise AssinaturaXmlDpsInvalida(
            "teste"
        )

    monkeypatch.setattr(
        emissao,
        "validar_assinatura_xml_dps",
        falhar,
    )

    with pytest.raises(
        emissao.PreparacaoEmissaoSefinInvalida,
        match="XMLDSIG valida",
    ):
        emissao.montar_corpo_emissao_nfse(
            XML_ASSINADO
        )


def test_b8a3a3_004_executa_post_homologacao(monkeypatch):
    _assinatura_valida(monkeypatch)

    monkeypatch.setenv(
        "NFSE_SEFIN_BASE_URL_HOMOLOGACAO",
        "https://sefin.teste/SefinNacional",
    )

    material = object()
    cliente = ClienteFake()

    caminhos = (
        "cert-teste.pem",
        "key-teste.pem",
    )

    @contextmanager
    def mtls_fake(material_recebido):
        assert material_recebido is material
        yield caminhos

    monkeypatch.setattr(
        emissao,
        "materializar_mtls_sefin",
        mtls_fake,
    )

    resposta = emissao.executar_emissao_nfse_http(
        xml_dps_assinado=XML_ASSINADO,
        ambiente="HOMOLOGACAO",
        material_certificado=material,
        cliente_http=cliente,
    )

    assert resposta.status_code == 201
    assert len(cliente.chamadas) == 1

    chamada = cliente.chamadas[0]

    assert chamada["metodo"] == "POST"

    assert chamada["url"] == (
        "https://sefin.teste/"
        "SefinNacional/nfse"
    )

    assert chamada["certificado_cliente"] == caminhos

    assert chamada["headers"] == {
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    dados = json.loads(
        chamada["conteudo"].decode("utf-8")
    )

    assert "dpsXmlGZipB64" in dados


def test_b8a3a3_005_nao_chama_http_se_assinatura_falhar(
    monkeypatch,
):
    monkeypatch.setenv(
        "NFSE_SEFIN_BASE_URL_HOMOLOGACAO",
        "https://sefin.teste/SefinNacional",
    )

    def falhar(xml):
        raise AssinaturaXmlDpsInvalida(
            "teste"
        )

    monkeypatch.setattr(
        emissao,
        "validar_assinatura_xml_dps",
        falhar,
    )

    cliente = ClienteFake()

    with pytest.raises(
        emissao.PreparacaoEmissaoSefinInvalida,
    ):
        emissao.executar_emissao_nfse_http(
            xml_dps_assinado=XML_ASSINADO,
            ambiente="HOMOLOGACAO",
            material_certificado=object(),
            cliente_http=cliente,
        )

    assert cliente.chamadas == []


def test_b8a3a3_006_exige_bytes():
    with pytest.raises(
        emissao.PreparacaoEmissaoSefinInvalida,
        match="bytes",
    ):
        emissao.montar_corpo_emissao_nfse(
            "<DPS/>"
        )


def test_b8a3a3_007_exige_xml_nao_vazio():
    with pytest.raises(
        emissao.PreparacaoEmissaoSefinInvalida,
        match="vazio",
    ):
        emissao.montar_corpo_emissao_nfse(
            b""
        )
