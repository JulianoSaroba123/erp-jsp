from types import SimpleNamespace

import pytest

from app.fiscal import nfse_service as service


def _documento(**alteracoes):
    dados = {
        "id": 10,
        "configuracao_fiscal_id": 1,
        "pode_ser_editada": True,
        "serie_rps": None,
        "numero_rps": None,
    }
    dados.update(alteracoes)
    return SimpleNamespace(**dados)


def _configuracao(**alteracoes):
    dados = {
        "id": 1,
        "serie_rps": "1",
        "proximo_rps": 321,
    }
    dados.update(alteracoes)
    return SimpleNamespace(**dados)


def _instalar_bloqueios(
    monkeypatch,
    documento,
    configuracao,
    flushes,
):
    monkeypatch.setattr(
        service,
        "_bloquear_documento_nfse_para_rps",
        lambda documento_id: documento,
    )

    monkeypatch.setattr(
        service,
        "_bloquear_configuracao_fiscal_para_rps",
        lambda configuracao_fiscal_id: configuracao,
    )

    monkeypatch.setattr(
        service,
        "_flush_reserva_rps",
        lambda: flushes.append("flush"),
    )


def test_b7a4_001_reserva_rps_e_incrementa_sequencia(
    monkeypatch,
):
    documento = _documento()
    configuracao = _configuracao()
    flushes = []

    _instalar_bloqueios(
        monkeypatch,
        documento,
        configuracao,
        flushes,
    )

    resultado, criado = service.reservar_rps_nfse(
        documento=documento,
        configuracao=configuracao,
    )

    assert resultado is documento
    assert criado is True

    assert documento.serie_rps == "1"
    assert documento.numero_rps == 321
    assert configuracao.proximo_rps == 322

    assert flushes == ["flush"]


def test_b7a4_002_reserva_existente_e_idempotente(
    monkeypatch,
):
    documento = _documento(
        serie_rps="1",
        numero_rps=77,
    )
    configuracao = _configuracao(
        proximo_rps=321,
    )
    flushes = []

    _instalar_bloqueios(
        monkeypatch,
        documento,
        configuracao,
        flushes,
    )

    resultado, criado = service.reservar_rps_nfse(
        documento=documento,
        configuracao=configuracao,
    )

    assert resultado is documento
    assert criado is False

    assert documento.serie_rps == "1"
    assert documento.numero_rps == 77
    assert configuracao.proximo_rps == 321

    assert flushes == []


@pytest.mark.parametrize(
    "serie_rps,numero_rps",
    [
        ("1", None),
        (None, 50),
    ],
)
def test_b7a4_003_bloqueia_reserva_parcial(
    monkeypatch,
    serie_rps,
    numero_rps,
):
    documento = _documento(
        serie_rps=serie_rps,
        numero_rps=numero_rps,
    )
    configuracao = _configuracao()
    flushes = []

    _instalar_bloqueios(
        monkeypatch,
        documento,
        configuracao,
        flushes,
    )

    with pytest.raises(
        service.PreparacaoNfseInvalida,
        match="parcial ou inconsistente",
    ):
        service.reservar_rps_nfse(
            documento=documento,
            configuracao=configuracao,
        )

    assert configuracao.proximo_rps == 321
    assert flushes == []


def test_b7a4_004_bloqueia_configuracao_divergente(
    monkeypatch,
):
    documento = _documento(
        configuracao_fiscal_id=2,
    )
    configuracao = _configuracao(
        id=1,
    )
    flushes = []

    _instalar_bloqueios(
        monkeypatch,
        documento,
        configuracao,
        flushes,
    )

    with pytest.raises(
        service.PreparacaoNfseInvalida,
        match="nao pertence",
    ):
        service.reservar_rps_nfse(
            documento=documento,
            configuracao=configuracao,
        )

    assert configuracao.proximo_rps == 321
    assert flushes == []


def test_b7a4_005_bloqueia_documento_nao_editavel(
    monkeypatch,
):
    documento = _documento(
        pode_ser_editada=False,
    )
    configuracao = _configuracao()
    flushes = []

    _instalar_bloqueios(
        monkeypatch,
        documento,
        configuracao,
        flushes,
    )

    with pytest.raises(
        service.PreparacaoNfseInvalida,
        match="nao permite reserva",
    ):
        service.reservar_rps_nfse(
            documento=documento,
            configuracao=configuracao,
        )

    assert configuracao.proximo_rps == 321
    assert flushes == []


def test_b7a4_006_rejeita_proximo_rps_invalido(
    monkeypatch,
):
    documento = _documento()
    configuracao = _configuracao(
        proximo_rps=0,
    )
    flushes = []

    _instalar_bloqueios(
        monkeypatch,
        documento,
        configuracao,
        flushes,
    )

    with pytest.raises(
        service.PreparacaoNfseInvalida,
        match="Proximo RPS",
    ):
        service.reservar_rps_nfse(
            documento=documento,
            configuracao=configuracao,
        )

    assert documento.numero_rps is None
    assert flushes == []
