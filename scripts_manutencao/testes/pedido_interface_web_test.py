# -*- coding: utf-8 -*-
"""Testes de interface web do modulo Pedidos."""

from __future__ import annotations

from pathlib import Path

import pytest


@pytest.fixture()
def app_ctx():
    from app import create_app
    from app.extensoes import db

    app = create_app("testing")

    with app.app_context():
        from app.auth.usuario_model import Usuario  # noqa: F401
        from app.cliente.cliente_model import Cliente  # noqa: F401
        from app.pedido.pedido_model import Pedido, PedidoItem  # noqa: F401
        from app.pedido_compra.pedido_compra_model import PedidoCompra, PedidoCompraItem  # noqa: F401
        from app.produto.produto_model import Produto  # noqa: F401
        from app.servico.servico_model import Servico  # noqa: F401
        from app.proposta.proposta_model import Proposta, PropostaProduto, PropostaServico  # noqa: F401

        db.drop_all()
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


def _seed_cliente_produto(db):
    from app.cliente.cliente_model import Cliente
    from app.produto.produto_model import Produto

    cliente = Cliente(nome="Cliente Teste Pedido", tipo="PF", cpf_cnpj="11122233344")
    produto = Produto(nome="Produto Pedido", preco_venda=120)
    db.session.add(cliente)
    db.session.add(produto)
    db.session.commit()
    return cliente, produto


def _seed_admin(db):
    from app.auth.usuario_model import Usuario

    usuario = Usuario(
        nome="Administrador Teste",
        email="admin.pedidos@teste.local",
        usuario="admin_pedidos",
        tipo_usuario="admin",
        ativo=True,
        email_confirmado=True,
        primeiro_login=False,
    )
    usuario.set_senha("123456")
    db.session.add(usuario)
    db.session.commit()
    return usuario


def _autenticar(client, usuario):
    response = client.post(
        "/auth/login",
        data={"identificador": usuario.usuario, "senha": "123456"},
        follow_redirects=False,
    )
    assert response.status_code == 302


def test_sidebar_exibe_menu_pedidos():
    template_path = Path(__file__).resolve().parents[2] / "app" / "templates" / "base.html"
    source = template_path.read_text(encoding="utf-8")

    assert "url_for('pedido.listar')" in source
    assert "<span class=\"nav-text\">Pedidos de Venda</span>" in source
    assert "url_for('pedido_compra.listar')" in source
    assert "<span class=\"nav-text\">Pedidos de Compra</span>" in source


def test_rotas_pedido_exigem_autenticacao(app_ctx):
    client = app_ctx.test_client()

    response = client.get("/pedido/", follow_redirects=False)
    assert response.status_code == 302
    assert "/auth/login" in response.headers["Location"]

    response = client.get("/pedido/novo", follow_redirects=False)
    assert response.status_code == 302
    assert "/auth/login" in response.headers["Location"]


def test_criar_pedido_via_form_web(app_ctx):
    from app.extensoes import db
    from app.pedido.pedido_model import Pedido

    cliente, produto = _seed_cliente_produto(db)
    usuario = _seed_admin(db)

    client = app_ctx.test_client()
    _autenticar(client, usuario)
    response = client.post(
        "/pedido/novo",
        data={
            "cliente_id": str(cliente.id),
            "status": "RASCUNHO",
            "data_pedido": "2026-08-01",
            "desconto": "10,00",
            "item_tipo[]": ["PRODUTO"],
            "item_referencia_id[]": [f"P:{produto.id}"],
            "item_descricao[]": ["Produto Pedido"],
            "item_quantidade[]": ["2"],
            "item_valor_unitario[]": ["120,00"],
            "item_desconto[]": ["0"],
        },
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"Pedido" in response.data

    pedido = Pedido.query.first()
    assert pedido is not None
    assert pedido.numero.startswith("PED")
    assert pedido.cliente_id == cliente.id
    assert float(pedido.subtotal) == pytest.approx(240.0)
    assert float(pedido.valor_total) == pytest.approx(230.0)


def test_listar_pedidos_renderiza_numero(app_ctx):
    from app.extensoes import db
    from app.pedido.pedido_model import Pedido

    cliente, _produto = _seed_cliente_produto(db)
    usuario = _seed_admin(db)
    pedido = Pedido(cliente_id=cliente.id, responsavel="Comercial")
    db.session.add(pedido)
    db.session.commit()

    client = app_ctx.test_client()
    _autenticar(client, usuario)
    response = client.get("/pedido/")

    assert response.status_code == 200
    assert pedido.numero.encode() in response.data
    assert b"Dashboard" in response.data
    assert b"Clientes" in response.data
    assert b"Fornecedores" in response.data
    assert b"Propostas" in response.data
    assert b"Pedidos de Venda" in response.data
    assert b"Ordens de Servi" in response.data
    assert b"Pedidos de Compra" in response.data
    assert b"Prospec" not in response.data
    assert b"Precifica" not in response.data

