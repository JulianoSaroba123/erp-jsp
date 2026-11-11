"""H4-F6 - assinatura real da DPS PRODREST 20261020 sem HTTP."""

from copy import deepcopy
from pathlib import Path
import runpy

import pytest
from lxml import etree

from app.fiscal.xsd import obter_caminho_xsd_dps
from app.fiscal.xml.dps_serializer import montar_xml_dps_serializado
from app.fiscal.xml.dps_signer import (
    AssinaturaXmlDpsInvalida,
    DSIG_NS,
    assinar_xml_dps,
    validar_assinatura_xml_dps,
)
from app.fiscal.xml.dps_xsd_validator import validar_xml_dps_xsd


def _dados():
    caminho = Path(__file__).with_name(
        "sefin_nacional_dps_b6_test.py"
    )
    namespace = runpy.run_path(str(caminho))
    return deepcopy(
        namespace["_dados_completos_xsd"]()
    )


def _material():
    caminho = Path(__file__).with_name(
        "sefin_nacional_dps_b8a2_signer_test.py"
    )
    namespace = runpy.run_path(str(caminho))
    return namespace["_material_rsa"]()


def _q(ns, nome):
    return f"{{{ns}}}{nome}"


def _xml_homologacao():
    return montar_xml_dps_serializado(
        _dados(),
        ambiente="HOMOLOGACAO",
    )


def test_h4f6_001_xml_nao_assinado_valida_prodrest():
    xml = _xml_homologacao()

    resultado = validar_xml_dps_xsd(
        xml,
        obter_caminho_xsd_dps(
            ambiente="HOMOLOGACAO"
        ),
    )

    assert resultado.valido is True, resultado.erros


def test_h4f6_002_assina_dps_real_e_valida_criptografia():
    material = _material()

    xml_assinado = assinar_xml_dps(
        _xml_homologacao(),
        material_certificado=material,
    )

    certificado = validar_assinatura_xml_dps(
        xml_assinado,
        certificado_esperado=material.certificado,
    )

    assert (
        certificado.serial_number
        == material.certificado.serial_number
    )


def test_h4f6_003_xml_assinado_valida_prodrest_20261020():
    material = _material()

    xml_assinado = assinar_xml_dps(
        _xml_homologacao(),
        material_certificado=material,
    )

    resultado = validar_xml_dps_xsd(
        xml_assinado,
        obter_caminho_xsd_dps(
            ambiente="HOMOLOGACAO"
        ),
    )

    assert resultado.valido is True, resultado.erros


def test_h4f6_004_signature_referencia_id_dps_oficial():
    xml_assinado = assinar_xml_dps(
        _xml_homologacao(),
        material_certificado=_material(),
    )

    raiz = etree.fromstring(
        xml_assinado
    )

    inf_dps = raiz[0]

    identificador = inf_dps.get("Id")

    assert identificador.startswith("DPS")
    assert len(identificador) == 45

    signature = raiz.find(
        _q(
            DSIG_NS,
            "Signature",
        )
    )

    assert signature is not None

    reference = signature.find(
        ".//" + _q(
            DSIG_NS,
            "Reference",
        )
    )

    assert reference is not None
    assert reference.get("URI") == f"#{identificador}"


def test_h4f6_005_adulteracao_pos_assinatura_e_bloqueada():
    material = _material()

    xml_assinado = assinar_xml_dps(
        _xml_homologacao(),
        material_certificado=material,
    )

    raiz = etree.fromstring(
        xml_assinado
    )

    descricao = raiz.find(
        ".//{http://www.sped.fazenda.gov.br/nfse}xDescServ"
    )

    assert descricao is not None

    descricao.text = (
        str(descricao.text or "")
        + " ALTERADO"
    )

    adulterado = etree.tostring(
        raiz,
        encoding="UTF-8",
        xml_declaration=True,
        pretty_print=False,
    )

    with pytest.raises(
        AssinaturaXmlDpsInvalida,
        match="DigestValue",
    ):
        validar_assinatura_xml_dps(
            adulterado
        )


def test_h4f6_006_id_legado_id_nao_e_aceito():
    xml = _xml_homologacao()

    raiz = etree.fromstring(
        xml
    )

    raiz[0].set(
        "Id",
        "ID" + "0" * 43,
    )

    invalido = etree.tostring(
        raiz,
        encoding="UTF-8",
        xml_declaration=True,
        pretty_print=False,
    )

    with pytest.raises(
        AssinaturaXmlDpsInvalida,
        match="deve iniciar com DPS",
    ):
        assinar_xml_dps(
            invalido,
            material_certificado=_material(),
        )
