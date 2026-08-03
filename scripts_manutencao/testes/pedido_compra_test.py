# -*- coding: utf-8 -*-

from __future__ import annotations

import importlib.util
from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest
import sqlalchemy as sa
from alembic.operations import Operations
from alembic.runtime.migration import MigrationContext


@pytest.fixture()
def app_ctx():
    from app import create_app
    from app.extensoes import db

    app = create_app("testing")

    with app.app_context():
        from app.auth.usuario_model import Usuario  # noqa: F401
        from app.cliente.cliente_model import Cliente  # noqa: F401
        from app.financeiro.financeiro_model import LancamentoFinanceiro  # noqa: F401
        from app.fornecedor.fornecedor_model import Fornecedor  # noqa: F401
        from app.ordem_servico.ordem_servico_model import OrdemServico  # noqa: F401
        from app.pedido.pedido_model import Pedido  # noqa: F401
        from app.pedido_compra.pedido_compra_model import PedidoCompra, PedidoCompraItem  # noqa: F401
        from app.produto.produto_model import Produto  # noqa: F401
        from app.proposta.proposta_model import Proposta  # noqa: F401
        from app.servico.servico_model import Servico  # noqa: F401

        db.drop_all()
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


def _seed_admin(db):
    from app.auth.usuario_model import Usuario

    usuario = Usuario(
        nome="Administrador Compra",
        email="admin.compra@teste.local",
        usuario="admin_compra",
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


def _seed_base_compra(db):
    from app.cliente.cliente_model import Cliente
    from app.fornecedor.fornecedor_model import Fornecedor
    from app.ordem_servico.ordem_servico_model import OrdemServico
    from app.pedido.pedido_model import Pedido
    from app.produto.produto_model import Produto
    from app.proposta.proposta_model import Proposta
    from app.servico.servico_model import Servico

    cliente = Cliente(nome="Cliente Fluxo", tipo="PF", cpf_cnpj="44455566677")
    fornecedor = Fornecedor(nome="Fornecedor Teste Compra")
    produto = Produto(nome="Produto Compra", preco_custo=Decimal("80.00"), preco_venda=Decimal("150.00"), unidade_medida="UN", estoque_atual=7)
    servico = Servico(nome="Servico Compra", valor_base=Decimal("40.00"), tipo_cobranca="servico")
    proposta = Proposta(cliente_id=1, titulo="Proposta Compra", status="aprovada", valor_total=Decimal("500.00"))

    db.session.add(cliente)
    db.session.flush()
    proposta.cliente_id = cliente.id
    pedido_venda = Pedido(cliente_id=cliente.id, proposta_id=None)
    ordem = OrdemServico(numero="OS0001", titulo="OS Teste Compra", cliente_id=cliente.id, data_abertura=date.today())

    db.session.add(fornecedor)
    db.session.add(produto)
    db.session.add(servico)
    db.session.add(proposta)
    db.session.add(pedido_venda)
    db.session.add(ordem)
    db.session.commit()
    return fornecedor, produto, servico, ordem, pedido_venda


def _post_data(fornecedor, produto, servico, ordem, pedido_venda, **overrides):
    data = {
        "fornecedor_id": str(fornecedor.id),
        "data_emissao": "2026-08-03",
        "previsao_entrega": "2026-08-20",
        "status": "APROVADO",
        "finalidade": "PEDIDO_VENDA",
        "solicitante": "Compras",
        "responsavel_compra": "Maria",
        "condicao_pagamento": "28 dias",
        "desconto": "10,00",
        "ordem_servico_id": str(ordem.id),
        "pedido_venda_id": str(pedido_venda.id),
        "item_tipo[]": ["PRODUTO", "SERVICO"],
        "item_referencia_id[]": [f"P:{produto.id}", f"S:{servico.id}"],
        "item_descricao[]": ["Produto Compra", "Servico Compra"],
        "item_unidade[]": ["UN", "SV"],
        "item_quantidade[]": ["2", "1"],
        "item_quantidade_recebida[]": ["0", "0"],
        "item_valor_unitario[]": ["80,00", "40,00"],
        "item_desconto[]": ["0", "0"],
    }
    data.update(overrides)
    return data


def test_rotas_pedido_compra_exigem_autenticacao(app_ctx):
    client = app_ctx.test_client()

    response = client.get("/pedido-compra/", follow_redirects=False)
    assert response.status_code == 302
    assert "/auth/login" in response.headers["Location"]

    response = client.get("/pedido-compra/novo", follow_redirects=False)
    assert response.status_code == 302
    assert "/auth/login" in response.headers["Location"]


def test_sidebar_completa_nas_rotas_de_pedidos(app_ctx):
    from app.extensoes import db

    usuario = _seed_admin(db)
    fornecedor, produto, servico, ordem, pedido_venda = _seed_base_compra(db)
    client = app_ctx.test_client()
    _autenticar(client, usuario)

    response = client.post("/pedido-compra/novo", data=_post_data(fornecedor, produto, servico, ordem, pedido_venda), follow_redirects=True)
    assert response.status_code == 200
    assert b"Dashboard" in response.data
    assert b"Clientes" in response.data
    assert b"Fornecedores" in response.data
    assert b"Propostas" in response.data
    assert b"Pedidos de Venda" in response.data
    assert b"Ordens de Servi" in response.data
    assert b"Pedidos de Compra" in response.data
    assert b"Prospec" not in response.data
    assert b"Precifica" not in response.data


def test_criacao_edicao_listagem_e_visualizacao_pedido_compra(app_ctx):
    from app.extensoes import db
    from app.pedido_compra.pedido_compra_model import PedidoCompra

    usuario = _seed_admin(db)
    fornecedor, produto, servico, ordem, pedido_venda = _seed_base_compra(db)
    client = app_ctx.test_client()
    _autenticar(client, usuario)

    response = client.post("/pedido-compra/novo", data=_post_data(fornecedor, produto, servico, ordem, pedido_venda), follow_redirects=True)
    assert response.status_code == 200
    assert b"PC0001" in response.data

    pedido_compra = PedidoCompra.query.first()
    assert pedido_compra is not None
    assert pedido_compra.fornecedor_id == fornecedor.id
    assert pedido_compra.pedido_venda_id == pedido_venda.id
    assert pedido_compra.ordem_servico_id == ordem.id
    assert pedido_compra.subtotal == Decimal("200.00")
    assert pedido_compra.total == Decimal("190.00")

    response = client.get("/pedido-compra/")
    assert pedido_compra.numero.encode() in response.data

    response = client.post(
        f"/pedido-compra/{pedido_compra.id}/editar",
        data=_post_data(fornecedor, produto, servico, ordem, pedido_venda, solicitante="Compras Editado", desconto="5,00"),
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert b"Compras Editado" in response.data


def test_fornecedor_obrigatorio_e_calculo_decimal(app_ctx):
    from app.extensoes import db
    from app.pedido_compra.pedido_compra_model import PedidoCompra

    usuario = _seed_admin(db)
    fornecedor, produto, servico, ordem, pedido_venda = _seed_base_compra(db)
    client = app_ctx.test_client()
    _autenticar(client, usuario)

    response = client.post(
        "/pedido-compra/novo",
        data=_post_data(fornecedor, produto, servico, ordem, pedido_venda, fornecedor_id="", desconto="0,10", **{"item_quantidade[]": ["1", "1"], "item_valor_unitario[]": ["0,10", "0,20"]}),
        follow_redirects=True,
    )
    assert b"Fornecedor e obrigatorio" in response.data

    response = client.post(
        "/pedido-compra/novo",
        data=_post_data(fornecedor, produto, servico, ordem, pedido_venda, desconto="0,10", **{"item_quantidade[]": ["3", "1"], "item_valor_unitario[]": ["0,10", "0,20"]}),
        follow_redirects=True,
    )
    pedido_compra = PedidoCompra.query.order_by(PedidoCompra.id.desc()).first()
    assert pedido_compra.subtotal == Decimal("0.50")
    assert pedido_compra.total == Decimal("0.40")


def test_status_e_regras_de_recebimento(app_ctx):
    from app.extensoes import db
    from app.pedido_compra.pedido_compra_model import PedidoCompra

    usuario = _seed_admin(db)
    fornecedor, produto, servico, ordem, pedido_venda = _seed_base_compra(db)
    client = app_ctx.test_client()
    _autenticar(client, usuario)

    client.post("/pedido-compra/novo", data=_post_data(fornecedor, produto, servico, ordem, pedido_venda), follow_redirects=True)
    pedido_compra = PedidoCompra.query.first()

    response = client.post(f"/pedido-compra/{pedido_compra.id}/recebimento", data={"item_quantidade_receber[]": ["1", "0"]}, follow_redirects=True)
    assert response.status_code == 200

    db.session.refresh(pedido_compra)
    assert pedido_compra.status == PedidoCompra.STATUS_RECEBIDO_PARCIAL

    response = client.post(f"/pedido-compra/{pedido_compra.id}/recebimento", data={"item_quantidade_receber[]": ["1", "1"]}, follow_redirects=True)
    assert response.status_code == 200

    db.session.refresh(pedido_compra)
    assert pedido_compra.status == PedidoCompra.STATUS_RECEBIDO

    response = client.post(f"/pedido-compra/{pedido_compra.id}/recebimento", data={"item_quantidade_receber[]": ["1", "0"]}, follow_redirects=True)
    assert b"Recebimento permitido apenas" in response.data


def test_bloqueia_recebimento_excedente_e_cancelado(app_ctx):
    from app.extensoes import db
    from app.pedido_compra.pedido_compra_model import PedidoCompra

    usuario = _seed_admin(db)
    fornecedor, produto, servico, ordem, pedido_venda = _seed_base_compra(db)
    client = app_ctx.test_client()
    _autenticar(client, usuario)

    client.post("/pedido-compra/novo", data=_post_data(fornecedor, produto, servico, ordem, pedido_venda), follow_redirects=True)
    pedido_compra = PedidoCompra.query.first()

    response = client.post(f"/pedido-compra/{pedido_compra.id}/recebimento", data={"item_quantidade_receber[]": ["3", "0"]}, follow_redirects=True)
    assert b"nao pode exceder" in response.data

    client.post(f"/pedido-compra/{pedido_compra.id}/cancelar", follow_redirects=True)
    response = client.post(f"/pedido-compra/{pedido_compra.id}/recebimento", data={"item_quantidade_receber[]": ["1", "0"]}, follow_redirects=True)
    assert b"Pedido cancelado nao pode receber itens" in response.data


def test_nao_gera_financeiro_nem_movimenta_estoque(app_ctx):
    from app.extensoes import db
    from app.financeiro.financeiro_model import LancamentoFinanceiro
    from app.pedido_compra.pedido_compra_model import PedidoCompra
    from app.produto.produto_model import Produto

    usuario = _seed_admin(db)
    fornecedor, produto, servico, ordem, pedido_venda = _seed_base_compra(db)
    estoque_inicial = produto.estoque_atual
    client = app_ctx.test_client()
    _autenticar(client, usuario)

    client.post("/pedido-compra/novo", data=_post_data(fornecedor, produto, servico, ordem, pedido_venda), follow_redirects=True)
    pedido_compra = PedidoCompra.query.first()

    assert pedido_compra is not None
    assert LancamentoFinanceiro.query.count() == 0
    produto_atualizado = Produto.query.get(produto.id)
    assert produto_atualizado.estoque_atual == estoque_inicial


def test_migration_pedido_compra_em_banco_temporario(tmp_path):
    migration_path = Path(__file__).resolve().parents[2] / "migrations" / "versions" / "20260803_01_create_pedidos_compra.py"
    spec = importlib.util.spec_from_file_location("migration_pedido_compra", migration_path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)

    db_file = tmp_path / "pedido_compra_migration.db"
    engine = sa.create_engine(f"sqlite:///{db_file}")
    metadata = sa.MetaData()
    sa.Table("fornecedores", metadata, sa.Column("id", sa.Integer, primary_key=True))
    sa.Table("ordem_servico", metadata, sa.Column("id", sa.Integer, primary_key=True))
    sa.Table("pedidos", metadata, sa.Column("id", sa.Integer, primary_key=True))
    sa.Table("produtos", metadata, sa.Column("id", sa.Integer, primary_key=True))
    sa.Table("servicos", metadata, sa.Column("id", sa.Integer, primary_key=True))
    metadata.create_all(engine)

    with engine.begin() as connection:
        context = MigrationContext.configure(connection)
        operations = Operations(context)
        original_op = module.op
        module.op = operations
        try:
            module.upgrade()
            inspector = sa.inspect(connection)
            assert "pedidos_compra" in inspector.get_table_names()
            assert "pedido_compra_itens" in inspector.get_table_names()
            colunas_pedido = {col["name"] for col in inspector.get_columns("pedidos_compra")}
            assert {"numero", "fornecedor_id", "ordem_servico_id", "pedido_venda_id", "finalidade", "status", "subtotal", "desconto", "total"}.issubset(colunas_pedido)
            module.downgrade()
            inspector = sa.inspect(connection)
            assert "pedidos_compra" not in inspector.get_table_names()
            assert "pedido_compra_itens" not in inspector.get_table_names()
        finally:
            module.op = original_op
