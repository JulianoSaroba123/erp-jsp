"""Teste da migração de auditoria de setembro: SQLite isolado e PostgreSQL descartável.

Nenhum teste acessa o banco de produção: PostgreSQL usa apenas PR46_POSTGRES_TEST_URL
do serviço efêmero do GitHub Actions, com schema único por caso.
"""
from contextlib import contextmanager
from datetime import date
from decimal import Decimal
import importlib.util
import os
from pathlib import Path
import uuid

from alembic.migration import MigrationContext
from alembic.operations import Operations
import pytest
import sqlalchemy as sa


MIGRATION = (Path(__file__).resolve().parents[2] / "migrations" / "versions" /
             "20261029_01_auditoria_set2026_pagamentos_pedagio.py")
spec = importlib.util.spec_from_file_location("auditoria_set2026_migration", MIGRATION)
migration = importlib.util.module_from_spec(spec)
spec.loader.exec_module(migration)


def _tabelas():
    meta = sa.MetaData()
    fin = sa.Table(
        "lancamentos_financeiros", meta,
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("descricao", sa.String(255), nullable=False),
        sa.Column("valor", sa.Numeric(12, 2), nullable=False),
        sa.Column("tipo", sa.String(20), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("origem", sa.String(50)),
        sa.Column("ativo", sa.Boolean, nullable=False),
        sa.Column("data_lancamento", sa.Date, nullable=False),
        sa.Column("data_vencimento", sa.Date),
        sa.Column("data_pagamento", sa.Date),
        sa.Column("conta_bancaria_id", sa.Integer),
        sa.Column("ordem_servico_id", sa.Integer),
        sa.Column("ordem_servico_parcela_id", sa.Integer),
        sa.Column("proposta_id", sa.Integer),
        sa.Column("proposta_parcela_id", sa.Integer),
        sa.Column("pedido_id", sa.Integer),
        sa.Column("custo_fixo_id", sa.Integer),
        sa.Column("usuario_editor", sa.String(100)),
        sa.Column("data_edicao_auditoria", sa.DateTime),
        sa.Column("atualizado_em", sa.DateTime),
    )
    ext = sa.Table(
        "extratos_bancarios", meta,
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("lancamento_id", sa.Integer),
        sa.Column("valor", sa.Numeric(12, 2), nullable=False),
        sa.Column("tipo_movimento", sa.String(10), nullable=False),
        sa.Column("data_movimento", sa.Date, nullable=False),
        sa.Column("ativo", sa.Boolean, nullable=False),
        sa.Column("conciliado", sa.Boolean, nullable=False),
    )
    nn = sa.Table(
        "conciliacao_bancaria_itens", meta,
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("lancamento_id", sa.Integer, nullable=False),
        sa.Column("extrato_id", sa.Integer, nullable=False),
        sa.Column("valor_conciliado", sa.Numeric(12, 2), nullable=False),
        sa.Column("ativo", sa.Boolean, nullable=False),
    )
    hist = sa.Table(
        "historico_financeiro", meta,
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("lancamento_id", sa.Integer, nullable=False),
        sa.Column("campo_alterado", sa.String(50), nullable=False),
        sa.Column("valor_anterior", sa.Text),
        sa.Column("valor_novo", sa.Text),
        sa.Column("usuario", sa.String(100), nullable=False),
        sa.Column("data_alteracao", sa.DateTime, nullable=False),
        sa.Column("acao", sa.String(20)),
        sa.Column("motivo", sa.Text),
        sa.Column("criado_em", sa.DateTime, nullable=False),
        sa.Column("atualizado_em", sa.DateTime, nullable=False),
        sa.Column("ativo", sa.Boolean, nullable=False),
    )
    return meta, fin, ext, nn, hist


@contextmanager
def ambiente(motor="sqlite", popular=True):
    if motor == "postgresql":
        url = os.environ.get("PR46_POSTGRES_TEST_URL")
        if not url:
            pytest.skip("PostgreSQL descartável não configurado")
        engine = sa.create_engine(url)
        schema = "audit_" + uuid.uuid4().hex[:12]
        with engine.begin() as admin:
            admin.exec_driver_sql("CREATE SCHEMA " + schema)
    else:
        engine = sa.create_engine("sqlite+pysqlite:///:memory:")
        schema = None

    try:
        with engine.connect() as con:
            if schema:
                con.exec_driver_sql("SET search_path TO " + schema)
                con.commit()
            meta, fin, ext, nn, hist = _tabelas()
            meta.create_all(con)
            con.commit()
            if popular:
                regs = []
                for i, (descricao, tipo, valor, dt_pg) in {
                    **migration._DUPLICADOS, **migration._CORRETOS
                }.items():
                    regs.append(dict(
                        id=i, descricao=descricao, tipo=tipo, valor=valor,
                        status="pago", origem="MANUAL", ativo=True,
                        data_lancamento=dt_pg, data_vencimento=dt_pg,
                        data_pagamento=dt_pg, atualizado_em=dt_pg,
                    ))
                regs.append(dict(
                    id=182, descricao="Pagamento de pedágio em deslocamento",
                    valor=Decimal("20.40"), tipo="despesa",
                    status="pago", origem="MANUAL", ativo=True,
                    data_lancamento=date(26, 2, 9), data_vencimento=date(26, 2, 9),
                    data_pagamento=date(26, 2, 9), atualizado_em=date(2026, 9, 9),
                ))
                con.execute(sa.insert(fin), regs)
                con.execute(sa.insert(ext), [
                    dict(id=2, lancamento_id=166, valor=Decimal("500.00"),
                         tipo_movimento="debito", data_movimento=date(2026, 9, 11),
                         ativo=True, conciliado=True),
                    dict(id=3, lancamento_id=165, valor=Decimal("600.00"),
                         tipo_movimento="debito", data_movimento=date(2026, 9, 11),
                         ativo=True, conciliado=True),
                    dict(id=15, lancamento_id=182, valor=Decimal("20.40"),
                         tipo_movimento="debito", data_movimento=date(2026, 9, 9),
                         ativo=True, conciliado=True),
                ])
                con.execute(sa.insert(nn), [
                    dict(extrato_id=2, lancamento_id=166,
                         valor_conciliado=Decimal("500.00"), ativo=True),
                    dict(extrato_id=3, lancamento_id=165,
                         valor_conciliado=Decimal("600.00"), ativo=True),
                    dict(extrato_id=15, lancamento_id=182,
                         valor_conciliado=Decimal("20.40"), ativo=True),
                ])
                con.commit()
            yield con, (fin, ext, nn, hist)
    finally:
        if schema:
            with engine.begin() as admin:
                admin.exec_driver_sql("DROP SCHEMA " + schema + " CASCADE")
        engine.dispose()


def aplicar(con):
    migration.op = Operations(MigrationContext.configure(con))
    with con.begin():
        migration.upgrade()


@pytest.mark.parametrize("motor", ["sqlite", "postgresql"])
def test_correcao_auditavel_sem_movimentar_banco(motor):
    with ambiente(motor) as (con, (fin, ext, nn, hist)):
        extratos_antes = con.execute(sa.select(ext).order_by(ext.c.id)).mappings().all()
        nn_antes = con.execute(sa.select(nn).order_by(nn.c.id)).mappings().all()
        aplicar(con)
        regs = {
            r.id: r for r in con.execute(sa.select(fin)).all()
        }
        for i in (99, 123, 141, 142):
            assert regs[i].ativo is False
        for i in (165, 166, 182):
            assert regs[i].ativo is True
        for campo in ("data_lancamento", "data_vencimento", "data_pagamento"):
            assert getattr(regs[182], campo) == date(2026, 9, 9)
        assert con.execute(sa.select(ext).order_by(ext.c.id)).mappings().all() == extratos_antes
        assert con.execute(sa.select(nn).order_by(nn.c.id)).mappings().all() == nn_antes
        audits = con.execute(sa.select(hist)).mappings().all()
        assert len(audits) == 7
        assert {r["lancamento_id"] for r in audits} == {99, 123, 141, 142, 182}
        assert sum(r["acao"] == "inativacao" for r in audits) == 4
        assert all(r["motivo"] and r["usuario"] == migration._AUTOR for r in audits)
        # Segunda execução idempotente, sem produzir novas linhas de auditoria.
        aplicar(con)
        assert con.execute(sa.select(sa.func.count()).select_from(hist)).scalar_one() == 7


@pytest.mark.parametrize("motor", ["sqlite", "postgresql"])
def test_vinculo_em_duplicado_aborta_e_reverte(motor):
    with ambiente(motor) as (con, (fin, ext, nn, hist)):
        con.execute(sa.insert(nn).values(
            extrato_id=55, lancamento_id=99,
            valor_conciliado=Decimal("100.00"), ativo=False))
        con.commit()
        migration.op = Operations(MigrationContext.configure(con))
        with pytest.raises(RuntimeError, match="referência externa"):
            with con.begin():
                migration.upgrade()
        assert con.execute(sa.select(fin.c.ativo).where(fin.c.id == 99)).scalar_one() is True
        assert con.execute(sa.select(sa.func.count()).select_from(hist)).scalar_one() == 0


@pytest.mark.parametrize("motor", ["sqlite", "postgresql"])
def test_data_divergente_aborta_sem_alterar_outros(motor):
    with ambiente(motor) as (con, (fin, ext, nn, hist)):
        con.execute(sa.update(fin).where(fin.c.id == 182).values(data_vencimento=date(2026, 9, 9)))
        con.commit()
        migration.op = Operations(MigrationContext.configure(con))
        with pytest.raises(RuntimeError, match="data data_vencimento"):
            with con.begin():
                migration.upgrade()
        assert con.execute(sa.select(sa.func.count()).select_from(hist)).scalar_one() == 0
        assert all(row.ativo for row in con.execute(
            sa.select(fin.c.ativo).where(fin.c.id.in_([99, 123, 141, 142]))))


@pytest.mark.parametrize("motor", ["sqlite", "postgresql"])
def test_banco_vazio_nao_recebe_ajustes(motor):
    with ambiente(motor, popular=False) as (con, (fin, ext, nn, hist)):
        aplicar(con)
        assert con.execute(sa.select(sa.func.count()).select_from(fin)).scalar_one() == 0
        assert con.execute(sa.select(sa.func.count()).select_from(hist)).scalar_one() == 0
