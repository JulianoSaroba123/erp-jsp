from types import SimpleNamespace

import pytest

from app.fiscal.nfse_service import (
    TransicaoStatusNfseInvalida,
    aplicar_resultado_transmissao_nfse,
)


def _documento():
    return SimpleNamespace(
        status="PENDENTE_ENVIO",
        mensagem_status=None,
        protocolo=None,
        numero_nfse=None,
        codigo_verificacao=None,
        chave_acesso=None,
    )


def test_h3_s5e_001_geisweb_persiste_chave_e_codigo():
    documento = _documento()

    resultado = {
        "status": "ACEITA",
        "mensagem": "NFS-e autorizada.",
        "protocolo": None,
        "numero_nfse": "12345",
        "dados_provider": {
            "provider": "GEISWEB_TIETE",
            "chave_nacional": "CHAVE-NACIONAL-001",
            "codigo_verificacao": "ABC123",
        },
    }

    aplicar_resultado_transmissao_nfse(
        documento=documento,
        resultado=resultado,
    )

    assert documento.status == "AUTORIZADA"
    assert documento.numero_nfse == "12345"
    assert documento.chave_acesso == "CHAVE-NACIONAL-001"
    assert documento.codigo_verificacao == "ABC123"


def test_h3_s5e_002_chave_acesso_tem_precedencia():
    documento = _documento()

    resultado = {
        "status": "ACEITA",
        "mensagem": "NFS-e autorizada.",
        "protocolo": None,
        "numero_nfse": "12346",
        "dados_provider": {
            "provider": "GEISWEB_TIETE",
            "chave_acesso": "CHAVE-EXPLICITA",
            "chave_nacional": "CHAVE-NACIONAL",
            "codigo_verificacao": "XYZ789",
        },
    }

    aplicar_resultado_transmissao_nfse(
        documento=documento,
        resultado=resultado,
    )

    assert documento.chave_acesso == "CHAVE-EXPLICITA"
    assert documento.codigo_verificacao == "XYZ789"


def test_h3_s5e_003_codigo_invalido_nao_muta_documento():
    documento = _documento()

    resultado = {
        "status": "ACEITA",
        "mensagem": "NFS-e autorizada.",
        "protocolo": None,
        "numero_nfse": "12347",
        "dados_provider": {
            "provider": "GEISWEB_TIETE",
            "chave_nacional": "CHAVE-NACIONAL-002",
            "codigo_verificacao": 123,
        },
    }

    with pytest.raises(
        TransicaoStatusNfseInvalida,
        match="codigo_verificacao",
    ):
        aplicar_resultado_transmissao_nfse(
            documento=documento,
            resultado=resultado,
        )

    assert documento.status == "PENDENTE_ENVIO"
    assert documento.numero_nfse is None
    assert documento.chave_acesso is None
    assert documento.codigo_verificacao is None
