from types import SimpleNamespace

import pytest

from app.fiscal import nfse_service as service


def _documento(status="PENDENTE_ENVIO"):
    return SimpleNamespace(
        status=status,
        numero_rps=1,
        mensagem_status=None,
        protocolo=None,
        numero_nfse=None,
        codigo_verificacao=None,
        chave_acesso=None,
    )


def _configuracao():
    return SimpleNamespace(
        provider="GEISWEB_TIETE",
        ambiente="HOMOLOGACAO",
        integracao_ativa=False,
        proximo_rps=2,
    )


def _bloquear_commit(monkeypatch):
    def commit_proibido():
        raise AssertionError(
            "transmitir_e_aplicar_nfse nao pode executar commit."
        )

    fake_db = SimpleNamespace(
        session=SimpleNamespace(
            commit=commit_proibido,
        ),
    )

    monkeypatch.setattr(
        service,
        "db",
        fake_db,
    )


def test_h3_s5e_c_001_orquestra_uma_vez_sem_commit_ou_consumir_rps(
    monkeypatch,
):
    documento = _documento()
    configuracao = _configuracao()

    payload = {
        "provider": "GEISWEB_TIETE",
        "conteudo": b"<xml/>",
    }

    resultado = {
        "status": "ACEITA",
        "mensagem": "NFS-e autorizada.",
        "protocolo": None,
        "numero_nfse": "100",
        "dados_provider": {
            "provider": "GEISWEB_TIETE",
        },
    }

    chamadas = []

    def transmitir(*, payload, configuracao):
        chamadas.append("transmitir")

        assert payload is not None
        assert payload["provider"] == "GEISWEB_TIETE"
        assert configuracao is not None
        assert configuracao.provider == "GEISWEB_TIETE"

        return resultado

    def aplicar(*, documento, resultado):
        chamadas.append("aplicar")

        assert resultado["status"] == "ACEITA"

        documento.status = "AUTORIZADA"
        documento.numero_nfse = "100"

        return documento

    monkeypatch.setattr(
        service,
        "transmitir_payload_nfse",
        transmitir,
    )

    monkeypatch.setattr(
        service,
        "aplicar_resultado_transmissao_nfse",
        aplicar,
    )

    _bloquear_commit(monkeypatch)

    numero_rps_antes = documento.numero_rps
    proximo_rps_antes = configuracao.proximo_rps

    documento_retorno, resultado_retorno = (
        service.transmitir_e_aplicar_nfse(
            documento=documento,
            payload=payload,
            configuracao=configuracao,
        )
    )

    assert documento_retorno is documento
    assert resultado_retorno is resultado

    assert chamadas == [
        "transmitir",
        "aplicar",
    ]

    assert documento.status == "AUTORIZADA"

    assert documento.numero_rps == numero_rps_antes
    assert configuracao.proximo_rps == proximo_rps_antes


def test_h3_s5e_c_002_erro_transmissao_nao_aplica_nem_muta_estado(
    monkeypatch,
):
    documento = _documento()
    configuracao = _configuracao()

    payload = {
        "provider": "GEISWEB_TIETE",
        "conteudo": b"<xml/>",
    }

    estado_antes = (
        documento.status,
        documento.numero_rps,
        documento.mensagem_status,
        documento.protocolo,
        documento.numero_nfse,
        documento.codigo_verificacao,
        documento.chave_acesso,
        configuracao.proximo_rps,
    )

    def transmitir(*, payload, configuracao):
        raise RuntimeError(
            "falha tecnica simulada GeisWeb"
        )

    def aplicar(*args, **kwargs):
        raise AssertionError(
            "Resultado nao pode ser aplicado apos falha de transmissao."
        )

    monkeypatch.setattr(
        service,
        "transmitir_payload_nfse",
        transmitir,
    )

    monkeypatch.setattr(
        service,
        "aplicar_resultado_transmissao_nfse",
        aplicar,
    )

    _bloquear_commit(monkeypatch)

    with pytest.raises(
        RuntimeError,
        match="falha tecnica simulada GeisWeb",
    ):
        service.transmitir_e_aplicar_nfse(
            documento=documento,
            payload=payload,
            configuracao=configuracao,
        )

    estado_depois = (
        documento.status,
        documento.numero_rps,
        documento.mensagem_status,
        documento.protocolo,
        documento.numero_nfse,
        documento.codigo_verificacao,
        documento.chave_acesso,
        configuracao.proximo_rps,
    )

    assert estado_depois == estado_antes


def test_h3_s5e_c_003_estado_invalido_bloqueia_antes_da_transmissao(
    monkeypatch,
):
    documento = _documento(
        status="PREPARADA",
    )

    configuracao = _configuracao()

    payload = {
        "provider": "GEISWEB_TIETE",
        "conteudo": b"<xml/>",
    }

    def transmitir(*args, **kwargs):
        raise AssertionError(
            "Estado invalido nao pode atingir transmissao."
        )

    def aplicar(*args, **kwargs):
        raise AssertionError(
            "Estado invalido nao pode atingir aplicacao."
        )

    monkeypatch.setattr(
        service,
        "transmitir_payload_nfse",
        transmitir,
    )

    monkeypatch.setattr(
        service,
        "aplicar_resultado_transmissao_nfse",
        aplicar,
    )

    _bloquear_commit(monkeypatch)

    numero_rps_antes = documento.numero_rps
    proximo_rps_antes = configuracao.proximo_rps

    with pytest.raises(
        service.TransicaoStatusNfseInvalida,
        match="nao pode ser transmitido",
    ):
        service.transmitir_e_aplicar_nfse(
            documento=documento,
            payload=payload,
            configuracao=configuracao,
        )

    assert documento.status == "PREPARADA"
    assert documento.numero_rps == numero_rps_antes
    assert configuracao.proximo_rps == proximo_rps_antes
