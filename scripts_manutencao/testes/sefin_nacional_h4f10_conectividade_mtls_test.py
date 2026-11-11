"""H4-F10 - contrato de segurança da conectividade mTLS real."""

from contextlib import contextmanager
import importlib.util
import os
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace

import pytest
import requests


SCRIPT = (
    Path(__file__).resolve().parents[1]
    / "sefin_nacional_h4f10_conectividade_mtls.py"
)


def _modulo():
    spec = importlib.util.spec_from_file_location(
        "h4f10_conectividade_mtls",
        SCRIPT,
    )
    modulo = importlib.util.module_from_spec(
        spec
    )
    spec.loader.exec_module(
        modulo
    )
    return modulo


def _preparar_sem_rede(
    monkeypatch,
    modulo,
):
    monkeypatch.setattr(
        modulo.preflight,
        "_validar_variaveis_minimas",
        lambda: None,
    )
    monkeypatch.setattr(
        modulo.preflight,
        "_validar_xsd",
        lambda: None,
    )
    monkeypatch.setattr(
        modulo.preflight,
        "_validar_endpoint",
        lambda: (
            "https://sefin.producaorestrita.nfse.gov.br"
            "/API/SefinNacional/nfse"
        ),
    )
    monkeypatch.setattr(
        modulo.preflight,
        "_carregar_material_a1",
        lambda: (
            object(),
            object(),
            (),
            "PFX_PATH",
        ),
    )

    @contextmanager
    def materializar(*args, **kwargs):
        yield (
            "cert-teste.pem",
            "key-teste.pem",
        )

    monkeypatch.setattr(
        modulo.preflight,
        "_materializar_mtls",
        materializar,
    )


def test_h4f10_001_codigo_nao_possui_post_operacional():
    texto = SCRIPT.read_text(
        encoding="utf-8"
    )

    assert "requests.post" not in texto
    assert ".post(" not in texto
    assert 'method="POST"' not in texto
    assert 'method="HEAD"' in texto
    assert "from app" not in texto
    assert "import app" not in texto


def test_h4f10_002_id_sintetico_tem_formato_oficial():
    modulo = _modulo()

    modulo._validar_id_sintetico()

    assert len(
        modulo.ID_DPS_SINTETICO
    ) == 45
    assert modulo.ID_DPS_SINTETICO.startswith(
        "DPS3554508"
    )


def test_h4f10_003_head_404_prova_fronteira_sem_transmissao(
    monkeypatch,
):
    modulo = _modulo()
    _preparar_sem_rede(
        monkeypatch,
        modulo,
    )

    chamadas = []

    class SessaoFake:
        def request(self, **kwargs):
            chamadas.append(
                kwargs
            )
            return SimpleNamespace(
                status_code=404,
            )

    resultado = modulo.executar_conectividade(
        session=SessaoFake(),
    )

    assert resultado.sucesso is True
    assert resultado.http_status == 404
    assert resultado.metodo == "HEAD"
    assert resultado.servidor_alcancado is True
    assert resultado.rede_utilizada is True
    assert resultado.transmissao_executada is False
    assert resultado.autenticacao_rejeitada is False

    assert len(chamadas) == 1

    chamada = chamadas[0]

    assert chamada["method"] == "HEAD"
    assert chamada["cert"] == (
        "cert-teste.pem",
        "key-teste.pem",
    )
    assert chamada["verify"] is True
    assert chamada["allow_redirects"] is False
    assert "data" not in chamada
    assert "json" not in chamada
    assert "files" not in chamada


def test_h4f10_004_401_e_classificado_como_rejeicao_de_auth(
    monkeypatch,
):
    modulo = _modulo()
    _preparar_sem_rede(
        monkeypatch,
        modulo,
    )

    class SessaoFake:
        def request(self, **kwargs):
            return SimpleNamespace(
                status_code=401,
            )

    resultado = modulo.executar_conectividade(
        session=SessaoFake(),
    )

    assert resultado.sucesso is False
    assert resultado.autenticacao_rejeitada is True
    assert resultado.classificacao == (
        "AUTENTICACAO_REJEITADA"
    )


def test_h4f10_005_falha_tls_e_explicita(
    monkeypatch,
):
    modulo = _modulo()
    _preparar_sem_rede(
        monkeypatch,
        modulo,
    )

    class SessaoFake:
        def request(self, **kwargs):
            raise requests.exceptions.SSLError(
                "teste"
            )

    with pytest.raises(
        modulo.ConectividadeSefinInvalida,
        match="TLS/mTLS",
    ):
        modulo.executar_conectividade(
            session=SessaoFake(),
        )


@pytest.mark.parametrize(
    ("status_code", "sucesso", "classificacao"),
    [
        (
            200,
            True,
            "HEAD_PROCESSADO_DPS_EXISTENTE",
        ),
        (
            400,
            True,
            "HEAD_PROCESSADO_REJEICAO_DE_CONSULTA",
        ),
        (
            403,
            False,
            "AUTENTICACAO_REJEITADA",
        ),
        (
            500,
            False,
            "SERVICO_INDISPONIVEL",
        ),
    ],
)
def test_h4f10_006_classificacao_http(
    status_code,
    sucesso,
    classificacao,
):
    modulo = _modulo()

    (
        resultado_sucesso,
        resultado_classificacao,
        _,
    ) = modulo._classificar_http(
        status_code
    )

    assert resultado_sucesso is sucesso
    assert resultado_classificacao == classificacao


def test_h4f10_007_execucao_sem_ambiente_nao_inicializa_erp():
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
    assert "POST /nfse: NAO EXECUTADO" in saida
    assert "TRANSMISSAO: NAO EXECUTADA" in saida
    assert "ERP JSP iniciado com sucesso" not in saida
    assert "Executando migrações automáticas" not in saida
