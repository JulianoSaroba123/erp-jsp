"""H4-F9 - teste do script operacional de preflight real local."""

import importlib.util
from pathlib import Path
from types import SimpleNamespace


SCRIPT = (
    Path(__file__).resolve().parents[1]
    / "sefin_nacional_h4f9_preflight_real.py"
)


def _modulo():
    spec = importlib.util.spec_from_file_location(
        "h4f9_preflight_real",
        SCRIPT,
    )
    modulo = importlib.util.module_from_spec(
        spec
    )
    spec.loader.exec_module(
        modulo
    )
    return modulo


def test_h4f9_001_nao_carrega_dotenv_automaticamente():
    texto = SCRIPT.read_text(
        encoding="utf-8"
    )

    assert "load_dotenv" not in texto
    assert "dotenv" not in texto.lower()


def test_h4f9_002_exige_endpoint_e_certificado(
    monkeypatch,
):
    modulo = _modulo()

    for nome in (
        modulo.ENV_ENDPOINT,
        modulo.ENV_PFX,
        modulo.ENV_PFX_B64,
        modulo.ENV_PFX_PASSWORD,
    ):
        monkeypatch.delenv(
            nome,
            raising=False,
        )

    try:
        modulo._validar_variaveis_minimas()
    except modulo.PreflightSefinInvalido as exc:
        mensagem = str(
            exc
        )
    else:
        raise AssertionError(
            "Preflight deveria bloquear ambiente incompleto."
        )

    assert modulo.ENV_ENDPOINT in mensagem
    assert modulo.ENV_PFX in mensagem
    assert modulo.ENV_PFX_B64 in mensagem
    assert modulo.ENV_PFX_PASSWORD not in mensagem


def test_h4f9_003_saida_nao_expoe_segredos(
    monkeypatch,
    capsys,
):
    modulo = _modulo()

    monkeypatch.setenv(
        modulo.ENV_ENDPOINT,
        "https://sefin.producaorestrita.nfse.gov.br/API/SefinNacional",
    )
    monkeypatch.setenv(
        modulo.ENV_PFX,
        r"C:\segredo\certificado-real.pfx",
    )
    monkeypatch.setenv(
        modulo.ENV_PFX_PASSWORD,
        "SENHA-SUPER-SECRETA",
    )

    monkeypatch.setattr(
        modulo,
        "executar_preflight_local_sefin",
        lambda **kwargs: SimpleNamespace(
            ambiente="HOMOLOGACAO",
            ambiente_externo="PRODUCAO_RESTRITA",
            perfil_xsd="PRODREST-v1.01-20261020",
            endpoint_emissao=(
                "https://sefin.producaorestrita.nfse.gov.br"
                "/API/SefinNacional/nfse"
            ),
            certificado_sha256=(
                "A" * 64
            ),
            mtls_ok=True,
            integracao_ativa=False,
            rede_utilizada=False,
        ),
    )

    assert modulo.executar() == 0

    saida = capsys.readouterr().out

    assert "STATUS: OK" in saida
    assert "TRANSMISSAO: NAO EXECUTADA" in saida
    assert "REDE UTILIZADA: False" in saida
    assert "SENHA-SUPER-SECRETA" not in saida
    assert "certificado-real.pfx" not in saida
    assert "C:\\segredo" not in saida
    assert "AAAAAAAAAAAAAAAA" not in saida


def test_h4f9_004_configuracao_sintetica_mantem_disjuntor_off(
    monkeypatch,
):
    modulo = _modulo()

    monkeypatch.setenv(
        modulo.ENV_ENDPOINT,
        "https://sefin.producaorestrita.nfse.gov.br/API/SefinNacional",
    )
    monkeypatch.setenv(
        modulo.ENV_PFX_B64,
        r"C:\segredo\certificado.b64",
    )

    capturado = {}

    def preflight(**kwargs):
        capturado.update(
            kwargs
        )
        return SimpleNamespace(
            ambiente="HOMOLOGACAO",
            ambiente_externo="PRODUCAO_RESTRITA",
            perfil_xsd="PRODREST-v1.01-20261020",
            endpoint_emissao=(
                "https://sefin.producaorestrita.nfse.gov.br"
                "/API/SefinNacional/nfse"
            ),
            certificado_sha256="B" * 64,
            mtls_ok=True,
            integracao_ativa=False,
            rede_utilizada=False,
        )

    monkeypatch.setattr(
        modulo,
        "executar_preflight_local_sefin",
        preflight,
    )

    assert modulo.executar() == 0

    configuracao = capturado[
        "configuracao_fiscal"
    ]

    assert configuracao.provider == "SEFIN_NACIONAL"
    assert configuracao.ambiente == "HOMOLOGACAO"
    assert configuracao.integracao_ativa is False
