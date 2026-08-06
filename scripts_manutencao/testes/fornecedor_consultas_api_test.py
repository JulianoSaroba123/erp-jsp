# -*- coding: utf-8 -*-

from __future__ import annotations

from pathlib import Path

import pytest


@pytest.fixture()
def app_ctx():
    from app import create_app

    app = create_app("testing")
    with app.app_context():
        yield app


class _FakeResponse:
    def __init__(self, status_code=200, payload=None):
        self.status_code = status_code
        self._payload = payload or {}

    def json(self):
        return self._payload


def test_consultar_cep_sucesso_aceita_com_ou_sem_hifen(app_ctx, monkeypatch):
    client = app_ctx.test_client()
    chamadas = []

    def fake_get(url, timeout):
        chamadas.append((url, timeout))
        return _FakeResponse(
            200,
            {
                "cep": "12345-678",
                "logradouro": "Rua Teste",
                "bairro": "Centro",
                "localidade": "Sao Paulo",
                "uf": "SP",
            },
        )

    import app.fornecedor.consultas_api as consultas_api

    monkeypatch.setattr(consultas_api.requests, "get", fake_get)

    for cep in ["12345-678", "12345678"]:
        response = client.get(f"/fornecedor/api/consultar-cep/{cep}")
        assert response.status_code == 200
        payload = response.get_json()
        assert payload["success"] is True
        assert payload["data"]["cidade"] == "Sao Paulo"
        assert payload["data"]["uf"] == "SP"

    assert len(chamadas) == 2
    for url, timeout in chamadas:
        assert url.endswith("/12345678/json/")
        assert timeout == 10


def test_consultar_cep_invalido_retorna_400(app_ctx):
    client = app_ctx.test_client()
    response = client.get("/fornecedor/api/consultar-cep/1234")
    assert response.status_code == 400
    payload = response.get_json()
    assert payload["success"] is False
    assert "8 dígitos" in payload["error"]


def test_consultar_cep_nao_encontrado_retorna_404(app_ctx, monkeypatch):
    client = app_ctx.test_client()

    def fake_get(url, timeout):
        return _FakeResponse(200, {"erro": True})

    import app.fornecedor.consultas_api as consultas_api

    monkeypatch.setattr(consultas_api.requests, "get", fake_get)

    response = client.get("/fornecedor/api/consultar-cep/12345678")
    assert response.status_code == 404
    payload = response.get_json()
    assert payload["success"] is False


def test_consultar_cep_erro_servico_externo_retorna_500(app_ctx, monkeypatch):
    client = app_ctx.test_client()

    def fake_get(url, timeout):
        return _FakeResponse(503, {})

    import app.fornecedor.consultas_api as consultas_api

    monkeypatch.setattr(consultas_api.requests, "get", fake_get)

    response = client.get("/fornecedor/api/consultar-cep/12345678")
    assert response.status_code == 500
    payload = response.get_json()
    assert payload["success"] is False


def test_consultar_cep_falha_rede_retorna_500(app_ctx, monkeypatch):
    client = app_ctx.test_client()

    def fake_get(url, timeout):
        raise RuntimeError("network down")

    import app.fornecedor.consultas_api as consultas_api

    monkeypatch.setattr(consultas_api.requests, "get", fake_get)

    response = client.get("/fornecedor/api/consultar-cep/12345678")
    assert response.status_code == 500
    payload = response.get_json()
    assert payload["success"] is False


def test_formulario_fornecedor_mantem_ids_selectors_e_endpoints_cep_cnpj():
    template_path = Path(__file__).resolve().parents[2] / "app" / "fornecedor" / "templates" / "fornecedor" / "form.html"
    source = template_path.read_text(encoding="utf-8")

    for expected_id in [
        "id=\"btn-consultar-cep\"",
        "id=\"btn-consultar-cnpj\"",
        "id=\"cep\"",
        "id=\"endereco\"",
        "id=\"bairro\"",
        "id=\"cidade\"",
        "id=\"estado\"",
        "id=\"cpf_cnpj\"",
    ]:
        assert expected_id in source

    assert "/fornecedor/api/consultar-cep/${cepLimpo}" in source
    assert "/fornecedor/api/consultar-cnpj/${cnpjLimpo}" in source
    assert source.count("btnConsultarCep.addEventListener('click'") == 1
    assert source.count("btnConsultarCnpj.addEventListener('click'") == 1
