import inspect
from types import SimpleNamespace

import pytest

from app.fiscal import nfse_service as service


def _documento(*, status="PENDENTE_ENVIO"):
    return SimpleNamespace(
        id=123,
        status=status,
        mensagem_status="Documento pronto para fronteira externa.",
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
    return SimpleNamespace(
        id=789,
    )


def test_h3_s5q_integracao_desativada_bloqueia_antes_da_reconstrucao(
    monkeypatch,
):
    documento = _documento()
    configuracao = _configuracao(
        integracao_ativa=False,
    )
    ordem_servico = _ordem_servico()

    def nao_deveria_reconstruir(*args, **kwargs):
        raise AssertionError(
            "Reconstrucao nao pode ocorrer com integracao desativada."
        )

    monkeypatch.setattr(
        service,
        "reconstruir_payload_geisweb_para_envio",
        nao_deveria_reconstruir,
    )

    with pytest.raises(
        service.TransmissaoNfseInvalida,
        match="Integracao externa NFS-e esta desativada",
    ):
        service.validar_elegibilidade_transmissao_geisweb(
            documento=documento,
            ordem_servico=ordem_servico,
            configuracao=configuracao,
        )

    assert documento.status == "PENDENTE_ENVIO"
    assert configuracao.integracao_ativa is False


def test_h3_s5q_status_invalido_bloqueia_antes_da_reconstrucao(
    monkeypatch,
):
    documento = _documento(
        status="PREPARADA",
    )
    configuracao = _configuracao(
        integracao_ativa=True,
    )
    ordem_servico = _ordem_servico()

    def nao_deveria_reconstruir(*args, **kwargs):
        raise AssertionError(
            "Reconstrucao nao pode ocorrer fora de PENDENTE_ENVIO."
        )

    monkeypatch.setattr(
        service,
        "reconstruir_payload_geisweb_para_envio",
        nao_deveria_reconstruir,
    )

    with pytest.raises(
        service.TransicaoStatusNfseInvalida,
        match="nao esta elegivel para transmissao",
    ):
        service.validar_elegibilidade_transmissao_geisweb(
            documento=documento,
            ordem_servico=ordem_servico,
            configuracao=configuracao,
        )

    assert documento.status == "PREPARADA"


def test_h3_s5q_integracao_ativa_reconstroi_e_retorna_payload_sem_mutar_status(
    monkeypatch,
):
    documento = _documento()
    configuracao = _configuracao(
        integracao_ativa=True,
    )
    ordem_servico = _ordem_servico()

    payload_esperado = {
        "provider": "GEISWEB_TIETE",
        "ambiente": "HOMOLOGACAO",
        "conteudo": b"<xml-persistido/>",
    }

    chamadas = []

    def reconstruir(
        *,
        documento,
        ordem_servico,
        configuracao,
    ):
        chamadas.append(
            (
                documento,
                ordem_servico,
                configuracao,
            )
        )

        return payload_esperado

    monkeypatch.setattr(
        service,
        "reconstruir_payload_geisweb_para_envio",
        reconstruir,
    )

    status_antes = documento.status
    mensagem_antes = documento.mensagem_status

    retorno = service.validar_elegibilidade_transmissao_geisweb(
        documento=documento,
        ordem_servico=ordem_servico,
        configuracao=configuracao,
    )

    assert retorno is payload_esperado

    assert chamadas == [
        (
            documento,
            ordem_servico,
            configuracao,
        )
    ]

    assert documento.status == status_antes
    assert documento.mensagem_status == mensagem_antes
    assert configuracao.integracao_ativa is True


def test_h3_s5q_falha_na_reconstrucao_preserva_documento(
    monkeypatch,
):
    documento = _documento()
    configuracao = _configuracao(
        integracao_ativa=True,
    )
    ordem_servico = _ordem_servico()

    status_antes = documento.status
    mensagem_antes = documento.mensagem_status

    def reconstruir_com_falha(*args, **kwargs):
        raise service.TransmissaoNfseInvalida(
            "Integridade do XML fiscal persistido nao confere."
        )

    monkeypatch.setattr(
        service,
        "reconstruir_payload_geisweb_para_envio",
        reconstruir_com_falha,
    )

    with pytest.raises(
        service.TransmissaoNfseInvalida,
        match="Integridade do XML fiscal persistido nao confere",
    ):
        service.validar_elegibilidade_transmissao_geisweb(
            documento=documento,
            ordem_servico=ordem_servico,
            configuracao=configuracao,
        )

    assert documento.status == status_antes
    assert documento.mensagem_status == mensagem_antes


def test_h3_s5q_gate_nao_transmite_nem_persiste():
    fonte = inspect.getsource(
        service.validar_elegibilidade_transmissao_geisweb
    )

    assert "reconstruir_payload_geisweb_para_envio(" in fonte

    proibidos = (
        ".transmitir(",
        "transmitir_payload_nfse(",
        "transmitir_e_aplicar_nfse(",
        "db.session",
        ".commit(",
        ".flush(",
        ".rollback(",
        "requests.",
        "httpx.",
    )

    for termo in proibidos:
        assert termo not in fonte
