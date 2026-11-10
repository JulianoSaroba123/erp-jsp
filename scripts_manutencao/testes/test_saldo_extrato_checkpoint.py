# -*- coding: utf-8 -*-
"""Regras do saldo por extrato, sem acesso à produção."""
from datetime import date
from decimal import Decimal

import pytest
import sqlalchemy as sa

from app.financeiro.saldo_extrato_service import obter_saldo_extrato


@pytest.fixture
def engine():
    engine = sa.create_engine("sqlite+pysqlite:///:memory:")
    with engine.begin() as c:
        c.execute(sa.text(
            "CREATE TABLE contas_bancarias (id INTEGER PRIMARY KEY,"
            "nome TEXT NOT NULL, ativo BOOLEAN NOT NULL, ativa BOOLEAN NOT NULL,"
            "saldo_atual NUMERIC NOT NULL)"
        ))
        c.execute(sa.text(
            "CREATE TABLE saldo_bancario_referencias (id INTEGER PRIMARY KEY,"
            "conta_bancaria_id INTEGER NOT NULL, data_referencia DATE NOT NULL,"
            "saldo_referencia NUMERIC NOT NULL, fonte TEXT NOT NULL)"
        ))
        c.execute(sa.text(
            "CREATE TABLE extratos_bancarios (id INTEGER PRIMARY KEY,"
            "conta_bancaria_id INTEGER NOT NULL, ativo BOOLEAN NOT NULL,"
            "conciliado BOOLEAN NOT NULL, data_movimento DATE NOT NULL,"
            "tipo_movimento TEXT NOT NULL, valor NUMERIC NOT NULL)"
        ))
        c.execute(sa.text(
            "INSERT INTO contas_bancarias VALUES (1,'Cora SCFI',1,1,-24544.59)"
        ))
    try:
        yield engine
    finally:
        engine.dispose()


def _popular(engine):
    with engine.begin() as c:
        c.execute(sa.text(
            "INSERT INTO saldo_bancario_referencias VALUES "
            "(1,1,'2026-10-31',3282.73,'Extrato oficial Cora')"
        ))
        c.execute(sa.text(
            "INSERT INTO extratos_bancarios VALUES "
            "(1,1,1,1,'2026-11-05','credito',13819),"
            "(2,1,1,1,'2026-11-09','credito',130),"
            "(3,1,1,1,'2026-11-09','debito',8592.96),"
            "(4,1,1,1,'2026-11-09','debito',130)"
        ))


def test_sem_referencia_nao_inventa_saldo(engine):
    with engine.connect() as c:
        assert obter_saldo_extrato(c) is None


def test_saldo_confirmado_e_repasses_neutros(engine):
    _popular(engine)
    with engine.connect() as c:
        r = obter_saldo_extrato(c)
        assert r["referencia"] == "2026-10-31"
        assert r["saldo_extrato"] == Decimal("8508.77")
        assert r["entradas"] == Decimal("13949.00")
        assert r["saidas"] == Decimal("8722.96")
        assert r["qtd_extratos"] == 4
        assert r["pendentes"] == 0
        assert r["diferenca_interna"] == Decimal("-33053.36")
        assert r["saldo_extrato_fmt"] == "R$ 8.508,77"
        assert r["data_ultimo_extrato"] == "2026-11-09"
        assert c.execute(sa.text("SELECT saldo_atual FROM contas_bancarias WHERE id=1")).scalar_one() == -24544.59


def test_extrato_importado_pendente_afeta_caixa_sem_criar_financeiro(engine):
    _popular(engine)
    with engine.begin() as c:
        c.execute(sa.text(
            "INSERT INTO extratos_bancarios VALUES "
            "(5,1,1,0,'2026-11-10','debito',80)"
        ))
    with engine.connect() as c:
        saldo = obter_saldo_extrato(c)
        assert saldo["saldo_extrato"] == Decimal("8428.77")
        assert saldo["pendentes"] == 1
        ontem = obter_saldo_extrato(c, data_limite=date(2026, 11, 9))
        assert ontem["saldo_extrato"] == Decimal("8508.77")
        referencia = obter_saldo_extrato(c, data_limite=date(2026, 10, 31))
        assert referencia["saldo_extrato"] == Decimal("3282.73")


def test_tipo_bancario_desconhecido_falha_fechado(engine):
    _popular(engine)
    with engine.begin() as c:
        c.execute(sa.text(
            "INSERT INTO extratos_bancarios VALUES "
            "(6,1,1,0,'2026-11-10','ajuste',5)"
        ))
    with engine.connect() as c:
        with pytest.raises(ValueError, match="desconhecido"):
            obter_saldo_extrato(c)
