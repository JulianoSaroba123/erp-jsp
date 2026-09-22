import inspect
from types import SimpleNamespace

import pytest

from app.fiscal import nfse_service as service


def _documento():
    return SimpleNamespace(
        id=123,
        status="PENDENTE_ENVIO",
        mensagem_status="Pronta para envio.",
        provider="GEISWEB_TIETE",
        ambiente="HOMOLOGACAO",
    )


def _configuracao(*, integracao_ativa=False):
    return SimpleNamespace(
        id=456,
        provider="GEISWEB_TIETE",
        ambiente="HOMOLOGACAO",
        integracao_ativa=integracao_ativa,
    )


def _ordem_servico():
    return SimpleNamespace(id=789)


def test_h3_s5r_sem_autorizacao_bloqueia_antes_do_gate(
    monkeypatch,
):
    documento = _documento()
    configuracao = _configuracao(
        integracao_ativa=True,
    )
    ordem_servico = _ordem_servico()

    def nao_deveria_validar(*args, **kwargs):
        raise AssertionError(
            "Gate H3-S5Q nao pode ser chamado sem autorizacao explicita."
        )

    def nao_deveria_transmitir(*args, **kwargs):
        raise AssertionError(
            "Transmissao nao pode ser chamada sem autorizacao explicita."
        )

    monkeypatch.setattr(
        service,
        "validar_elegibilidade_transmissao_geisweb",
        nao_deveria_validar,
    )

    monkeypatch.setattr(
        service,
        "transmitir_e_aplicar_nfse",
        nao_deveria_transmitir,
    )

    with pytest.raises(
        service.TransmissaoNfseInvalida,
        match="nao autorizada",
    ):
        service.transmitir_documento_nfse_geisweb_controlado(
            documento=documento,
            ordem_servico=ordem_servico,
            configuracao=configuracao,
        )

    assert documento.status == "PENDENTE_ENVIO"


def test_h3_s5r_autorizacao_exige_true_booleano(
    monkeypatch,
):
    documento = _documento()
    configuracao = _configuracao(
        integracao_ativa=True,
    )
    ordem_servico = _ordem_servico()

    def nao_deveria_validar(*args, **kwargs):
        raise AssertionError(
            "Valor truthy diferente de True nao pode liberar transmissao."
        )

    monkeypatch.setattr(
        service,
        "validar_elegibilidade_transmissao_geisweb",
        nao_deveria_validar,
    )

    with pytest.raises(
        service.TransmissaoNfseInvalida,
        match="nao autorizada",
    ):
        service.transmitir_documento_nfse_geisweb_controlado(
            documento=documento,
            ordem_servico=ordem_servico,
            configuracao=configuracao,
            autorizar_transmissao=1,
        )

    assert documento.status == "PENDENTE_ENVIO"


def test_h3_s5r_gate_s5q_bloqueia_antes_da_transmissao(
    monkeypatch,
):
    documento = _documento()
    configuracao = _configuracao(
        integracao_ativa=False,
    )
    ordem_servico = _ordem_servico()

    chamadas_gate = []

    def gate_bloqueado(
        *,
        documento,
        ordem_servico,
        configuracao,
    ):
        chamadas_gate.append(
            (
                documento,
                ordem_servico,
                configuracao,
            )
        )

        raise service.TransmissaoNfseInvalida(
            "Integracao externa NFS-e esta desativada."
        )

    def nao_deveria_transmitir(*args, **kwargs):
        raise AssertionError(
            "Transmissao nao pode ocorrer se H3-S5Q bloquear."
        )

    monkeypatch.setattr(
        service,
        "validar_elegibilidade_transmissao_geisweb",
        gate_bloqueado,
    )

    monkeypatch.setattr(
        service,
        "transmitir_e_aplicar_nfse",
        nao_deveria_transmitir,
    )

    with pytest.raises(
        service.TransmissaoNfseInvalida,
        match="Integracao externa NFS-e esta desativada",
    ):
        service.transmitir_documento_nfse_geisweb_controlado(
            documento=documento,
            ordem_servico=ordem_servico,
            configuracao=configuracao,
            autorizar_transmissao=True,
        )

    assert chamadas_gate == [
        (
            documento,
            ordem_servico,
            configuracao,
        )
    ]

    assert documento.status == "PENDENTE_ENVIO"


def test_h3_s5r_caminho_liberado_encaminha_payload_exato(
    monkeypatch,
):
    documento = _documento()
    configuracao = _configuracao(
        integracao_ativa=True,
    )
    ordem_servico = _ordem_servico()

    payload = {
        "provider": "GEISWEB_TIETE",
        "ambiente": "HOMOLOGACAO",
        "conteudo": b"<xml-persistido/>",
    }

    resultado = {
        "status": "PROCESSANDO",
        "mensagem": "Resultado fake.",
        "protocolo": "PROTO-TESTE",
        "numero_nfse": None,
        "dados_provider": {},
    }

    chamadas_transmissao = []

    monkeypatch.setattr(
        service,
        "validar_elegibilidade_transmissao_geisweb",
        lambda **kwargs: payload,
    )

    def transmitir_fake(
        *,
        documento,
        payload,
        configuracao,
    ):
        chamadas_transmissao.append(
            (
                documento,
                payload,
                configuracao,
            )
        )

        return documento, resultado

    monkeypatch.setattr(
        service,
        "transmitir_e_aplicar_nfse",
        transmitir_fake,
    )

    retorno_documento, retorno_resultado = (
        service.transmitir_documento_nfse_geisweb_controlado(
            documento=documento,
            ordem_servico=ordem_servico,
            configuracao=configuracao,
            autorizar_transmissao=True,
        )
    )

    assert retorno_documento is documento
    assert retorno_resultado is resultado

    assert chamadas_transmissao == [
        (
            documento,
            payload,
            configuracao,
        )
    ]


def test_h3_s5r_orquestrador_nao_persiste_nem_prepara_novo_artefato():
    fonte = inspect.getsource(
        service.transmitir_documento_nfse_geisweb_controlado
    )

    assert "validar_elegibilidade_transmissao_geisweb(" in fonte
    assert "transmitir_e_aplicar_nfse(" in fonte

    proibidos = (
        "db.session",
        ".commit(",
        ".flush(",
        ".rollback(",
        "reservar_rps_nfse(",
        "preparar_documento_nfse_com_geisweb(",
        "preparar_payload_nfse_com_geisweb(",
        "xml_envio =",
        "requests.",
        "httpx.",
    )

    for termo in proibidos:
        assert termo not in fonte
