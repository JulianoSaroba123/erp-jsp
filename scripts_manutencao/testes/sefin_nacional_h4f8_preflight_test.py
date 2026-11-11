"""H4-F8 - preflight local de HOMOLOGACAO sem rede."""

from pathlib import Path
import runpy
from types import SimpleNamespace

import pytest
import requests

from app.fiscal.providers import sefin_nacional_preflight as preflight
from app.fiscal.providers.sefin_nacional_preflight import (
    PERFIL_XSD_PRODREST,
    PreflightSefinInvalido,
    executar_preflight_local_sefin,
)


BASE_OFICIAL = (
    "https://sefin.producaorestrita.nfse.gov.br"
    "/API/SefinNacional"
)


def _material():
    caminho = Path(__file__).with_name(
        "sefin_nacional_mtls_b8a3a2_test.py"
    )
    namespace = runpy.run_path(str(caminho))
    return namespace["_material"]()


def _configuracao(
    *,
    ambiente="HOMOLOGACAO",
    ativa=False,
    provider="SEFIN_NACIONAL",
):
    return SimpleNamespace(
        provider=provider,
        ambiente=ambiente,
        integracao_ativa=ativa,
    )


def _base(monkeypatch):
    monkeypatch.setenv(
        "NFSE_SEFIN_BASE_URL_HOMOLOGACAO",
        BASE_OFICIAL,
    )


def test_h4f8_001_preflight_completo_sem_rede(
    monkeypatch,
):
    _base(monkeypatch)

    def rede_proibida(*args, **kwargs):
        raise AssertionError(
            "Preflight local nao pode usar rede."
        )

    monkeypatch.setattr(
        requests.sessions.Session,
        "request",
        rede_proibida,
    )

    resultado = executar_preflight_local_sefin(
        configuracao_fiscal=_configuracao(),
        material_certificado=_material(),
    )

    assert resultado.ambiente == "HOMOLOGACAO"
    assert (
        resultado.ambiente_externo
        == "PRODUCAO_RESTRITA"
    )
    assert (
        resultado.perfil_xsd
        == PERFIL_XSD_PRODREST
    )
    assert resultado.base_url == BASE_OFICIAL
    assert resultado.endpoint_emissao == (
        BASE_OFICIAL + "/nfse"
    )
    assert resultado.mtls_ok is True
    assert resultado.integracao_ativa is False
    assert resultado.rede_utilizada is False
    assert len(
        resultado.certificado_sha256
    ) == 64


def test_h4f8_002_producao_e_bloqueada(
    monkeypatch,
):
    _base(monkeypatch)

    with pytest.raises(
        PreflightSefinInvalido,
        match="somente HOMOLOGACAO",
    ):
        executar_preflight_local_sefin(
            configuracao_fiscal=_configuracao(
                ambiente="PRODUCAO"
            ),
            material_certificado=_material(),
        )


def test_h4f8_003_disjuntor_ativo_e_bloqueado(
    monkeypatch,
):
    _base(monkeypatch)

    with pytest.raises(
        PreflightSefinInvalido,
        match="deve permanecer desativado",
    ):
        executar_preflight_local_sefin(
            configuracao_fiscal=_configuracao(
                ativa=True
            ),
            material_certificado=_material(),
        )


def test_h4f8_004_provider_divergente_e_bloqueado(
    monkeypatch,
):
    _base(monkeypatch)

    with pytest.raises(
        PreflightSefinInvalido,
        match="SEFIN_NACIONAL",
    ):
        executar_preflight_local_sefin(
            configuracao_fiscal=_configuracao(
                provider="GEISWEB_TIETE"
            ),
            material_certificado=_material(),
        )


@pytest.mark.parametrize(
    "base",
    [
        "https://sefin.nfse.gov.br/SefinNacional",
        "https://exemplo.invalid/API/SefinNacional",
        "http://sefin.producaorestrita.nfse.gov.br/API/SefinNacional",
    ],
)
def test_h4f8_005_endpoint_nao_oficial_e_bloqueado(
    monkeypatch,
    base,
):
    monkeypatch.setenv(
        "NFSE_SEFIN_BASE_URL_HOMOLOGACAO",
        base,
    )

    with pytest.raises(
        PreflightSefinInvalido,
        match="Producao Restrita oficial",
    ):
        executar_preflight_local_sefin(
            configuracao_fiscal=_configuracao(),
            material_certificado=_material(),
        )


def test_h4f8_006_caminho_base_incorreto_e_bloqueado(
    monkeypatch,
):
    monkeypatch.setenv(
        "NFSE_SEFIN_BASE_URL_HOMOLOGACAO",
        (
            "https://sefin.producaorestrita.nfse.gov.br"
            "/SefinNacional"
        ),
    )

    with pytest.raises(
        PreflightSefinInvalido,
        match="/API/SefinNacional",
    ):
        executar_preflight_local_sefin(
            configuracao_fiscal=_configuracao(),
            material_certificado=_material(),
        )


def test_h4f8_007_perfil_xsd_divergente_e_bloqueado(
    monkeypatch,
):
    _base(monkeypatch)

    original = preflight.obter_configuracao_sefin

    def configuracao(ambiente):
        dados = original(
            ambiente
        )
        dados["perfil_xsd"] = "OUTRO"
        return dados

    monkeypatch.setattr(
        preflight,
        "obter_configuracao_sefin",
        configuracao,
    )

    with pytest.raises(
        PreflightSefinInvalido,
        match="release 20261020",
    ):
        executar_preflight_local_sefin(
            configuracao_fiscal=_configuracao(),
            material_certificado=_material(),
        )


def test_h4f8_008_carrega_certificado_sem_expor_segredo(
    monkeypatch,
):
    _base(monkeypatch)

    material = _material()
    chamadas = []

    def carregar():
        chamadas.append(True)
        return material

    monkeypatch.setattr(
        preflight,
        "carregar_certificado_a1_do_ambiente",
        carregar,
    )

    resultado = executar_preflight_local_sefin(
        configuracao_fiscal=_configuracao(),
    )

    assert chamadas == [True]
    assert resultado.mtls_ok is True
    assert not hasattr(
        resultado,
        "senha",
    )
    assert not hasattr(
        resultado,
        "chave_privada",
    )
