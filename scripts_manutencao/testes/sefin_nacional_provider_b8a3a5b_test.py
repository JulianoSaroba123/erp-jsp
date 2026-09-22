import base64
import gzip
import json
from types import SimpleNamespace

import pytest

from app.fiscal.providers import sefin_nacional as modulo
from app.fiscal.providers.base import (
    ErroAutenticacaoNfse,
    ErroTransmissaoNfse,
    IntegracaoFiscalDesativada,
)
from app.fiscal.providers.sefin_nacional import (
    SefinNacionalProvider,
)


def _configuracao(
    *,
    ativa=True,
    ambiente="HOMOLOGACAO",
):
    return SimpleNamespace(
        provider="SEFIN_NACIONAL",
        ambiente=ambiente,
        integracao_ativa=ativa,
    )


def _payload(
    *,
    ambiente="HOMOLOGACAO",
):
    return {
        "provider": "SEFIN_NACIONAL",
        "ambiente": ambiente,
        "conteudo": b"<DPS-assinada/>",
    }


def _xml_nfse(
    numero="12345",
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
    numero="12345",
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
                "2026-09-19T03:00:00-03:00"
            ),
            "idDps": "DPS123",
            "chaveAcesso": "CHAVE123",
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
                "2026-09-19T03:00:00-03:00"
            ),
            "idDPS": "DPS123",
            "erros": [
                {
                    "codigo": "E001",
                    "mensagem": "Regra fiscal rejeitada",
                    "descricao": "Descricao teste",
                    "complemento": "Complemento teste",
                }
            ],
        },
        separators=(",", ":"),
    ).encode(
        "utf-8"
    )


def test_b8a3a5b_001_disjuntor_bloqueia_antes_do_certificado(
    monkeypatch,
):
    provider = SefinNacionalProvider()

    def carregar_proibido():
        raise AssertionError(
            "Certificado nao deveria ser carregado."
        )

    def http_proibido(**kwargs):
        raise AssertionError(
            "HTTP nao deveria ser chamado."
        )

    monkeypatch.setattr(
        modulo,
        "carregar_certificado_a1_do_ambiente",
        carregar_proibido,
    )

    monkeypatch.setattr(
        modulo,
        "executar_emissao_nfse_http",
        http_proibido,
    )

    with pytest.raises(
        IntegracaoFiscalDesativada,
    ):
        provider.transmitir(
            payload=_payload(),
            configuracao=_configuracao(
                ativa=False
            ),
        )


def test_b8a3a5b_002_sucesso_201_vira_aceita(
    monkeypatch,
):
    provider = SefinNacionalProvider()
    material = object()

    monkeypatch.setattr(
        modulo,
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
        modulo,
        "executar_emissao_nfse_http",
        emitir,
    )

    resultado = provider.transmitir(
        payload=_payload(),
        configuracao=_configuracao(),
    )

    assert resultado["status"] == "ACEITA"
    assert resultado["numero_nfse"] == "98765"
    assert resultado["protocolo"] is None

    dados = resultado[
        "dados_provider"
    ]

    assert dados["id_dps"] == "DPS123"
    assert dados["chave_acesso"] == "CHAVE123"
    assert "<nNFSe>98765</nNFSe>" in dados["nfse_xml"]

    assert len(chamadas) == 1
    assert chamadas[0]["ambiente"] == "HOMOLOGACAO"
    assert chamadas[0]["material_certificado"] is material


def test_b8a3a5b_003_http_400_vira_rejeitada(
    monkeypatch,
):
    provider = SefinNacionalProvider()

    monkeypatch.setattr(
        modulo,
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
        modulo,
        "executar_emissao_nfse_http",
        emitir,
    )

    resultado = provider.transmitir(
        payload=_payload(),
        configuracao=_configuracao(),
    )

    assert resultado["status"] == "REJEITADA"
    assert resultado["numero_nfse"] is None
    assert resultado["protocolo"] is None

    assert "E001" in resultado["mensagem"]
    assert "Regra fiscal rejeitada" in resultado["mensagem"]

    erros = resultado[
        "dados_provider"
    ][
        "erros"
    ]

    assert erros[0]["codigo"] == "E001"


def test_b8a3a5b_004_403_continua_erro_tecnico(
    monkeypatch,
):
    provider = SefinNacionalProvider()

    monkeypatch.setattr(
        modulo,
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
        modulo,
        "executar_emissao_nfse_http",
        emitir,
    )

    with pytest.raises(
        ErroAutenticacaoNfse,
    ):
        provider.transmitir(
            payload=_payload(),
            configuracao=_configuracao(),
        )


def test_b8a3a5b_005_bloqueia_ambiente_divergente(
    monkeypatch,
):
    provider = SefinNacionalProvider()

    chamado = {
        "certificado": False,
    }

    def carregar():
        chamado[
            "certificado"
        ] = True

        return object()

    monkeypatch.setattr(
        modulo,
        "carregar_certificado_a1_do_ambiente",
        carregar,
    )

    with pytest.raises(
        ErroTransmissaoNfse,
        match="Ambiente do payload diverge",
    ):
        provider.transmitir(
            payload=_payload(
                ambiente="PRODUCAO"
            ),
            configuracao=_configuracao(
                ambiente="HOMOLOGACAO"
            ),
        )

    assert chamado["certificado"] is False


def test_b8a3a5b_006_bloqueia_provider_divergente(
    monkeypatch,
):
    provider = SefinNacionalProvider()

    payload = _payload()
    payload[
        "provider"
    ] = "OUTRO"

    with pytest.raises(
        ErroTransmissaoNfse,
        match="nao pertence",
    ):
        provider.transmitir(
            payload=payload,
            configuracao=_configuracao(),
        )


def test_b8a3a5b_007_exige_conteudo_assinado_em_bytes():
    provider = SefinNacionalProvider()

    payload = _payload()
    payload[
        "conteudo"
    ] = None

    with pytest.raises(
        ErroTransmissaoNfse,
        match="XML DPS assinado",
    ):
        provider.transmitir(
            payload=payload,
            configuracao=_configuracao(),
        )


def test_b8a3a5b_008_sucesso_sem_nnfse_e_bloqueado(
    monkeypatch,
):
    provider = SefinNacionalProvider()

    monkeypatch.setattr(
        modulo,
        "carregar_certificado_a1_do_ambiente",
        lambda: object(),
    )

    xml = (
        b'<NFSe xmlns="http://www.sped.fazenda.gov.br/nfse">'
        b'<infNFSe Id="NFS123"/>'
        b'</NFSe>'
    )

    corpo = json.dumps(
        {
            "tipoAmbiente": 2,
            "versaoAplicativo": "SEFIN-TESTE",
            "dataHoraProcessamento": (
                "2026-09-19T03:00:00-03:00"
            ),
            "idDps": "DPS123",
            "chaveAcesso": "CHAVE123",
            "nfseXmlGZipB64": base64.b64encode(
                gzip.compress(
                    xml,
                    mtime=0,
                )
            ).decode(
                "ascii"
            ),
        }
    ).encode(
        "utf-8"
    )

    monkeypatch.setattr(
        modulo,
        "executar_emissao_nfse_http",
        lambda **kwargs: SimpleNamespace(
            status_code=201,
            conteudo=corpo,
        ),
    )

    with pytest.raises(
        ErroTransmissaoNfse,
        match="nNFSe",
    ):
        provider.transmitir(
            payload=_payload(),
            configuracao=_configuracao(),
        )
