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


def test_h3_s5e_004_rejeitada_nao_persiste_campos_autorizacao():
    documento = _documento()

    resultado = {
        "status": "REJEITADA",
        "mensagem": "RPS rejeitado pelo GeisWeb.",
        "protocolo": None,
        "numero_nfse": None,
        "dados_provider": {
            "provider": "GEISWEB_TIETE",
            "numero_lote": "1",
            "chave_acesso": "NAO-DEVE-PERSISTIR",
            "chave_nacional": "NAO-DEVE-PERSISTIR-2",
            "codigo_verificacao": "NAO-DEVE-PERSISTIR-3",
        },
    }

    aplicar_resultado_transmissao_nfse(
        documento=documento,
        resultado=resultado,
    )

    assert documento.status == "REJEITADA"
    assert documento.mensagem_status == "RPS rejeitado pelo GeisWeb."
    assert documento.numero_nfse is None
    assert documento.chave_acesso is None
    assert documento.codigo_verificacao is None


def test_h3_s5e_005_processando_persiste_protocolo_sem_autorizacao():
    documento = _documento()

    resultado = {
        "status": "PROCESSANDO",
        "mensagem": "Lote recebido e em processamento.",
        "protocolo": "PROTOCOLO-H3-001",
        "numero_nfse": None,
        "dados_provider": {
            "provider": "GEISWEB_TIETE",
            "chave_acesso": "NAO-DEVE-PERSISTIR",
            "chave_nacional": "NAO-DEVE-PERSISTIR-2",
            "codigo_verificacao": "NAO-DEVE-PERSISTIR-3",
        },
    }

    aplicar_resultado_transmissao_nfse(
        documento=documento,
        resultado=resultado,
    )

    assert documento.status == "PROCESSANDO"
    assert documento.mensagem_status == (
        "Lote recebido e em processamento."
    )
    assert documento.protocolo == "PROTOCOLO-H3-001"
    assert documento.numero_nfse is None
    assert documento.chave_acesso is None
    assert documento.codigo_verificacao is None


def test_h3_s5e_006_erro_tecnico_preserva_estado_integralmente():
    documento = _documento()

    documento.mensagem_status = "Estado anterior."
    documento.protocolo = "PROTOCOLO-ANTERIOR"
    documento.numero_nfse = None
    documento.codigo_verificacao = None
    documento.chave_acesso = None

    antes = (
        documento.status,
        documento.mensagem_status,
        documento.protocolo,
        documento.numero_nfse,
        documento.codigo_verificacao,
        documento.chave_acesso,
    )

    resultado = {
        "status": "ERRO",
        "mensagem": "Falha tecnica do provider.",
        "protocolo": "NAO-DEVE-PERSISTIR",
        "numero_nfse": None,
        "dados_provider": {
            "provider": "GEISWEB_TIETE",
        },
    }

    aplicar_resultado_transmissao_nfse(
        documento=documento,
        resultado=resultado,
    )

    depois = (
        documento.status,
        documento.mensagem_status,
        documento.protocolo,
        documento.numero_nfse,
        documento.codigo_verificacao,
        documento.chave_acesso,
    )

    assert depois == antes


def test_h3_s5e_007_rejeitada_invalida_nao_muta_documento():
    from app.fiscal.nfse_service import TransmissaoNfseInvalida

    documento = _documento()

    antes = (
        documento.status,
        documento.mensagem_status,
        documento.protocolo,
        documento.numero_nfse,
        documento.codigo_verificacao,
        documento.chave_acesso,
    )

    resultado = {
        "status": "REJEITADA",
        "mensagem": 123,
        "protocolo": None,
        "numero_nfse": None,
        "dados_provider": {
            "provider": "GEISWEB_TIETE",
        },
    }

    with pytest.raises(
        TransmissaoNfseInvalida,
        match="mensagem",
    ):
        aplicar_resultado_transmissao_nfse(
            documento=documento,
            resultado=resultado,
        )

    depois = (
        documento.status,
        documento.mensagem_status,
        documento.protocolo,
        documento.numero_nfse,
        documento.codigo_verificacao,
        documento.chave_acesso,
    )

    assert depois == antes


def test_h3_s5e_008_processando_invalido_nao_muta_documento():
    from app.fiscal.nfse_service import TransmissaoNfseInvalida

    documento = _documento()

    antes = (
        documento.status,
        documento.mensagem_status,
        documento.protocolo,
        documento.numero_nfse,
        documento.codigo_verificacao,
        documento.chave_acesso,
    )

    resultado = {
        "status": "PROCESSANDO",
        "mensagem": "Em processamento.",
        "protocolo": 123,
        "numero_nfse": None,
        "dados_provider": {
            "provider": "GEISWEB_TIETE",
        },
    }

    with pytest.raises(
        TransmissaoNfseInvalida,
        match="protocolo",
    ):
        aplicar_resultado_transmissao_nfse(
            documento=documento,
            resultado=resultado,
        )

    depois = (
        documento.status,
        documento.mensagem_status,
        documento.protocolo,
        documento.numero_nfse,
        documento.codigo_verificacao,
        documento.chave_acesso,
    )

    assert depois == antes
