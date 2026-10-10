# -*- coding: utf-8 -*-
"""Integração HTTP do painel, usando exclusivamente SQLite em memória.

Testa autenticação real e renderização Jinja. Nenhuma conexão de produção.
"""
import os
from decimal import Decimal
from types import SimpleNamespace as NS

os.environ["FLASK_ENV"] = "testing"
os.environ["FLASK_CONFIG"] = "testing"
os.environ.pop("DATABASE_URL", None)

import pytest
from app.app import create_app
from app.extensoes import db
from app.auth.usuario_model import Usuario
from app.financeiro.conciliacao_comercial_service import montar_conciliacao


@pytest.fixture(scope="module")
def app_teste():
    app = create_app("testing")
    assert app.config["TESTING"] is True
    assert app.config["SQLALCHEMY_DATABASE_URI"] == "sqlite:///:memory:"
    with app.app_context():
        db.create_all()
        admin = Usuario(
            nome="Administrador Conciliacao", usuario="admin_conciliacao_teste",
            email="admin_conciliacao_teste@example.com", tipo_usuario="admin",
            ativo=True, email_confirmado=True, primeiro_login=False,
        )
        admin.set_senha("SenhaTeste123!")
        colaborador = Usuario(
            nome="Colaborador Conciliacao",
            usuario="colaborador_conciliacao_teste",
            email="colaborador_conciliacao_teste@example.com",
            tipo_usuario="colaborador", ativo=True,
            email_confirmado=True, primeiro_login=False,
        )
        colaborador.set_senha("SenhaTeste123!")
        db.session.add_all([admin, colaborador])
        db.session.commit()
    yield app
    with app.app_context():
        db.session.remove()


def login_admin(cliente):
    resposta = cliente.post("/auth/login", data={
        "identificador": "admin_conciliacao_teste",
        "senha": "SenhaTeste123!",
    }, follow_redirects=False)
    assert resposta.status_code == 302


def dados_simulados():
    cli = NS(nome="Cliente Simulado", id=7)
    prop = NS(
        id=1, codigo="PROPTESTE0001", cliente=cli, cliente_id=7,
        status="aprovada", ativo=True, valor_total=Decimal("100.00"),
    )
    pedido = NS(
        id=2, numero="PEDTESTE0002", proposta_id=None,
        cliente=cli, cliente_id=7, status="CONCLUIDO", ativo=True,
        valor_total=Decimal("50.00"),
    )
    os = NS(
        id=3, numero="OSTESTE0003", proposta_id=1,
        cliente=cli, cliente_id=7, status="concluida", tipo_os="comercial",
        ativo=True, valor_total=Decimal("100.00"),
    )
    return montar_conciliacao(
        [prop], [pedido], [os], [],
        tipo="todos", situacao="todas",
    )


def test_sem_login_redireciona_para_autenticacao(app_teste):
    client = app_teste.test_client()
    resp = client.get("/financeiro/conciliacao-comercial")
    assert resp.status_code == 302
    assert "login" in resp.location


def test_painel_vazio_renderiza_sem_erro_e_nao_grava(app_teste):
    client = app_teste.test_client()
    login_admin(client)
    resp = client.get("/financeiro/conciliacao-comercial")
    assert resp.status_code == 200
    html = resp.get_data(as_text=True)
    assert "Conciliação Comercial" in html
    assert "Nenhum documento encontrado" in html
    assert "Somente revisar" in html


def test_links_e_filtros_com_documentos_simulados(app_teste, monkeypatch):
    import app.financeiro.conciliacao_comercial_routes as rotas

    chamadas = []

    def fake_service(**kwargs):
        chamadas.append(kwargs)
        return dados_simulados()

    monkeypatch.setattr(rotas, "consultar_conciliacao", fake_service)
    client = app_teste.test_client()
    login_admin(client)
    resp = client.get(
        "/financeiro/conciliacao-comercial?tipo=pedido&situacao=todas&busca=teste"
    )
    assert resp.status_code == 200
    html = resp.get_data(as_text=True)
    assert "PROPTESTE0001" in html
    assert "PEDTESTE0002" in html
    assert "OSTESTE0003" in html
    assert "/propostas/1" in html
    assert "/pedido/2" in html
    assert "/ordem_servico/3" in html
    assert chamadas[0]["tipo"] == "pedido"
    assert chamadas[0]["situacao"] == "todas"
    assert chamadas[0]["busca"] == "teste"


def test_rota_nao_aceita_post(app_teste):
    client = app_teste.test_client()
    login_admin(client)
    resp = client.post("/financeiro/conciliacao-comercial")
    assert resp.status_code == 405


def test_menu_financeiro_exibe_conciliacao_para_admin(app_teste):
    client = app_teste.test_client()
    login_admin(client)
    resp = client.get("/dashboard")
    assert resp.status_code == 200
    assert 'href="/financeiro/conciliacao-comercial"' in resp.get_data(as_text=True)


def test_colaborador_nao_acessa_painel_financeiro(app_teste):
    client = app_teste.test_client()
    resposta = client.post("/auth/login", data={
        "identificador": "colaborador_conciliacao_teste",
        "senha": "SenhaTeste123!",
    }, follow_redirects=False)
    assert resposta.status_code == 302
    acesso = client.get("/financeiro/conciliacao-comercial", follow_redirects=False)
    assert acesso.status_code in {302, 403}
    assert "Conciliação Comercial → Financeiro" not in acesso.get_data(as_text=True)
