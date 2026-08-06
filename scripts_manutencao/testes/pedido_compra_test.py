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


def _seed_user(db, tipo_usuario: str, username: str):
    from app.auth.usuario_model import Usuario

    usuario = Usuario(
        nome=f"Usuario {tipo_usuario}",
        email=f"{username}@teste.local",
        usuario=username,
        tipo_usuario=tipo_usuario,
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
    db.session.add(cliente)
    db.session.flush()

    fornecedor = Fornecedor(nome="Fornecedor Teste Compra")
    produto = Produto(nome="Produto Compra", preco_custo=Decimal("80.00"), preco_venda=Decimal("150.00"), unidade_medida="UN", estoque_atual=7)
    servico = Servico(nome="Servico Compra", valor_base=Decimal("40.00"), tipo_cobranca="servico")
    proposta = Proposta(cliente_id=cliente.id, titulo="Proposta Compra", status="aprovada", valor_total=Decimal("500.00"))
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
        "item_id[]": ["", ""],
        "item_tipo[]": ["PRODUTO", "SERVICO"],
        "item_referencia_id[]": [f"P:{produto.id}", f"S:{servico.id}"],
        "item_descricao[]": ["Produto Compra", "Servico Compra"],
        "item_unidade[]": ["UN", "SV"],
        "item_quantidade[]": ["2", "1"],
        "item_valor_unitario[]": ["80,00", "40,00"],
        "item_desconto[]": ["0", "0"],
    }
    data.update(overrides)
    return data


def _criar_pedido_compra(client, fornecedor, produto, servico, ordem, pedido_venda):
    response = client.post("/pedido-compra/novo", data=_post_data(fornecedor, produto, servico, ordem, pedido_venda), follow_redirects=True)
    assert response.status_code == 200


def test_rotas_pedido_compra_exigem_autenticacao(app_ctx):
    client = app_ctx.test_client()

    response = client.get("/pedido-compra/", follow_redirects=False)
    assert response.status_code == 302
    assert "/auth/login" in response.headers["Location"]

    response = client.get("/pedido-compra/novo", follow_redirects=False)
    assert response.status_code == 302
    assert "/auth/login" in response.headers["Location"]


def test_matriz_permissoes_readonly_e_usuario(app_ctx):
    from app.extensoes import db
    from app.pedido_compra.pedido_compra_model import PedidoCompra

    readonly = _seed_user(db, "readonly", "readonly_compra")
    usuario = _seed_user(db, "usuario", "usuario_compra")
    fornecedor, produto, servico, ordem, pedido_venda = _seed_base_compra(db)

    client = app_ctx.test_client()
    _autenticar(client, usuario)
    _criar_pedido_compra(client, fornecedor, produto, servico, ordem, pedido_venda)
    pedido = PedidoCompra.query.first()

    client.get("/auth/logout", follow_redirects=False)
    _autenticar(client, readonly)

    assert client.get("/pedido-compra/").status_code == 200
    assert client.get(f"/pedido-compra/{pedido.id}").status_code == 200
    assert client.get(f"/pedido-compra/{pedido.id}/imprimir").status_code == 200

    for rota in [
        "/pedido-compra/novo",
        f"/pedido-compra/{pedido.id}/editar",
        f"/pedido-compra/{pedido.id}/cancelar",
        f"/pedido-compra/{pedido.id}/recebimento",
    ]:
        response = client.post(rota, data={}, follow_redirects=False)
        assert response.status_code == 302
        assert "/dashboard" in response.headers.get("Location", "")

    for rota in [
        "/pedido-compra/novo",
        f"/pedido-compra/{pedido.id}/editar",
        f"/pedido-compra/{pedido.id}/cancelar",
        f"/pedido-compra/{pedido.id}/recebimento",
    ]:
        response = client.get(rota, follow_redirects=False)
        assert response.status_code == 302
        assert "/dashboard" in response.headers.get("Location", "")


def test_status_recebimento_nao_e_aceito_no_formulario_geral(app_ctx):
    from app.extensoes import db
    from app.pedido_compra.pedido_compra_model import PedidoCompra

    usuario = _seed_user(db, "usuario", "usuario_status")
    fornecedor, produto, servico, ordem, pedido_venda = _seed_base_compra(db)
    client = app_ctx.test_client()
    _autenticar(client, usuario)

    response = client.post(
        "/pedido-compra/novo",
        data=_post_data(fornecedor, produto, servico, ordem, pedido_venda, status="RECEBIDO"),
        follow_redirects=True,
    )
    assert b"Status de recebimento" in response.data
    assert PedidoCompra.query.count() == 0


def test_status_cancelado_nao_e_aceito_no_formulario_geral(app_ctx):
    from app.extensoes import db
    from app.pedido_compra.pedido_compra_model import PedidoCompra

    usuario = _seed_user(db, "usuario", "usuario_status_cancelado")
    fornecedor, produto, servico, ordem, pedido_venda = _seed_base_compra(db)
    client = app_ctx.test_client()
    _autenticar(client, usuario)

    response = client.post(
        "/pedido-compra/novo",
        data=_post_data(fornecedor, produto, servico, ordem, pedido_venda, status="CANCELADO"),
        follow_redirects=True,
    )
    assert b"Status cancelado" in response.data
    assert PedidoCompra.query.count() == 0


def test_quantidade_recebida_do_formulario_geral_e_ignorada_no_cadastro(app_ctx):
    from app.extensoes import db
    from app.pedido_compra.pedido_compra_model import PedidoCompra

    usuario = _seed_user(db, "usuario", "usuario_qtd_cadastro")
    fornecedor, produto, servico, ordem, pedido_venda = _seed_base_compra(db)
    client = app_ctx.test_client()
    _autenticar(client, usuario)

    data = _post_data(fornecedor, produto, servico, ordem, pedido_venda)
    data["item_quantidade_recebida[]"] = ["999", "999"]
    response = client.post("/pedido-compra/novo", data=data, follow_redirects=True)
    assert response.status_code == 200

    pedido = PedidoCompra.query.first()
    itens = pedido.itens.order_by("id").all()
    assert all(item.quantidade_recebida == Decimal("0.000") for item in itens)


def test_edicao_preserva_recebimento_e_bloqueia_reducao_abaixo_do_recebido(app_ctx):
    from app.extensoes import db
    from app.pedido_compra.pedido_compra_model import PedidoCompra

    usuario = _seed_user(db, "usuario", "usuario_qtd_edicao")
    fornecedor, produto, servico, ordem, pedido_venda = _seed_base_compra(db)
    client = app_ctx.test_client()
    _autenticar(client, usuario)

    _criar_pedido_compra(client, fornecedor, produto, servico, ordem, pedido_venda)
    pedido = PedidoCompra.query.first()
    item = pedido.itens.order_by("id").first()

    client.post(f"/pedido-compra/{pedido.id}/recebimento", data={"item_quantidade_receber[]": ["1", "0"]}, follow_redirects=True)
    db.session.refresh(item)
    assert item.quantidade_recebida == Decimal("1.000")

    response = client.post(
        f"/pedido-compra/{pedido.id}/editar",
        data={
            **_post_data(fornecedor, produto, servico, ordem, pedido_venda),
            "item_id[]": [str(item.id), ""],
            "item_quantidade[]": ["0,5", "1"],
            "item_quantidade_recebida[]": ["0", "0"],
        },
        follow_redirects=True,
    )
    assert b"Quantidade comprada nao pode ser menor" in response.data


def test_item_recebido_nao_pode_mudar_identidade(app_ctx):
    from app.extensoes import db
    from app.pedido_compra.pedido_compra_model import PedidoCompra
    from app.produto.produto_model import Produto
    from app.servico.servico_model import Servico

    usuario = _seed_user(db, "usuario", "usuario_identidade")
    fornecedor, produto, servico, ordem, pedido_venda = _seed_base_compra(db)
    produto2 = Produto(nome="Produto Compra 2", preco_custo=Decimal("10.00"), preco_venda=Decimal("20.00"), unidade_medida="UN", estoque_atual=2)
    servico2 = Servico(nome="Servico Compra 2", valor_base=Decimal("15.00"), tipo_cobranca="servico")
    db.session.add(produto2)
    db.session.add(servico2)
    db.session.commit()

    client = app_ctx.test_client()
    _autenticar(client, usuario)

    _criar_pedido_compra(client, fornecedor, produto, servico, ordem, pedido_venda)
    pedido = PedidoCompra.query.first()
    item_produto = pedido.itens.order_by("id").first()

    client.post(f"/pedido-compra/{pedido.id}/recebimento", data={"item_quantidade_receber[]": ["1", "0"]}, follow_redirects=True)

    base = _post_data(fornecedor, produto, servico, ordem, pedido_venda)
    tentativas = [
        {
            **base,
            "item_id[]": [str(item_produto.id), ""],
            "item_tipo[]": ["SERVICO", "SERVICO"],
            "item_referencia_id[]": [f"S:{servico.id}", f"S:{servico.id}"],
        },
        {
            **base,
            "item_id[]": [str(item_produto.id), ""],
            "item_tipo[]": ["PRODUTO", "SERVICO"],
            "item_referencia_id[]": [f"P:{produto2.id}", f"S:{servico.id}"],
        },
    ]

    for payload in tentativas:
        response = client.post(f"/pedido-compra/{pedido.id}/editar", data=payload, follow_redirects=True)
        assert b"ja possui recebimento" in response.data

    db.session.refresh(item_produto)
    assert item_produto.tipo_item == "PRODUTO"
    assert item_produto.produto_id == produto.id
    assert item_produto.servico_id is None
    assert item_produto.quantidade_recebida == Decimal("1.000")


def test_item_recebido_nao_pode_ser_excluido_na_edicao(app_ctx):
    from app.extensoes import db
    from app.pedido_compra.pedido_compra_model import PedidoCompra, PedidoCompraItem

    usuario = _seed_user(db, "usuario", "usuario_exclusao_item")
    fornecedor, produto, servico, ordem, pedido_venda = _seed_base_compra(db)
    client = app_ctx.test_client()
    _autenticar(client, usuario)

    _criar_pedido_compra(client, fornecedor, produto, servico, ordem, pedido_venda)
    pedido = PedidoCompra.query.first()
    itens = pedido.itens.order_by(PedidoCompraItem.id.asc()).all()

    client.post(f"/pedido-compra/{pedido.id}/recebimento", data={"item_quantidade_receber[]": ["1", "0"]}, follow_redirects=True)

    response = client.post(
        f"/pedido-compra/{pedido.id}/editar",
        data={
            **_post_data(fornecedor, produto, servico, ordem, pedido_venda),
            "item_id[]": [str(itens[1].id)],
            "item_tipo[]": ["SERVICO"],
            "item_referencia_id[]": [f"S:{servico.id}"],
            "item_descricao[]": ["Servico Compra"],
            "item_unidade[]": ["SV"],
            "item_quantidade[]": ["1"],
            "item_valor_unitario[]": ["40,00"],
            "item_desconto[]": ["0"],
        },
        follow_redirects=True,
    )
    assert b"Nao e permitido excluir item" in response.data


def test_formulario_tem_controles_de_multiplos_itens(app_ctx):
    from app.extensoes import db

    usuario = _seed_user(db, "usuario", "usuario_form_multi")
    _seed_base_compra(db)
    client = app_ctx.test_client()
    _autenticar(client, usuario)

    response = client.get("/pedido-compra/novo")
    assert b"Adicionar item" in response.data
    assert b"btn-remover-item" in response.data
    assert b"item-row-template" in response.data
    assert b'option value="CANCELADO"' not in response.data
    assert b'option value="RECEBIDO_PARCIAL"' not in response.data
    assert b'option value="RECEBIDO"' not in response.data


def test_pedido_com_dois_ou_mais_itens_funciona(app_ctx):
    from app.extensoes import db
    from app.pedido_compra.pedido_compra_model import PedidoCompra

    usuario = _seed_user(db, "usuario", "usuario_dois_itens")
    fornecedor, produto, servico, ordem, pedido_venda = _seed_base_compra(db)
    client = app_ctx.test_client()
    _autenticar(client, usuario)

    _criar_pedido_compra(client, fornecedor, produto, servico, ordem, pedido_venda)
    pedido = PedidoCompra.query.first()
    assert pedido.itens.count() >= 2


def test_nao_gera_financeiro_nem_movimenta_estoque(app_ctx):
    from app.extensoes import db
    from app.financeiro.financeiro_model import LancamentoFinanceiro
    from app.pedido_compra.pedido_compra_model import PedidoCompra
    from app.produto.produto_model import Produto

    usuario = _seed_user(db, "usuario", "usuario_financeiro")
    fornecedor, produto, servico, ordem, pedido_venda = _seed_base_compra(db)
    estoque_inicial = produto.estoque_atual
    client = app_ctx.test_client()
    _autenticar(client, usuario)

    _criar_pedido_compra(client, fornecedor, produto, servico, ordem, pedido_venda)
    pedido_compra = PedidoCompra.query.first()

    assert pedido_compra is not None
    assert LancamentoFinanceiro.query.count() == 0
    produto_atualizado = Produto.query.get(produto.id)
    assert produto_atualizado.estoque_atual == estoque_inicial


def test_cancelamento_somente_rota_dedicada_e_cancelado_bloqueado(app_ctx):
    from app.extensoes import db
    from app.pedido_compra.pedido_compra_model import PedidoCompra

    usuario = _seed_user(db, "usuario", "usuario_cancelamento")
    operador = _seed_user(db, "operador", "operador_cancelamento")
    fornecedor, produto, servico, ordem, pedido_venda = _seed_base_compra(db)

    client = app_ctx.test_client()
    _autenticar(client, usuario)
    _criar_pedido_compra(client, fornecedor, produto, servico, ordem, pedido_venda)
    pedido = PedidoCompra.query.first()

    response = client.post(
        f"/pedido-compra/{pedido.id}/editar",
        data={**_post_data(fornecedor, produto, servico, ordem, pedido_venda), "status": "CANCELADO"},
        follow_redirects=True,
    )
    assert b"Status cancelado" in response.data
    db.session.refresh(pedido)
    assert pedido.status != PedidoCompra.STATUS_CANCELADO

    client.get("/auth/logout", follow_redirects=False)
    _autenticar(client, operador)
    response = client.post(
        f"/pedido-compra/{pedido.id}/editar",
        data={**_post_data(fornecedor, produto, servico, ordem, pedido_venda), "status": "CANCELADO"},
        follow_redirects=True,
    )
    assert b"Status cancelado" in response.data

    client.get("/auth/logout", follow_redirects=False)
    _autenticar(client, usuario)
    response = client.post(f"/pedido-compra/{pedido.id}/cancelar", data={}, follow_redirects=True)
    assert b"cancelado com sucesso" in response.data
    db.session.refresh(pedido)
    assert pedido.status == PedidoCompra.STATUS_CANCELADO

    response = client.post(
        f"/pedido-compra/{pedido.id}/editar",
        data={**_post_data(fornecedor, produto, servico, ordem, pedido_venda), "status": "APROVADO"},
        follow_redirects=True,
    )
    assert b"nao pode ser editado ou reativado" in response.data
    db.session.refresh(pedido)
    assert pedido.status == PedidoCompra.STATUS_CANCELADO

    response = client.post(
        f"/pedido-compra/{pedido.id}/recebimento",
        data={"item_quantidade_receber[]": ["1", "0"]},
        follow_redirects=True,
    )
    assert b"Pedido cancelado nao pode receber itens" in response.data


def test_visibilidade_botoes_por_permissao_e_status(app_ctx):
    from app.extensoes import db
    from app.pedido_compra.pedido_compra_model import PedidoCompra

    usuario = _seed_user(db, "usuario", "usuario_visibilidade")
    readonly = _seed_user(db, "readonly", "readonly_visibilidade")
    operador = _seed_user(db, "operador", "operador_visibilidade")
    fornecedor, produto, servico, ordem, pedido_venda = _seed_base_compra(db)

    client = app_ctx.test_client()
    _autenticar(client, usuario)
    _criar_pedido_compra(client, fornecedor, produto, servico, ordem, pedido_venda)
    pedido = PedidoCompra.query.first()

    page = client.get("/pedido-compra/")
    assert b"Novo pedido de compra" in page.data

    details = client.get(f"/pedido-compra/{pedido.id}")
    assert b"Editar" in details.data
    assert b"Recebimento" in details.data
    assert b"Cancelar pedido" in details.data

    client.get("/auth/logout", follow_redirects=False)
    _autenticar(client, readonly)
    page = client.get("/pedido-compra/")
    assert b"Novo pedido de compra" not in page.data

    details = client.get(f"/pedido-compra/{pedido.id}")
    assert b"Editar" not in details.data
    assert b"Recebimento" not in details.data
    assert b"Cancelar pedido" not in details.data

    client.get("/auth/logout", follow_redirects=False)
    _autenticar(client, operador)
    details = client.get(f"/pedido-compra/{pedido.id}")
    assert b"Editar" in details.data
    assert b"Recebimento" in details.data
    assert b"Cancelar pedido" not in details.data


def test_render_templates_pedido_compra_exibem_moeda_brl(app_ctx):
    from app.extensoes import db
    from app.pedido_compra.pedido_compra_model import PedidoCompra

    usuario = _seed_user(db, "usuario", "usuario_moeda_brl")
    fornecedor, produto, _servico, ordem, pedido_venda = _seed_base_compra(db)

    client = app_ctx.test_client()
    _autenticar(client, usuario)

    payload = _post_data(
        fornecedor,
        produto,
        _servico,
        ordem,
        pedido_venda,
        desconto="0,00",
        **{
            "item_tipo[]": ["PRODUTO"],
            "item_referencia_id[]": [f"P:{produto.id}"],
            "item_descricao[]": ["Produto Compra"],
            "item_unidade[]": ["UN"],
            "item_quantidade[]": ["1"],
            "item_valor_unitario[]": ["2600,00"],
            "item_desconto[]": ["0"],
            "item_id[]": [""],
        },
    )
    response = client.post("/pedido-compra/novo", data=payload, follow_redirects=True)
    assert response.status_code == 200

    pedido = PedidoCompra.query.first()
    assert pedido is not None

    esperado = "R$ 2.600,00".encode("utf-8")

    page_listar = client.get("/pedido-compra/")
    assert esperado in page_listar.data
    assert b"R$ 2600.00" not in page_listar.data

    page_visualizar = client.get(f"/pedido-compra/{pedido.id}")
    assert esperado in page_visualizar.data
    assert b"R$ 2600.00" not in page_visualizar.data
    assert b"R$ 2,600.00" not in page_visualizar.data

    page_imprimir = client.get(f"/pedido-compra/{pedido.id}/imprimir")
    assert esperado in page_imprimir.data
    assert b"R$ 2600.00" not in page_imprimir.data
    assert b"R$ 2,600.00" not in page_imprimir.data


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
