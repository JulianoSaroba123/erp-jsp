# -*- coding: utf-8 -*-
"""Testes isolados da seguranca de sessao.

Nao importa app.app nem cria a aplicacao de producao. Usa um Flask minimo
com usuarios falsos e relogio controlado; nunca toca no banco.
"""
import importlib.util
from pathlib import Path
from types import SimpleNamespace

import pytest
from flask import Flask, jsonify, redirect, request, session, url_for
from flask_login import LoginManager, UserMixin, login_required, login_user


MODULE_PATH = (
    Path(__file__).resolve().parents[2]
    / "app" / "auth" / "idle_session.py"
)


class UsuarioFalso(UserMixin):
    def __init__(self, user_id="1"):
        self.id = user_id


@pytest.fixture
def cenario():
    spec = importlib.util.spec_from_file_location(
        "jsp_idle_test_isolado", MODULE_PATH
    )
    idle = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(idle)

    relogio = [100000.0]
    idle.time = SimpleNamespace(time=lambda: relogio[0])

    app = Flask("jsp_idle_isolado")
    app.config.update(
        SECRET_KEY="somente-testes-sessao",
        TESTING=True,
        PERMANENT_SESSION_LIFETIME=3600,
    )

    login_manager = LoginManager(app)
    login_manager.login_view = "login"

    @login_manager.user_loader
    def obter_usuario(user_id):
        return UsuarioFalso(user_id)

    @app.route("/auth/login", methods=["GET", "POST"], endpoint="login")
    def login():
        if request.method == "POST":
            login_user(UsuarioFalso(), remember=False)
            idle.activate_idle_session()
            return "autenticado"
        return "login"

    @app.route("/auth/legacy", methods=["POST"])
    def login_legacy():
        login_user(UsuarioFalso(), remember=True)
        return "antigo"

    @app.route("/auth/logout", endpoint="auth.logout")
    @login_required
    def logout():
        idle.expire_idle_session()
        return redirect(url_for("login"))

    @app.route("/private")
    @login_required
    def pagina_privada():
        return "conteudo reservado"

    @app.route("/api/poll")
    @login_required
    def api_poll():
        return jsonify({"ok": True})

    idle.init_idle_session(app)
    return app, app.test_client(), idle, relogio


def _login(client):
    resposta = client.post("/auth/login")
    assert resposta.status_code == 200
    with client.session_transaction() as sessao:
        return sessao["_jsp_idle_csrf"]


def _navegar(client, path="/private"):
    return client.get(
        path,
        headers={
            "Accept": "text/html",
            "Sec-Fetch-Mode": "navigate",
        },
        follow_redirects=False,
    )


def test_login_inicia_sessao_com_marcadores_e_sem_remember(cenario):
    _, cliente, _, _ = cenario
    token = _login(cliente)
    assert len(token) >= 32
    resposta = _navegar(cliente)
    assert resposta.status_code == 200
    assert "no-store" in resposta.headers["Cache-Control"]


def test_logout_apos_30_minutos_bloqueia_navegacao(cenario):
    _, cliente, _, tempo = cenario
    _login(cliente)
    tempo[0] += 1801
    resposta = _navegar(cliente)
    assert resposta.status_code == 302
    assert "/auth/login" in resposta.headers["Location"]
    with cliente.session_transaction() as sessao:
        assert "_user_id" not in sessao
        assert "_jsp_idle_last_at" not in sessao


def test_atividade_navegacao_renova_antes_do_prazo(cenario):
    _, cliente, _, tempo = cenario
    _login(cliente)
    tempo[0] += 1700
    assert _navegar(cliente).status_code == 200
    tempo[0] += 1700
    assert _navegar(cliente).status_code == 200


def test_requisicao_automatica_nao_renova(cenario):
    _, cliente, _, tempo = cenario
    _login(cliente)
    tempo[0] += 1790
    resposta = cliente.get(
        "/api/poll",
        headers={"Accept": "application/json", "Sec-Fetch-Mode": "cors"},
    )
    assert resposta.status_code == 200
    tempo[0] += 11
    assert _navegar(cliente).status_code == 302


def test_ping_precisa_de_csrf_valido(cenario):
    _, cliente, _, tempo = cenario
    token = _login(cliente)
    tempo[0] += 100
    assert cliente.post("/auth/sessao/atividade").status_code == 403
    assert cliente.post(
        "/auth/sessao/atividade", headers={"X-JSP-Idle-CSRF": "invalido"}
    ).status_code == 403
    resposta = cliente.post(
        "/auth/sessao/atividade",
        headers={"X-JSP-Idle-CSRF": token},
    )
    assert resposta.status_code == 200
    assert resposta.get_json()["ok"] is True


def test_ping_nao_reativa_apos_expiracao(cenario):
    _, cliente, _, tempo = cenario
    token = _login(cliente)
    tempo[0] += 1801
    resposta = cliente.post(
        "/auth/sessao/atividade",
        headers={"X-JSP-Idle-CSRF": token},
    )
    assert resposta.status_code == 401
    assert resposta.get_json()["expired"] is True


def test_cookie_remember_antigo_nao_contorna_prazo(cenario):
    _, cliente, _, _ = cenario
    assert cliente.post("/auth/legacy").status_code == 200
    resposta = _navegar(cliente)
    assert resposta.status_code == 302
    assert "/auth/login" in resposta.headers["Location"]


def test_sessao_sem_marcador_e_recusada(cenario):
    _, cliente, _, _ = cenario
    _login(cliente)
    with cliente.session_transaction() as sessao:
        del sessao["_jsp_idle_last_at"]
    assert _navegar(cliente).status_code == 302


def test_usuario_nao_autenticado_recebe_401_no_ping(cenario):
    _, cliente, _, _ = cenario
    resposta = cliente.post("/auth/sessao/atividade")
    assert resposta.status_code == 401


def test_logout_manual_revoga_sessao(cenario):
    _, cliente, _, _ = cenario
    _login(cliente)
    assert cliente.get("/auth/logout").status_code == 302
    with cliente.session_transaction() as sessao:
        assert "_user_id" not in sessao


def test_nao_duplicar_hooks_em_inicializacao(cenario):
    app, cliente, idle, _ = cenario
    idle.init_idle_session(app)
    _login(cliente)
    assert _navegar(cliente).status_code == 200
