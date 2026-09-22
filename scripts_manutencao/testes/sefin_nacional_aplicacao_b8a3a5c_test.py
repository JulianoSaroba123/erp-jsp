from types import SimpleNamespace

import pytest

from app.fiscal.nfse_service import (
    TransicaoStatusNfseInvalida,
    aplicar_resultado_transmissao_nfse,
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


def _resultado_aceito(
    *,
    chave_acesso="CHAVE123",
):
    return {
        "status": "ACEITA",
        "mensagem": "NFS-e autorizada.",
        "protocolo": None,
        "numero_nfse": "98765",
        "dados_provider": {
            "provider": "SEFIN_NACIONAL",
            "chave_acesso": chave_acesso,
        },
    }


def test_b8a3a5c_001_aceita_persiste_chave_acesso():
    documento = _documento()

    aplicar_resultado_transmissao_nfse(
        documento=documento,
        resultado=_resultado_aceito(),
    )

    assert documento.status == "AUTORIZADA"
    assert documento.numero_nfse == "98765"
    assert documento.chave_acesso == "CHAVE123"
    assert documento.protocolo is None


def test_b8a3a5c_002_normaliza_espacos_da_chave():
    documento = _documento()

    aplicar_resultado_transmissao_nfse(
        documento=documento,
        resultado=_resultado_aceito(
            chave_acesso="  CHAVE456  "
        ),
    )

    assert documento.chave_acesso == "CHAVE456"


def test_b8a3a5c_003_aceita_sem_chave_continua_valida():
    documento = _documento()

    aplicar_resultado_transmissao_nfse(
        documento=documento,
        resultado=_resultado_aceito(
            chave_acesso=None
        ),
    )

    assert documento.status == "AUTORIZADA"
    assert documento.numero_nfse == "98765"
    assert documento.chave_acesso is None


def test_b8a3a5c_004_rejeitada_nao_grava_chave():
    documento = _documento()

    resultado = {
        "status": "REJEITADA",
        "mensagem": "Regra fiscal rejeitada.",
        "protocolo": None,
        "numero_nfse": None,
        "dados_provider": {
            "provider": "SEFIN_NACIONAL",
            "chave_acesso": "NAO-DEVE-GRAVAR",
        },
    }

    aplicar_resultado_transmissao_nfse(
        documento=documento,
        resultado=resultado,
    )

    assert documento.status == "REJEITADA"
    assert documento.numero_nfse is None
    assert documento.chave_acesso is None


def test_b8a3a5c_005_chave_invalida_bloqueia_antes_da_mutacao():
    documento = _documento()

    resultado = _resultado_aceito(
        chave_acesso=12345
    )

    with pytest.raises(
        TransicaoStatusNfseInvalida,
        match="chave_acesso",
    ):
        aplicar_resultado_transmissao_nfse(
            documento=documento,
            resultado=resultado,
        )

    assert documento.status == "PENDENTE_ENVIO"
    assert documento.numero_nfse is None
    assert documento.chave_acesso is None


def test_b8a3a5c_006_chave_maior_que_coluna_e_bloqueada():
    documento = _documento()

    resultado = _resultado_aceito(
        chave_acesso="X" * 101
    )

    with pytest.raises(
        TransicaoStatusNfseInvalida,
        match="100 caracteres",
    ):
        aplicar_resultado_transmissao_nfse(
            documento=documento,
            resultado=resultado,
        )

    assert documento.status == "PENDENTE_ENVIO"
    assert documento.numero_nfse is None
    assert documento.chave_acesso is None


def test_b8a3a5c_007_erro_tecnico_nao_muta_documento():
    documento = _documento()

    resultado = {
        "status": "ERRO",
        "mensagem": "Falha tecnica.",
        "protocolo": None,
        "numero_nfse": None,
        "dados_provider": {
            "chave_acesso": "NAO-GRAVAR",
        },
    }

    aplicar_resultado_transmissao_nfse(
        documento=documento,
        resultado=resultado,
    )

    assert documento.status == "PENDENTE_ENVIO"
    assert documento.numero_nfse is None
    assert documento.chave_acesso is None


def test_b8a3a5c_008_preserva_protocolo_real():
    documento = _documento()

    resultado = _resultado_aceito()
    resultado["protocolo"] = "PROTOCOLO-123"

    aplicar_resultado_transmissao_nfse(
        documento=documento,
        resultado=resultado,
    )

    assert documento.status == "AUTORIZADA"
    assert documento.protocolo == "PROTOCOLO-123"
    assert documento.chave_acesso == "CHAVE123"
