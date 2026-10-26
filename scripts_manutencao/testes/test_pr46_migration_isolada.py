# -*- coding: utf-8 -*-
"""Smoke aditivo de migration PR46 apenas em SQLite descartável na memória."""
import importlib.util
from pathlib import Path

import pytest
import sqlalchemy as sa
from alembic.migration import MigrationContext
from alembic.operations import Operations


MIGRACAO = (
    Path(__file__).resolve().parents[2]
    / "migrations/versions/20261026_01_os_recebimento_saldo_externo.py"
)


def carregar_migracao():
    spec = importlib.util.spec_from_file_location("migration_pr46_isolada", MIGRACAO)
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


def test_migration_pr46_upgrade_downgrade_seguro():
    modulo = carregar_migracao()
    assert modulo.revision == "20261026_01"
    assert modulo.down_revision == "20261015_01"

    engine = sa.create_engine("sqlite+pysqlite:///:memory:")
    with engine.begin() as conn:
        conn.execute(sa.text(
            "CREATE TABLE lancamentos_financeiros (id INTEGER PRIMARY KEY)"
        ))
        conn.execute(sa.text(
            "INSERT INTO lancamentos_financeiros (id) VALUES (1)"
        ))
        with Operations.context(MigrationContext.configure(conn)):
            modulo.upgrade()

        colunas = {
            coluna["name"]: coluna
            for coluna in sa.inspect(conn).get_columns("lancamentos_financeiros")
        }
        assert "sem_movimentacao_bancaria" in colunas
        assert colunas["sem_movimentacao_bancaria"]["nullable"] is False
        assert conn.execute(sa.text(
            "SELECT sem_movimentacao_bancaria FROM lancamentos_financeiros "
            "WHERE id = 1"
        )).scalar_one() == 0

        conn.execute(sa.text(
            "UPDATE lancamentos_financeiros "
            "SET sem_movimentacao_bancaria = 1 WHERE id = 1"
        ))
        with Operations.context(MigrationContext.configure(conn)):
            with pytest.raises(RuntimeError, match="Downgrade bloqueado"):
                modulo.downgrade()

        conn.execute(sa.text(
            "UPDATE lancamentos_financeiros "
            "SET sem_movimentacao_bancaria = 0 WHERE id = 1"
        ))
        with Operations.context(MigrationContext.configure(conn)):
            modulo.downgrade()
        assert "sem_movimentacao_bancaria" not in {
            c["name"]
            for c in sa.inspect(conn).get_columns("lancamentos_financeiros")
        }
    engine.dispose()
