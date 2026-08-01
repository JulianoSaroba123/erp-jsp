# -*- coding: utf-8 -*-
"""Testes da fundacao do modulo Pedidos."""

from __future__ import annotations

from datetime import date
from decimal import Decimal
import os
import sys
from pathlib import Path
from unittest.mock import patch

import pytest
import sqlalchemy as sa
from sqlalchemy.exc import IntegrityError

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


@pytest.fixture()
def app_ctx():
    from app import create_app
    from app.extensoes import db

    app = create_app("testing")

    with app.app_context():
        # Garante que os models de pedido entrem no metadata antes do create_all.
        from app.pedido.pedido_model import Pedido, PedidoItem  # noqa: F401

        db.drop_all()
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


def _criar_cliente(db):
    from app.cliente.cliente_model import Cliente

    cliente = Cliente(nome="Cliente Pedido", tipo="PF", cpf_cnpj="12345678901")
    db.session.add(cliente)
    db.session.commit()
    return cliente


def _criar_proposta(db, cliente_id):
    from app.proposta.proposta_model import Proposta

    proposta = Proposta(
        cliente_id=cliente_id,
        titulo="Proposta Base",
        status="aprovada",
        valor_total=Decimal("250.00"),
    )
    db.session.add(proposta)
    db.session.commit()
    return proposta


def _criar_produto(db):
    from app.produto.produto_model import Produto

    produto = Produto(nome="Produto Snapshot", preco_venda=Decimal("99.90"))
    db.session.add(produto)
    db.session.commit()
    return produto


def _criar_servico(db):
    from app.servico.servico_model import Servico

    servico = Servico(nome="Servico Snapshot", valor_base=Decimal("150.00"), tipo_cobranca="servico")
    db.session.add(servico)
    db.session.commit()
    return servico


def test_geracao_sequencial_numero_pedido_ped0001(app_ctx):
    from app.extensoes import db
    from app.pedido.pedido_model import Pedido

    cliente = _criar_cliente(db)

    pedido = Pedido(cliente_id=cliente.id)
    db.session.add(pedido)
    db.session.commit()

    assert pedido.numero == "PED0001"


def test_unicidade_numero_pedido(app_ctx):
    from app.extensoes import db
    from app.pedido.pedido_model import Pedido

    cliente = _criar_cliente(db)

    db.session.add(Pedido(cliente_id=cliente.id, numero="PED0001"))
    db.session.commit()

    db.session.add(Pedido(cliente_id=cliente.id, numero="PED0001"))
    with pytest.raises(IntegrityError):
        db.session.commit()
    db.session.rollback()


def test_criacao_pedido_com_cliente(app_ctx):
    from app.extensoes import db
    from app.pedido.pedido_model import Pedido

    cliente = _criar_cliente(db)
    pedido = Pedido(cliente_id=cliente.id, responsavel="Comercial")
    db.session.add(pedido)
    db.session.commit()

    assert pedido.id is not None
    assert pedido.cliente_id == cliente.id


def test_criacao_pedido_com_proposta_opcional(app_ctx):
    from app.extensoes import db
    from app.pedido.pedido_model import Pedido

    cliente = _criar_cliente(db)
    proposta = _criar_proposta(db, cliente.id)

    pedido = Pedido(cliente_id=cliente.id, proposta_id=proposta.id)
    db.session.add(pedido)
    db.session.commit()

    assert pedido.proposta_id == proposta.id


def test_impede_dois_pedidos_para_mesma_proposta(app_ctx):
    from app.extensoes import db
    from app.pedido.pedido_model import Pedido

    cliente = _criar_cliente(db)
    proposta = _criar_proposta(db, cliente.id)

    db.session.add(Pedido(cliente_id=cliente.id, proposta_id=proposta.id))
    db.session.commit()

    db.session.add(Pedido(cliente_id=cliente.id, proposta_id=proposta.id))
    with pytest.raises(IntegrityError):
        db.session.commit()
    db.session.rollback()


def test_item_produto_valido(app_ctx):
    from app.extensoes import db
    from app.pedido.pedido_model import Pedido, PedidoItem

    cliente = _criar_cliente(db)
    produto = _criar_produto(db)

    pedido = Pedido(cliente_id=cliente.id)
    db.session.add(pedido)
    db.session.flush()

    item = PedidoItem(
        pedido_id=pedido.id,
        tipo_item=PedidoItem.TIPO_PRODUTO,
        produto_id=produto.id,
        descricao="Produto Snapshot",
        quantidade=Decimal("2.000"),
        valor_unitario=Decimal("10.00"),
        desconto=Decimal("0.00"),
        ordem=1,
    )
    db.session.add(item)
    db.session.commit()

    assert item.id is not None
    assert item.servico_id is None


def test_item_servico_valido(app_ctx):
    from app.extensoes import db
    from app.pedido.pedido_model import Pedido, PedidoItem

    cliente = _criar_cliente(db)
    servico = _criar_servico(db)

    pedido = Pedido(cliente_id=cliente.id)
    db.session.add(pedido)
    db.session.flush()

    item = PedidoItem(
        pedido_id=pedido.id,
        tipo_item=PedidoItem.TIPO_SERVICO,
        servico_id=servico.id,
        descricao="Servico Snapshot",
        quantidade=Decimal("1.000"),
        valor_unitario=Decimal("150.00"),
        desconto=Decimal("0.00"),
        ordem=1,
    )
    db.session.add(item)
    db.session.commit()

    assert item.id is not None
    assert item.produto_id is None


def test_rejeita_item_com_produto_e_servico_simultaneamente(app_ctx):
    from app.extensoes import db
    from app.pedido.pedido_model import Pedido, PedidoItem

    cliente = _criar_cliente(db)
    produto = _criar_produto(db)
    servico = _criar_servico(db)

    pedido = Pedido(cliente_id=cliente.id)
    db.session.add(pedido)
    db.session.flush()

    item = PedidoItem(
        pedido_id=pedido.id,
        tipo_item=PedidoItem.TIPO_PRODUTO,
        produto_id=produto.id,
        servico_id=servico.id,
        descricao="Invalido",
        quantidade=Decimal("1.000"),
        valor_unitario=Decimal("10.00"),
        desconto=Decimal("0.00"),
    )
    db.session.add(item)

    with pytest.raises(ValueError):
        db.session.commit()
    db.session.rollback()


def test_rejeita_item_sem_produto_nem_servico(app_ctx):
    from app.extensoes import db
    from app.pedido.pedido_model import Pedido, PedidoItem

    cliente = _criar_cliente(db)
    pedido = Pedido(cliente_id=cliente.id)
    db.session.add(pedido)
    db.session.flush()

    item = PedidoItem(
        pedido_id=pedido.id,
        tipo_item=PedidoItem.TIPO_PRODUTO,
        descricao="Invalido",
        quantidade=Decimal("1.000"),
        valor_unitario=Decimal("10.00"),
        desconto=Decimal("0.00"),
    )
    db.session.add(item)

    with pytest.raises(ValueError):
        db.session.commit()
    db.session.rollback()


def test_calculo_monetario_sem_float(app_ctx):
    from app.extensoes import db
    from app.pedido.pedido_model import Pedido, PedidoItem

    cliente = _criar_cliente(db)
    produto = _criar_produto(db)

    pedido = Pedido(cliente_id=cliente.id)
    db.session.add(pedido)
    db.session.flush()

    item = PedidoItem(
        pedido_id=pedido.id,
        tipo_item=PedidoItem.TIPO_PRODUTO,
        produto_id=produto.id,
        descricao="Produto Monetario",
        quantidade=Decimal("2.500"),
        valor_unitario=Decimal("10.40"),
        desconto=Decimal("1.00"),
        ordem=1,
    )
    db.session.add(item)
    db.session.commit()

    assert isinstance(item.valor_total, Decimal)
    assert item.valor_total == Decimal("25.00")


def test_preserva_snapshot_descricao_e_valor(app_ctx):
    from app.extensoes import db
    from app.pedido.pedido_model import Pedido, PedidoItem
    from app.produto.produto_model import Produto

    cliente = _criar_cliente(db)
    produto = _criar_produto(db)

    pedido = Pedido(cliente_id=cliente.id)
    db.session.add(pedido)
    db.session.flush()

    item = PedidoItem(
        pedido_id=pedido.id,
        tipo_item=PedidoItem.TIPO_PRODUTO,
        produto_id=produto.id,
        descricao=produto.nome,
        quantidade=Decimal("1.000"),
        valor_unitario=produto.preco_venda,
        desconto=Decimal("0.00"),
        ordem=1,
    )
    db.session.add(item)
    db.session.commit()

    descricao_snapshot = item.descricao
    valor_snapshot = item.valor_unitario

    produto.nome = "Produto Alterado"
    produto.preco_venda = Decimal("999.99")
    db.session.commit()
    db.session.refresh(item)

    assert item.descricao == descricao_snapshot
    assert item.valor_unitario == valor_snapshot


def test_ausencia_geracao_financeira_e_ausencia_alteracao_os(app_ctx):
    from app.extensoes import db
    from app.financeiro.financeiro_model import LancamentoFinanceiro
    from app.ordem_servico.ordem_servico_model import OrdemServico
    from app.pedido.pedido_model import Pedido

    cliente = _criar_cliente(db)

    total_financeiro_antes = LancamentoFinanceiro.query.count()
    total_os_antes = OrdemServico.query.count()

    pedido = Pedido(
        cliente_id=cliente.id,
        data_pedido=date.today(),
        status=Pedido.STATUS_RASCUNHO,
    )
    db.session.add(pedido)
    db.session.commit()

    assert LancamentoFinanceiro.query.count() == total_financeiro_antes
    assert OrdemServico.query.count() == total_os_antes


def test_pedido_e_pedido_item_herdam_basemodel(app_ctx):
    from app.models import BaseModel
    from app.pedido.pedido_model import Pedido, PedidoItem

    assert issubclass(Pedido, BaseModel)
    assert issubclass(PedidoItem, BaseModel)

    for campo in ("id", "criado_em", "atualizado_em", "ativo"):
        assert campo in Pedido.__table__.c
        assert campo in PedidoItem.__table__.c

    assert "created_at" not in Pedido.__table__.c
    assert "updated_at" not in Pedido.__table__.c
    assert "created_at" not in PedidoItem.__table__.c
    assert "updated_at" not in PedidoItem.__table__.c


def test_rejeita_quantidade_zero_ou_negativa(app_ctx):
    from app.extensoes import db
    from app.pedido.pedido_model import Pedido, PedidoItem

    cliente = _criar_cliente(db)
    produto = _criar_produto(db)

    pedido = Pedido(cliente_id=cliente.id)
    db.session.add(pedido)
    db.session.flush()

    item_zero = PedidoItem(
        pedido_id=pedido.id,
        tipo_item=PedidoItem.TIPO_PRODUTO,
        produto_id=produto.id,
        descricao="Quantidade Zero",
        quantidade=Decimal("0.000"),
        valor_unitario=Decimal("10.00"),
        desconto=Decimal("0.00"),
    )
    db.session.add(item_zero)
    with pytest.raises(ValueError, match="quantidade do item deve ser maior que zero"):
        db.session.commit()
    db.session.rollback()

    item_negativo = PedidoItem(
        pedido_id=pedido.id,
        tipo_item=PedidoItem.TIPO_PRODUTO,
        produto_id=produto.id,
        descricao="Quantidade Negativa",
        quantidade=Decimal("-1.000"),
        valor_unitario=Decimal("10.00"),
        desconto=Decimal("0.00"),
    )
    db.session.add(item_negativo)
    with pytest.raises(ValueError, match="quantidade do item deve ser maior que zero"):
        db.session.commit()
    db.session.rollback()


def test_rejeita_valores_monetarios_negativos_no_item(app_ctx):
    from app.extensoes import db
    from app.pedido.pedido_model import Pedido, PedidoItem

    cliente = _criar_cliente(db)
    produto = _criar_produto(db)

    pedido = Pedido(cliente_id=cliente.id)
    db.session.add(pedido)
    db.session.flush()

    item_valor_unitario_negativo = PedidoItem(
        pedido_id=pedido.id,
        tipo_item=PedidoItem.TIPO_PRODUTO,
        produto_id=produto.id,
        descricao="Valor Unitario Negativo",
        quantidade=Decimal("1.000"),
        valor_unitario=Decimal("-0.01"),
        desconto=Decimal("0.00"),
    )
    db.session.add(item_valor_unitario_negativo)
    with pytest.raises(ValueError, match="valor_unitario do item nao pode ser negativo"):
        db.session.commit()
    db.session.rollback()

    item_desconto_negativo = PedidoItem(
        pedido_id=pedido.id,
        tipo_item=PedidoItem.TIPO_PRODUTO,
        produto_id=produto.id,
        descricao="Desconto Negativo",
        quantidade=Decimal("1.000"),
        valor_unitario=Decimal("10.00"),
        desconto=Decimal("-0.01"),
    )
    db.session.add(item_desconto_negativo)
    with pytest.raises(ValueError, match="desconto do item nao pode ser negativo"):
        db.session.commit()
    db.session.rollback()


def test_rejeita_desconto_que_torna_total_item_negativo(app_ctx):
    from app.extensoes import db
    from app.pedido.pedido_model import Pedido, PedidoItem

    cliente = _criar_cliente(db)
    produto = _criar_produto(db)

    pedido = Pedido(cliente_id=cliente.id)
    db.session.add(pedido)
    db.session.flush()

    item = PedidoItem(
        pedido_id=pedido.id,
        tipo_item=PedidoItem.TIPO_PRODUTO,
        produto_id=produto.id,
        descricao="Total Negativo",
        quantidade=Decimal("1.000"),
        valor_unitario=Decimal("10.00"),
        desconto=Decimal("10.01"),
    )
    db.session.add(item)

    with pytest.raises(ValueError, match="valor_total do item nao pode ser negativo"):
        db.session.commit()
    db.session.rollback()


def test_rejeita_totais_negativos_no_pedido(app_ctx):
    from app.extensoes import db
    from app.pedido.pedido_model import Pedido

    cliente = _criar_cliente(db)

    pedido_subtotal_negativo = Pedido(
        cliente_id=cliente.id,
        subtotal=Decimal("-0.01"),
        desconto=Decimal("0.00"),
        valor_total=Decimal("0.00"),
    )
    db.session.add(pedido_subtotal_negativo)
    with pytest.raises(ValueError, match="subtotal do pedido nao pode ser negativo"):
        db.session.commit()
    db.session.rollback()

    pedido_desconto_negativo = Pedido(
        cliente_id=cliente.id,
        subtotal=Decimal("0.00"),
        desconto=Decimal("-0.01"),
        valor_total=Decimal("0.00"),
    )
    db.session.add(pedido_desconto_negativo)
    with pytest.raises(ValueError, match="desconto do pedido nao pode ser negativo"):
        db.session.commit()
    db.session.rollback()

    pedido_total_negativo = Pedido(
        cliente_id=cliente.id,
        subtotal=Decimal("1.00"),
        desconto=Decimal("0.00"),
        valor_total=Decimal("-0.01"),
    )
    db.session.add(pedido_total_negativo)
    with pytest.raises(ValueError, match="valor_total do pedido nao pode ser negativo"):
        db.session.commit()
    db.session.rollback()


def test_metadata_contem_constraints_exigidas(app_ctx):
    from app.pedido.pedido_model import Pedido, PedidoItem

    nomes_pedido = {
        constraint.name
        for constraint in Pedido.__table__.constraints
        if constraint.name
    }
    nomes_item = {
        constraint.name
        for constraint in PedidoItem.__table__.constraints
        if constraint.name
    }

    assert {
        "ck_pedidos_status",
        "ck_pedidos_subtotal_nao_negativo",
        "ck_pedidos_desconto_nao_negativo",
        "ck_pedidos_valor_total_nao_negativo",
    }.issubset(nomes_pedido)

    assert {
        "ck_pedido_itens_tipo_item",
        "ck_pedido_itens_referencia_exclusiva",
        "ck_pedido_itens_quantidade_positiva",
        "ck_pedido_itens_valor_unitario_nao_negativo",
        "ck_pedido_itens_desconto_nao_negativo",
        "ck_pedido_itens_valor_total_nao_negativo",
    }.issubset(nomes_item)


def test_equivalencia_estrutural_constraints_model_e_migration(app_ctx):
    from app.pedido.pedido_model import Pedido, PedidoItem

    def _coluna_signature(column):
        foreign_keys = []
        for fk in column.foreign_keys:
            target = getattr(fk, "target_fullname", None) or getattr(fk, "_colspec", None)
            foreign_keys.append((target, fk.ondelete))
        return {
            "name": column.name,
            "type": type(column.type).__name__,
            "nullable": column.nullable,
            "primary_key": column.primary_key,
            "foreign_keys": sorted(foreign_keys),
            "precision": getattr(column.type, "precision", None),
            "scale": getattr(column.type, "scale", None),
        }

    def _default_signature(column):
        python_default = None
        if column.default is not None and getattr(column.default, "arg", None) is not None:
            python_default = repr(column.default.arg)
        server_default = None if column.server_default is None else str(column.server_default.arg)
        return python_default, server_default

    def _constraint_signature(constraint):
        if isinstance(constraint, sa.ForeignKeyConstraint):
            return (
                type(constraint).__name__,
                None,
                tuple((getattr(elem, "target_fullname", None) or getattr(elem, "_colspec", None), elem.ondelete) for elem in constraint.elements),
            )
        if isinstance(constraint, sa.CheckConstraint):
            return (type(constraint).__name__, constraint.name, str(constraint.sqltext))
        if isinstance(constraint, sa.PrimaryKeyConstraint):
            return (type(constraint).__name__, constraint.name, tuple(constraint.columns.keys()))
        return (type(constraint).__name__, constraint.name, tuple(getattr(constraint, "columns", {}).keys()))

    def _unique_columns(table):
        unique_columns = {column.name for column in table.columns if bool(getattr(column, "unique", False))}
        for constraint in table.constraints:
            if isinstance(constraint, sa.UniqueConstraint):
                unique_columns.update(constraint.columns.keys())
        for index in table.indexes:
            if index.unique:
                unique_columns.update(index.columns.keys())
        return sorted(unique_columns)

    def _index_signature(index):
        return (index.name, tuple(index.columns.keys()), index.unique)

    def _table_signature(table):
        return {
            "columns": {column.name: _coluna_signature(column) for column in table.columns},
            "constraints": sorted(_constraint_signature(constraint) for constraint in table.constraints if not isinstance(constraint, sa.UniqueConstraint)),
            "unique_columns": _unique_columns(table),
            "defaults": {column.name: _default_signature(column) for column in table.columns},
        }

    def _capturar_upgrade():
        import importlib.util

        module_path = (
            Path(__file__).resolve().parents[2]
            / "migrations"
            / "versions"
            / "20260801_02_create_pedidos_foundation.py"
        )
        spec = importlib.util.spec_from_file_location("pedido_migration", module_path)
        module = importlib.util.module_from_spec(spec)
        assert spec.loader is not None

        captured_tables = {}
        captured_indexes = []

        def fake_create_table(name, *elements, **kwargs):
            captured_tables[name] = sa.Table(name, sa.MetaData(), *elements, **kwargs)

        def fake_create_index(name, table_name, columns, unique=False, **kwargs):
            captured_indexes.append((name, table_name, tuple(columns), unique, kwargs))

        with patch("alembic.op.create_table", side_effect=fake_create_table), patch("alembic.op.create_index", side_effect=fake_create_index):
            spec.loader.exec_module(module)
            module.upgrade()

        return captured_tables, captured_indexes

    pedido_signature = _table_signature(Pedido.__table__)
    item_signature = _table_signature(PedidoItem.__table__)
    captured_tables, captured_indexes = _capturar_upgrade()

    assert set(captured_tables) == {"pedidos", "pedido_itens"}
    captured_pedido_signature = _table_signature(captured_tables["pedidos"])
    captured_item_signature = _table_signature(captured_tables["pedido_itens"])

    assert captured_pedido_signature["columns"] == pedido_signature["columns"]
    assert captured_pedido_signature["constraints"] == pedido_signature["constraints"]
    assert captured_pedido_signature["unique_columns"] == pedido_signature["unique_columns"]

    assert captured_item_signature["columns"] == item_signature["columns"]
    assert captured_item_signature["constraints"] == item_signature["constraints"]
    assert captured_item_signature["unique_columns"] == item_signature["unique_columns"]

    assert sorted(captured_indexes) == [
        ("ix_pedido_itens_pedido_id", "pedido_itens", ("pedido_id",), False, {}),
        ("ix_pedido_itens_tipo_item", "pedido_itens", ("tipo_item",), False, {}),
        ("ix_pedidos_cliente_id", "pedidos", ("cliente_id",), False, {}),
        ("ix_pedidos_numero", "pedidos", ("numero",), True, {}),
        ("ix_pedidos_proposta_id", "pedidos", ("proposta_id",), True, {}),
        ("ix_pedidos_status", "pedidos", ("status",), False, {}),
    ]

    assert sorted(_index_signature(index) for index in Pedido.__table__.indexes) == [
        ("ix_pedidos_cliente_id", ("cliente_id",), False),
        ("ix_pedidos_numero", ("numero",), True),
        ("ix_pedidos_proposta_id", ("proposta_id",), True),
        ("ix_pedidos_status", ("status",), False),
    ]
    assert sorted(_index_signature(index) for index in PedidoItem.__table__.indexes) == [
        ("ix_pedido_itens_pedido_id", ("pedido_id",), False),
        ("ix_pedido_itens_tipo_item", ("tipo_item",), False),
    ]

    assert pedido_signature["unique_columns"] == ["numero", "proposta_id"]
    assert item_signature["unique_columns"] == []

    assert pedido_signature["defaults"]["criado_em"][0] is not None
    assert pedido_signature["defaults"]["criado_em"][1] is None
    assert pedido_signature["defaults"]["atualizado_em"][0] is not None
    assert pedido_signature["defaults"]["atualizado_em"][1] is None
    assert pedido_signature["defaults"]["ativo"][0] == "True"
    assert pedido_signature["defaults"]["ativo"][1] == "true"

    assert item_signature["defaults"]["criado_em"][0] is not None
    assert item_signature["defaults"]["criado_em"][1] is None
    assert item_signature["defaults"]["atualizado_em"][0] is not None
    assert item_signature["defaults"]["atualizado_em"][1] is None
    assert item_signature["defaults"]["ativo"][0] == "True"
    assert item_signature["defaults"]["ativo"][1] == "true"

    assert captured_pedido_signature["defaults"]["criado_em"][1] == "CURRENT_TIMESTAMP"
    assert captured_pedido_signature["defaults"]["atualizado_em"][1] == "CURRENT_TIMESTAMP"
    assert captured_pedido_signature["defaults"]["ativo"][1] == "true"

    assert captured_item_signature["defaults"]["criado_em"][1] == "CURRENT_TIMESTAMP"
    assert captured_item_signature["defaults"]["atualizado_em"][1] == "CURRENT_TIMESTAMP"
    assert captured_item_signature["defaults"]["ativo"][1] == "true"

    expected_pedido_columns = {
        "numero",
        "cliente_id",
        "proposta_id",
        "data_pedido",
        "status",
        "responsavel",
        "solicitante",
        "telefone_contato",
        "email_contato",
        "prazo_previsto",
        "condicoes_pagamento",
        "subtotal",
        "desconto",
        "valor_total",
        "observacoes",
        "id",
        "criado_em",
        "atualizado_em",
        "ativo",
    }
    expected_item_columns = {
        "pedido_id",
        "tipo_item",
        "produto_id",
        "servico_id",
        "descricao",
        "quantidade",
        "valor_unitario",
        "desconto",
        "valor_total",
        "ordem",
        "id",
        "criado_em",
        "atualizado_em",
        "ativo",
    }

    assert set(pedido_signature["columns"]) == expected_pedido_columns
    assert set(item_signature["columns"]) == expected_item_columns

    pedido_columns = pedido_signature["columns"]
    item_columns = item_signature["columns"]

    assert pedido_columns["id"]["primary_key"] is True
    assert pedido_columns["criado_em"]["nullable"] is False
    assert pedido_columns["atualizado_em"]["nullable"] is False
    assert pedido_columns["ativo"]["nullable"] is False

    assert pedido_columns["subtotal"]["precision"] == 12
    assert pedido_columns["subtotal"]["scale"] == 2
    assert pedido_columns["desconto"]["precision"] == 12
    assert pedido_columns["desconto"]["scale"] == 2
    assert pedido_columns["valor_total"]["precision"] == 12
    assert pedido_columns["valor_total"]["scale"] == 2

    assert item_columns["quantidade"]["precision"] == 12
    assert item_columns["quantidade"]["scale"] == 3
    assert item_columns["valor_unitario"]["precision"] == 12
    assert item_columns["valor_unitario"]["scale"] == 2
    assert item_columns["desconto"]["precision"] == 12
    assert item_columns["desconto"]["scale"] == 2
    assert item_columns["valor_total"]["precision"] == 12
    assert item_columns["valor_total"]["scale"] == 2

    migration_path = (
        Path(__file__).resolve().parents[2]
        / "migrations"
        / "versions"
        / "20260801_02_create_pedidos_foundation.py"
    )
    migration_source = migration_path.read_text(encoding="utf-8")

    nomes_pedido_model = {constraint.name for constraint in Pedido.__table__.constraints if constraint.name and constraint.name.startswith("ck_pedidos_")}
    nomes_item_model = {constraint.name for constraint in PedidoItem.__table__.constraints if constraint.name and constraint.name.startswith("ck_pedido_itens_")}

    esperados_pedido = {
        "ck_pedidos_status",
        "ck_pedidos_subtotal_nao_negativo",
        "ck_pedidos_desconto_nao_negativo",
        "ck_pedidos_valor_total_nao_negativo",
    }
    esperados_item = {
        "ck_pedido_itens_tipo_item",
        "ck_pedido_itens_referencia_exclusiva",
        "ck_pedido_itens_quantidade_positiva",
        "ck_pedido_itens_valor_unitario_nao_negativo",
        "ck_pedido_itens_desconto_nao_negativo",
        "ck_pedido_itens_valor_total_nao_negativo",
    }

    assert nomes_pedido_model == esperados_pedido
    assert nomes_item_model == esperados_item

    for nome in sorted(esperados_pedido | esperados_item):
        assert f'name="{nome}"' in migration_source
