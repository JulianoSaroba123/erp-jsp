# -*- coding: utf-8 -*-
"""D26F03-A3 - Validacao da migration de estoque."""

from decimal import Decimal
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

from alembic.migration import MigrationContext
from alembic.operations import Operations
from sqlalchemy import (
    Column,
    Integer,
    MetaData,
    String,
    Table,
    create_engine,
    inspect,
    text,
)
from sqlalchemy.pool import StaticPool


ROOT = Path(__file__).resolve().parents[2]

MIGRATION = (
    ROOT
    / "migrations"
    / "versions"
    / "20260921_01_pedido_estoque_fundacao.py"
)


def _carregar_migration():
    spec = spec_from_file_location(
        "migration_d26f03",
        MIGRATION,
    )

    module = module_from_spec(spec)
    spec.loader.exec_module(module)

    return module


def _engine():
    return create_engine(
        "sqlite://",
        connect_args={
            "check_same_thread": False,
        },
        poolclass=StaticPool,
    )


def _schema_anterior(engine):
    metadata = MetaData()

    Table(
        "produtos",
        metadata,
        Column(
            "id",
            Integer,
            primary_key=True,
        ),
        Column(
            "nome",
            String(100),
            nullable=False,
        ),
        Column(
            "estoque_atual",
            Integer,
            nullable=True,
        ),
        Column(
            "estoque_minimo",
            Integer,
            nullable=True,
        ),
        Column(
            "estoque_maximo",
            Integer,
            nullable=True,
        ),
    )

    Table(
        "pedidos",
        metadata,
        Column(
            "id",
            Integer,
            primary_key=True,
        ),
        Column(
            "numero",
            String(20),
            nullable=False,
        ),
    )

    metadata.create_all(engine)

    with engine.begin() as conn:
        conn.execute(
            text(
                """
                INSERT INTO produtos (
                    id,
                    nome,
                    estoque_atual,
                    estoque_minimo,
                    estoque_maximo
                )
                VALUES (
                    1,
                    'Produto migration',
                    10,
                    2,
                    50
                )
                """
            )
        )

        conn.execute(
            text(
                """
                INSERT INTO pedidos (
                    id,
                    numero
                )
                VALUES (
                    1,
                    'PED0001'
                )
                """
            )
        )


def _operations(conn):
    context = MigrationContext.configure(
        conn
    )

    return Operations(
        context
    )


def test_revision_encadeada_corretamente():
    module = _carregar_migration()

    assert module.revision == "20260921_01"
    assert module.down_revision == "20260919_03"


def test_upgrade_sqlite_preserva_saldo_e_cria_movimentacoes():
    engine = _engine()

    _schema_anterior(engine)

    module = _carregar_migration()

    with engine.begin() as conn:
        module.op = _operations(conn)
        module.upgrade()

    inspector = inspect(engine)

    assert (
        "movimentacoes_estoque"
        in inspector.get_table_names()
    )

    colunas_produto = {
        coluna["name"]: coluna
        for coluna
        in inspector.get_columns(
            "produtos"
        )
    }

    for campo in (
        "estoque_atual",
        "estoque_minimo",
        "estoque_maximo",
    ):
        tipo = colunas_produto[
            campo
        ]["type"]

        assert getattr(
            tipo,
            "precision",
            None,
        ) == 12

        assert getattr(
            tipo,
            "scale",
            None,
        ) == 3

    with engine.connect() as conn:
        row = conn.execute(
            text(
                """
                SELECT
                    estoque_atual,
                    estoque_minimo,
                    estoque_maximo
                FROM produtos
                WHERE id = 1
                """
            )
        ).one()

        assert Decimal(
            str(row.estoque_atual)
        ) == Decimal("10")

        assert Decimal(
            str(row.estoque_minimo)
        ) == Decimal("2")

        assert Decimal(
            str(row.estoque_maximo)
        ) == Decimal("50")


def test_migration_cria_indices_e_constraint_idempotencia():
    engine = _engine()

    _schema_anterior(engine)

    module = _carregar_migration()

    with engine.begin() as conn:
        module.op = _operations(conn)
        module.upgrade()

    inspector = inspect(engine)

    indices = {
        indice["name"]
        for indice
        in inspector.get_indexes(
            "movimentacoes_estoque"
        )
    }

    assert (
        "ix_movimentacoes_estoque_produto_id"
        in indices
    )

    assert (
        "ix_movimentacoes_estoque_pedido_id"
        in indices
    )

    uniques = inspector.get_unique_constraints(
        "movimentacoes_estoque"
    )

    nomes_unique = {
        constraint["name"]
        for constraint
        in uniques
    }

    assert (
        "uq_mov_estoque_pedido_produto_tipo_origem"
        in nomes_unique
    )
