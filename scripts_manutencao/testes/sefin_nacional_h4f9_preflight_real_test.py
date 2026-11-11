"""H4-F9 - testes do preflight real standalone e sem banco."""

import importlib.util
import os
from pathlib import Path
import subprocess
import sys
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


def test_h4f9_001_nao_importa_app_flask_nem_dotenv():
    texto = SCRIPT.read_text(
        encoding="utf-8"
    )

    assert "from app" not in texto
    assert "import app" not in texto
    assert "load_dotenv" not in texto
    assert "dotenv" not in texto.lower()
    assert "create_app" not in texto
    assert "sqlalchemy" not in texto.lower()


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
    except modulo.PreflightStandaloneInvalido as exc:
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
        (
            "https://sefin.producaorestrita.nfse.gov.br"
            "/API/SefinNacional"
        ),
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
        "_validar_xsd",
        lambda: None,
    )
    monkeypatch.setattr(
        modulo,
        "_carregar_material_a1",
        lambda: (
            object(),
            SimpleNamespace(
                fingerprint=lambda algoritmo: bytes.fromhex(
                    "AA" * 32
                )
            ),
            (),
            "PFX_PATH",
        ),
    )

    class ContextoFake:
        def __enter__(self):
            return None

        def __exit__(
            self,
            exc_type,
            exc,
            tb,
        ):
            return False

    monkeypatch.setattr(
        modulo,
        "_materializar_mtls",
        lambda *args, **kwargs: ContextoFake(),
    )

    assert modulo.executar() == 0

    saida = capsys.readouterr().out

    assert "STATUS: OK" in saida
    assert "BANCO ACESSADO: False" in saida
    assert "FLASK INICIALIZADO: False" in saida
    assert "TRANSMISSAO: NAO EXECUTADA" in saida
    assert "SENHA-SUPER-SECRETA" not in saida
    assert "certificado-real.pfx" not in saida
    assert r"C:\segredo" not in saida
    assert "AAAAAAAAAAAAAAAA" not in saida


def test_h4f9_004_endpoint_homologacao_e_fixo(
    monkeypatch,
):
    modulo = _modulo()

    base = (
        "https://sefin.producaorestrita.nfse.gov.br"
        "/API/SefinNacional"
    )

    monkeypatch.setenv(
        modulo.ENV_ENDPOINT,
        base,
    )

    assert modulo._validar_endpoint() == (
        base + "/nfse"
    )


def test_h4f9_005_execucao_direta_nao_inicializa_erp():
    ambiente = dict(
        os.environ
    )

    for nome in (
        "NFSE_SEFIN_BASE_URL_HOMOLOGACAO",
        "NFSE_CERTIFICADO_PFX_PATH",
        "NFSE_CERTIFICADO_PFX_B64_PATH",
        "NFSE_CERTIFICADO_PFX_PASSWORD",
    ):
        ambiente.pop(
            nome,
            None,
        )

    processo = subprocess.run(
        [
            sys.executable,
            "-X",
            "utf8",
            str(SCRIPT),
        ],
        cwd=str(
            SCRIPT.parents[1]
        ),
        env=ambiente,
        capture_output=True,
        text=True,
        check=False,
    )

    saida = (
        processo.stdout
        + processo.stderr
    )

    assert processo.returncode == 1
    assert "STATUS: FALHA" in saida
    assert "Variaveis obrigatorias ausentes" in saida
    assert "ModuleNotFoundError" not in saida
    assert "ERP JSP iniciado com sucesso" not in saida
    assert "Executando migrações automáticas" not in saida
    assert "Tabelas do banco de dados" not in saida
    assert "BANCO ACESSADO: False" in saida
    assert "FLASK INICIALIZADO: False" in saida


def test_h4f9_006_xsd_prodrest_compila_sem_app():
    modulo = _modulo()

    modulo._validar_xsd()


def test_h4f9_007_http_e_bloqueado():
    modulo = _modulo()

    os.environ[
        modulo.ENV_ENDPOINT
    ] = (
        "http://sefin.producaorestrita.nfse.gov.br"
        "/API/SefinNacional"
    )

    try:
        modulo._validar_endpoint()
    except modulo.PreflightStandaloneInvalido as exc:
        assert "HTTPS" in str(exc)
    else:
        raise AssertionError(
            "HTTP deveria ser bloqueado."
        )
