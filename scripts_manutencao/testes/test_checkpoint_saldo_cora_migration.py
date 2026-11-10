# -*- coding: utf-8 -*-
"""Migração do checkpoint Cora em PostgreSQL descartável e schema isolado."""
from datetime import date
from decimal import Decimal
from importlib.util import spec_from_file_location, module_from_spec
import os
from pathlib import Path
from uuid import uuid4

import pytest
import sqlalchemy as sa
from alembic.migration import MigrationContext
from alembic.operations import Operations
from unittest.mock import patch


@pytest.fixture
def banco():
    url = os.environ.get("PR46_POSTGRES_TEST_URL")
    if not url:
        pytest.skip("PostgreSQL de teste não configurado")
    u = sa.engine.make_url(url)
    assert u.get_backend_name() == "postgresql"
    assert u.host in ("localhost", "127.0.0.1", "::1")
    assert u.database == "erp_jsp_pr46_test"
    assert not os.environ.get("RENDER_SERVICE_ID")
    assert os.environ.get("RENDER", "").lower() not in ("true", "yes", "1")
    schema = "saldo_cora_" + uuid4().hex
    admin = sa.create_engine(url)
    with admin.begin() as c:
        c.execute(sa.text(f"CREATE SCHEMA {schema}"))
    eng = sa.create_engine(url, connect_args={"options": f"-csearch_path={schema}"})
    try:
        with eng.begin() as c:
            c.execute(sa.text(
                "CREATE TABLE contas_bancarias (id INTEGER PRIMARY KEY,"
                "nome TEXT,banco TEXT,ativo BOOLEAN,ativa BOOLEAN,"
                "saldo_atual NUMERIC(14,2),atualizado_em TIMESTAMP)"
            ))
            c.execute(sa.text(
                "CREATE TABLE extratos_bancarios (id INTEGER PRIMARY KEY,"
                "conta_bancaria_id INTEGER,ativo BOOLEAN,conciliado BOOLEAN,"
                "tipo_movimento TEXT,valor NUMERIC(14,2),data_movimento DATE)"
            ))
            c.execute(sa.text(
                "INSERT INTO contas_bancarias "
                "(id,nome,banco,ativo,ativa,saldo_atual) "
                "VALUES (1,'Cora SCFI','Cora SCFI',true,true,-24544.59)"
            ))
            credits = [Decimal("9550"), Decimal("3400"), Decimal("435"),
                       Decimal("434"), Decimal("130")]
            debits = [Decimal("100")] * 34 + [Decimal("5322.96")]
            rows = (
                [(i, "credito", amount) for i, amount in enumerate(credits, 1)] +
                [(i, "debito", amount) for i, amount in enumerate(debits, 6)]
            )
            assert len(rows) == 40
            for i, tipo, valor in rows:
                c.execute(sa.text(
                    "INSERT INTO extratos_bancarios "
                    "(id,conta_bancaria_id,ativo,conciliado,tipo_movimento,valor,data_movimento) "
                    "VALUES (:id,1,true,true,:tipo,:valor,:dia)"
                ), {"id": i, "tipo": tipo, "valor": valor,
                    "dia": date(2026, 11, 9)})
        path = (Path(__file__).resolve().parents[2] /
                "migrations/versions/20261109_01_checkpoint_saldo_cora.py")
        spec = spec_from_file_location("checkpoint_cora_teste", path)
        module = module_from_spec(spec)
        spec.loader.exec_module(module)
        yield eng, module
    finally:
        eng.dispose()
        with admin.begin() as c:
            c.execute(sa.text(f"DROP SCHEMA IF EXISTS {schema} CASCADE"))
        admin.dispose()


def _aplicar(conn, module):
    ops = Operations(MigrationContext.configure(conn))
    with patch.object(module, "op", ops):
        module.upgrade()


def test_checkpoint_saldo_ajusta_apenas_conta_e_guarda_proveniencia(banco):
    eng, module = banco
    with eng.begin() as c:
        _aplicar(c, module)
    with eng.connect() as c:
        assert Decimal(str(c.execute(sa.text(
            "SELECT saldo_atual FROM contas_bancarias WHERE id=1"
        )).scalar_one())) == Decimal("8508.77")
        ref = c.execute(sa.text(
            "SELECT saldo_referencia,saldo_interno_anterior,saldo_interno_reparado,"
            "fonte,motivo FROM saldo_bancario_referencias"
        )).mappings().one()
        assert Decimal(str(ref["saldo_referencia"])) == Decimal("3282.73")
        assert Decimal(str(ref["saldo_interno_anterior"])) == Decimal("-24544.59")
        assert Decimal(str(ref["saldo_interno_reparado"])) == Decimal("8508.77")
        assert "Cora" in ref["fonte"]
        assert "histórico financeiro" in ref["motivo"]
        assert c.execute(sa.text(
            "SELECT count(*) FROM extratos_bancarios"
        )).scalar_one() == 40


@pytest.mark.parametrize("alteracao", [
    "UPDATE contas_bancarias SET saldo_atual=-24544.58 WHERE id=1",
    "UPDATE extratos_bancarios SET conciliado=false WHERE id=1",
    "INSERT INTO extratos_bancarios "
    "(id,conta_bancaria_id,ativo,conciliado,tipo_movimento,valor,data_movimento) "
    "VALUES (41,1,true,false,'debito',1,'2026-11-10')",
])
def test_mudanca_no_saldo_ou_extrato_aborta_sem_efeitos(banco, alteracao):
    eng, module = banco
    with eng.begin() as c:
        c.execute(sa.text(alteracao))
    with pytest.raises(RuntimeError, match="regularização bloqueada"):
        with eng.begin() as c:
            _aplicar(c, module)
    with eng.connect() as c:
        assert not sa.inspect(c).has_table("saldo_bancario_referencias")
