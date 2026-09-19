from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

from cryptography import x509
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID
from lxml import etree

from app.fiscal.providers import obter_provider
from app.fiscal.providers.geisweb_tiete_preparacao import (
    preparar_payload_geisweb_com_xml,
)
from app.fiscal.providers.geisweb_tiete_signer import (
    NS_DSIG,
    NS_SIGN,
    assinar_xml_geisweb,
    validar_assinatura_xml_geisweb,
)
from app.fiscal.providers.geisweb_tiete_xsd_sign import (
    validar_xml_envio_sign_lote_rps,
)


def _documento():
    return SimpleNamespace(
        id=10,
        serie_rps="A",
        numero_rps=7,
    )


def _ordem():
    return SimpleNamespace(
        id=20,
    )


def _institucional():
    return SimpleNamespace(
        id=30,
        cnpj="11.111.111/0001-91",
        razao_social="EMPRESA TESTE",
    )


def _fiscal():
    return SimpleNamespace(
        configuracao_id=30,
        provider="GEISWEB_TIETE",
        ambiente="HOMOLOGACAO",
        municipio_ibge="3554508",
        integracao_ativa=False,
        inscricao_municipal="14180",
        aliquota_iss_padrao="2.00",
        codigo_servico_municipal="140601",
        codigo_lc116="1406",
    )


def _tomador():
    return {
        "tipo_documento": "CNPJ",
        "documento": "22.222.222/0001-91",
        "nome": "CLIENTE TESTE",
        "email": "cliente@example.com",
        "endereco": {
            "cep": "18530000",
            "logradouro": "RUA TESTE",
            "numero": "100",
            "complemento": "",
            "bairro": "CENTRO",
            "cidade": "TIETE",
            "uf": "SP",
            "pais": "BR",
        },
    }


def _servico():
    return {
        "codigo_lista_nacional": "1406",
        "codigo_tributacao_municipal": "140601",
        "nbs": "",
        "descricao": "SERVICO TESTE",
        "municipio_incidencia_ibge": "3554508",
        "municipio_prestacao_ibge": "3554508",
    }


def _valores():
    return {
        "valor_servicos": "100.00",
        "valor_recebido": None,
        "desconto_incondicionado": "0.00",
        "desconto_condicionado": "0.00",
        "deducoes": "0.00",
    }


def _material_certificado():
    chave = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
    )

    agora = datetime.now(
        timezone.utc
    )

    nome = x509.Name([
        x509.NameAttribute(
            NameOID.COMMON_NAME,
            "GEISWEB TESTE LOCAL",
        )
    ])

    certificado = (
        x509.CertificateBuilder()
        .subject_name(nome)
        .issuer_name(nome)
        .public_key(
            chave.public_key()
        )
        .serial_number(
            x509.random_serial_number()
        )
        .not_valid_before(
            agora - timedelta(days=1)
        )
        .not_valid_after(
            agora + timedelta(days=30)
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
        caminho="TESTE",
    )


def _xml_normal_valido():
    documento = _documento()
    ordem = _ordem()

    provider = obter_provider(
        "GEISWEB_TIETE"
    )

    payload = provider.preparar_payload(
        documento=documento,
        ordem_servico=ordem,
        configuracao=_fiscal(),
    )

    resultado = (
        preparar_payload_geisweb_com_xml(
            payload=payload,
            documento=documento,
            ordem_servico=ordem,
            configuracao_institucional=(
                _institucional()
            ),
            configuracao_fiscal=(
                _fiscal()
            ),
            numero_lote="7",
            data_emissao=datetime(
                2026,
                9,
                19,
                12,
                0,
                0,
            ),
            tipo_lancamento="1",
            regime_geisweb="1",
            codigo_nacional="140601",
            base_calculo="100.00",
            ibs_cbs={
                "c_class_trib": "TESTE",
                "ibs": "0.00",
                "cbs": "0.00",
                "c_class_trib_reg": "TESTE",
            },
            outros_impostos={
                "pis": "0.00",
                "cofins": "0.00",
                "csll": "0.00",
                "irrf": "0.00",
                "inss": "0.00",
            },
            tomador=_tomador(),
            servico=_servico(),
            valores=_valores(),
        )
    )

    return resultado["conteudo"]


def test_fluxo_completo_assinado_valida_no_xsd_real():
    xml_normal = _xml_normal_valido()

    xml_assinado = assinar_xml_geisweb(
        xml_normal,
        _material_certificado(),
    )

    criptografia = (
        validar_assinatura_xml_geisweb(
            xml_assinado
        )
    )

    assert criptografia.valido is True

    xsd = validar_xml_envio_sign_lote_rps(
        xml_assinado
    )

    assert xsd.valido, xsd.erros


def test_signature_e_ultimo_elemento_da_raiz():
    xml_assinado = assinar_xml_geisweb(
        _xml_normal_valido(),
        _material_certificado(),
    )

    raiz = etree.fromstring(
        xml_assinado
    )

    assert (
        etree.QName(raiz).localname
        == "EnviaSignLoteRps"
    )

    assert (
        etree.QName(raiz).namespace
        == NS_SIGN
    )

    ultimo = list(raiz)[-1]

    assert (
        etree.QName(ultimo).localname
        == "Signature"
    )

    assert (
        etree.QName(ultimo).namespace
        == NS_DSIG
    )
