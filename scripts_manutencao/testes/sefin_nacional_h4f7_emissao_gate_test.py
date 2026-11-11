"""H4-F7 - empacotamento e gate XSD imediatamente antes da rede."""

import base64
from contextlib import contextmanager
import gzip
import json
from pathlib import Path
import runpy
from types import SimpleNamespace

import pytest
from lxml import etree

from app.fiscal.providers import sefin_nacional_emissao as emissao
from app.fiscal.providers.sefin_nacional_emissao import (
    PreparacaoEmissaoSefinInvalida,
    montar_corpo_emissao_nfse,
)
from app.fiscal.xsd import obter_caminho_xsd_dps
from app.fiscal.xml.dps_signer import assinar_xml_dps


def _helpers_h4f6():
    caminho = Path(__file__).with_name(
        "sefin_nacional_xsd_h4f6_assinatura_test.py"
    )
    return runpy.run_path(str(caminho))


def _xml_assinado_valido():
    helpers = _helpers_h4f6()
    material = helpers["_material"]()
    xml = helpers["_xml_homologacao"]()

    return (
        assinar_xml_dps(
            xml,
            material_certificado=material,
        ),
        material,
    )


def _xml_assinado_fora_xsd():
    helpers = _helpers_h4f6()
    material = helpers["_material"]()
    xml = helpers["_xml_homologacao"]()

    raiz = etree.fromstring(xml)

    ns = "http://www.sped.fazenda.gov.br/nfse"
    c_loc_emi = raiz.find(
        f".//{{{ns}}}cLocEmi"
    )

    assert c_loc_emi is not None

    pai = c_loc_emi.getparent()
    pai.remove(c_loc_emi)

    invalido = etree.tostring(
        raiz,
        encoding="UTF-8",
        xml_declaration=True,
        pretty_print=False,
    )

    return (
        assinar_xml_dps(
            invalido,
            material_certificado=material,
        ),
        material,
    )


def test_h4f7_001_json_gzip_base64_recupera_xml_exato():
    xml_assinado, _ = _xml_assinado_valido()

    corpo = montar_corpo_emissao_nfse(
        xml_assinado,
        caminho_xsd=obter_caminho_xsd_dps(
            ambiente="HOMOLOGACAO"
        ),
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

    assert gzip.decompress(
        comprimido
    ) == xml_assinado


def test_h4f7_002_corpo_e_deterministico_com_xml_real():
    xml_assinado, _ = _xml_assinado_valido()
    xsd = obter_caminho_xsd_dps(
        ambiente="HOMOLOGACAO"
    )

    primeiro = montar_corpo_emissao_nfse(
        xml_assinado,
        caminho_xsd=xsd,
    )

    segundo = montar_corpo_emissao_nfse(
        xml_assinado,
        caminho_xsd=xsd,
    )

    assert primeiro == segundo


def test_h4f7_003_assinado_valido_mas_fora_xsd_e_bloqueado():
    xml_assinado, _ = _xml_assinado_fora_xsd()

    with pytest.raises(
        PreparacaoEmissaoSefinInvalida,
        match="invalido perante o XSD",
    ):
        montar_corpo_emissao_nfse(
            xml_assinado,
            caminho_xsd=obter_caminho_xsd_dps(
                ambiente="HOMOLOGACAO"
            ),
        )


def test_h4f7_004_xsd_invalido_nao_materializa_mtls_nem_http(
    monkeypatch,
):
    xml_assinado, material = _xml_assinado_fora_xsd()

    monkeypatch.setenv(
        "NFSE_SEFIN_BASE_URL_HOMOLOGACAO",
        "https://sefin.teste/SefinNacional",
    )

    chamadas_http = []

    class ClienteProibido:
        def requisitar(self, **kwargs):
            chamadas_http.append(kwargs)
            raise AssertionError(
                "HTTP nao pode ser chamado com XML fora do XSD."
            )

    @contextmanager
    def mtls_proibido(material_recebido):
        raise AssertionError(
            "mTLS nao pode ser materializado com XML fora do XSD."
        )
        yield None

    monkeypatch.setattr(
        emissao,
        "materializar_mtls_sefin",
        mtls_proibido,
    )

    with pytest.raises(
        PreparacaoEmissaoSefinInvalida,
        match="invalido perante o XSD",
    ):
        emissao.executar_emissao_nfse_http(
            xml_dps_assinado=xml_assinado,
            ambiente="HOMOLOGACAO",
            material_certificado=material,
            cliente_http=ClienteProibido(),
        )

    assert chamadas_http == []


def test_h4f7_005_xml_valido_chega_fronteira_http_sem_rede_real(
    monkeypatch,
):
    xml_assinado, material = _xml_assinado_valido()

    monkeypatch.setenv(
        "NFSE_SEFIN_BASE_URL_HOMOLOGACAO",
        "https://sefin.teste/SefinNacional",
    )

    caminhos = (
        "cert-h4f7.pem",
        "key-h4f7.pem",
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

    chamadas = []

    class ClienteFake:
        def requisitar(self, **kwargs):
            chamadas.append(kwargs)
            return SimpleNamespace(
                status_code=201,
                conteudo=b'{"ok":true}',
                headers={},
                metodo="POST",
                url=kwargs["url"],
            )

    resposta = emissao.executar_emissao_nfse_http(
        xml_dps_assinado=xml_assinado,
        ambiente="HOMOLOGACAO",
        material_certificado=material,
        cliente_http=ClienteFake(),
    )

    assert resposta.status_code == 201
    assert len(chamadas) == 1

    chamada = chamadas[0]

    assert chamada["metodo"] == "POST"
    assert chamada["url"].endswith(
        "/SefinNacional/nfse"
    )
    assert chamada["certificado_cliente"] == caminhos

    dados = json.loads(
        chamada["conteudo"].decode("utf-8")
    )

    assert gzip.decompress(
        base64.b64decode(
            dados["dpsXmlGZipB64"],
            validate=True,
        )
    ) == xml_assinado
