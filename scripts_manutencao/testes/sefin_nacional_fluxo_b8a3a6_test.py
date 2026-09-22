import base64
import gzip
import json
from types import SimpleNamespace

import pytest

from app.fiscal.nfse_service import (
    TransicaoStatusNfseInvalida,
    transmitir_e_aplicar_nfse,
)
from app.fiscal.providers import sefin_nacional as modulo_sefin
from app.fiscal.providers.base import (
    ErroAutenticacaoNfse,
    ErroTransmissaoNfse,
    IntegracaoFiscalDesativada,
)


def _configuracao(
    *,
    ativa=True,
):
    return SimpleNamespace(
        provider="SEFIN_NACIONAL",
        ambiente="HOMOLOGACAO",
        integracao_ativa=ativa,
    )


def _documento(
    *,
    status="PENDENTE_ENVIO",
):
    return SimpleNamespace(
        status=status,
        mensagem_status=None,
        protocolo=None,
        numero_nfse=None,
        chave_acesso=None,
    )


def _payload():
    return {
        "provider": "SEFIN_NACIONAL",
        "ambiente": "HOMOLOGACAO",
        "conteudo": b"<DPS-assinada/>",
    }


def _xml_nfse(
    numero="98765",
):
    return (
        b'<?xml version="1.0" encoding="UTF-8"?>'
        b'<NFSe xmlns="http://www.sped.fazenda.gov.br/nfse">'
        b'<infNFSe Id="NFS123">'
        b'<nNFSe>'
        + numero.encode("ascii")
        + b'</nNFSe>'
        b'</infNFSe>'
        b'</NFSe>'
    )


def _corpo_201(
    *,
    numero="98765",
):
    xml = _xml_nfse(
        numero
    )

    xml_b64 = base64.b64encode(
        gzip.compress(
            xml,
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
                "2026-09-19T01:00:00-03:00"
            ),
            "idDps": "DPS123",
            "chaveAcesso": "CHAVE-ACESSO-123",
            "nfseXmlGZipB64": xml_b64,
        },
        separators=(",", ":"),
    ).encode(
        "utf-8"
    )


def _corpo_400():
    return json.dumps(
        {
            "tipoAmbiente": 2,
            "versaoAplicativo": "SEFIN-TESTE",
            "dataHoraProcessamento": (
                "2026-09-19T01:00:00-03:00"
            ),
            "idDPS": "DPS123",
            "erros": [
                {
                    "codigo": "E001",
                    "mensagem": "Regra fiscal rejeitada",
                    "descricao": "Descricao teste",
                    "complemento": None,
                }
            ],
        },
        separators=(",", ":"),
    ).encode(
        "utf-8"
    )


def test_b8a3a6_001_fluxo_201_autoriza_documento(
    monkeypatch,
):
    documento = _documento()
    material = object()

    monkeypatch.setattr(
        modulo_sefin,
        "carregar_certificado_a1_do_ambiente",
        lambda: material,
    )

    chamadas = []

    def emitir(**kwargs):
        chamadas.append(
            kwargs
        )

        return SimpleNamespace(
            status_code=201,
            conteudo=_corpo_201(
                numero="98765"
            ),
        )

    monkeypatch.setattr(
        modulo_sefin,
        "executar_emissao_nfse_http",
        emitir,
    )

    documento_retorno, resultado = (
        transmitir_e_aplicar_nfse(
            documento=documento,
            payload=_payload(),
            configuracao=_configuracao(),
        )
    )

    assert documento_retorno is documento

    assert resultado["status"] == "ACEITA"

    assert documento.status == "AUTORIZADA"
    assert documento.numero_nfse == "98765"
    assert documento.chave_acesso == "CHAVE-ACESSO-123"

    assert len(chamadas) == 1

    assert chamadas[0][
        "material_certificado"
    ] is material


def test_b8a3a6_002_fluxo_400_rejeita_documento(
    monkeypatch,
):
    documento = _documento()

    monkeypatch.setattr(
        modulo_sefin,
        "carregar_certificado_a1_do_ambiente",
        lambda: object(),
    )

    def emitir(**kwargs):
        exc = ErroTransmissaoNfse(
            "HTTP 400"
        )

        exc.status_code = 400
        exc.conteudo = _corpo_400()

        raise exc

    monkeypatch.setattr(
        modulo_sefin,
        "executar_emissao_nfse_http",
        emitir,
    )

    documento_retorno, resultado = (
        transmitir_e_aplicar_nfse(
            documento=documento,
            payload=_payload(),
            configuracao=_configuracao(),
        )
    )

    assert documento_retorno is documento
    assert resultado["status"] == "REJEITADA"

    assert documento.status == "REJEITADA"
    assert documento.numero_nfse is None
    assert documento.chave_acesso is None

    assert "E001" in documento.mensagem_status


def test_b8a3a6_003_erro_403_nao_muta_documento(
    monkeypatch,
):
    documento = _documento()

    monkeypatch.setattr(
        modulo_sefin,
        "carregar_certificado_a1_do_ambiente",
        lambda: object(),
    )

    def emitir(**kwargs):
        exc = ErroAutenticacaoNfse(
            "HTTP 403"
        )

        exc.status_code = 403
        exc.conteudo = b'{"erros":[]}'

        raise exc

    monkeypatch.setattr(
        modulo_sefin,
        "executar_emissao_nfse_http",
        emitir,
    )

    with pytest.raises(
        ErroAutenticacaoNfse,
    ):
        transmitir_e_aplicar_nfse(
            documento=documento,
            payload=_payload(),
            configuracao=_configuracao(),
        )

    assert documento.status == "PENDENTE_ENVIO"
    assert documento.numero_nfse is None
    assert documento.chave_acesso is None
    assert documento.mensagem_status is None


def test_b8a3a6_004_disjuntor_impede_certificado_e_http(
    monkeypatch,
):
    documento = _documento()

    def certificado_proibido():
        raise AssertionError(
            "Certificado nao deveria ser carregado."
        )

    def http_proibido(**kwargs):
        raise AssertionError(
            "HTTP nao deveria ser executado."
        )

    monkeypatch.setattr(
        modulo_sefin,
        "carregar_certificado_a1_do_ambiente",
        certificado_proibido,
    )

    monkeypatch.setattr(
        modulo_sefin,
        "executar_emissao_nfse_http",
        http_proibido,
    )

    with pytest.raises(
        IntegracaoFiscalDesativada,
    ):
        transmitir_e_aplicar_nfse(
            documento=documento,
            payload=_payload(),
            configuracao=_configuracao(
                ativa=False
            ),
        )

    assert documento.status == "PENDENTE_ENVIO"
    assert documento.numero_nfse is None
    assert documento.chave_acesso is None


def test_b8a3a6_005_estado_invalido_bloqueia_antes_da_rede(
    monkeypatch,
):
    documento = _documento(
        status="PREPARADA"
    )

    def certificado_proibido():
        raise AssertionError(
            "Certificado nao deveria ser carregado."
        )

    def http_proibido(**kwargs):
        raise AssertionError(
            "HTTP nao deveria ser executado."
        )

    monkeypatch.setattr(
        modulo_sefin,
        "carregar_certificado_a1_do_ambiente",
        certificado_proibido,
    )

    monkeypatch.setattr(
        modulo_sefin,
        "executar_emissao_nfse_http",
        http_proibido,
    )

    with pytest.raises(
        TransicaoStatusNfseInvalida,
        match="nao pode ser transmitido",
    ):
        transmitir_e_aplicar_nfse(
            documento=documento,
            payload=_payload(),
            configuracao=_configuracao(),
        )

    assert documento.status == "PREPARADA"
