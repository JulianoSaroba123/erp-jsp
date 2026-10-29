"""Testes de inativação OS618/FIN224 exclusivamente em bases isoladas.

SQLite em memória ou PostgreSQL descartável no GitHub Actions.
Nenhum acesso ao banco de produção.
"""
from contextlib import contextmanager
from datetime import datetime, date
from decimal import Decimal
import importlib.util
import os
from pathlib import Path
import uuid

from alembic.migration import MigrationContext
from alembic.operations import Operations
import pytest
import sqlalchemy as sa


PATH = Path(__file__).resolve().parents[2] / "migrations" / "versions" / "20261029_02_inativacao_os_eliana.py"
spec = importlib.util.spec_from_file_location("migration_eliana", PATH)
mig = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mig)


def _schema():
    meta = sa.MetaData()
    os_table = sa.Table("ordem_servico", meta,
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("numero", sa.String(30), nullable=False),
        sa.Column("titulo", sa.String(255), nullable=False),
        sa.Column("cliente_id", sa.Integer),
        sa.Column("status", sa.String(30), nullable=False),
        sa.Column("status_pagamento", sa.String(30)),
        sa.Column("situacao_fiscal", sa.String(30)),
        sa.Column("proposta_id", sa.Integer),
        sa.Column("valor_total", sa.Numeric(12, 2)),
        sa.Column("ativo", sa.Boolean, nullable=False),
        sa.Column("atualizado_em", sa.DateTime),
    )
    fin = sa.Table("lancamentos_financeiros", meta,
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("descricao", sa.String(255), nullable=False),
        sa.Column("ordem_servico_id", sa.Integer, sa.ForeignKey("ordem_servico.id")),
        sa.Column("cliente_id", sa.Integer),
        sa.Column("conta_bancaria_id", sa.Integer),
        sa.Column("valor", sa.Numeric(12, 2), nullable=False),
        sa.Column("origem", sa.String(50)),
        sa.Column("tipo", sa.String(30), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("ativo", sa.Boolean, nullable=False),
        sa.Column("sem_movimentacao_bancaria", sa.Boolean, nullable=False),
        sa.Column("data_pagamento", sa.Date),
        sa.Column("usuario_editor", sa.String(100)),
        sa.Column("data_edicao_auditoria", sa.DateTime),
        sa.Column("atualizado_em", sa.DateTime),
    )
    items=sa.Table("ordem_servico_itens", meta,
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("ordem_servico_id", sa.Integer, sa.ForeignKey("ordem_servico.id"), nullable=False),
        sa.Column("descricao", sa.String(255)),
        sa.Column("ativo", sa.Boolean, nullable=False),
    )
    annex=sa.Table("ordem_servico_anexos", meta,
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("ordem_servico_id", sa.Integer, sa.ForeignKey("ordem_servico.id"), nullable=False),
        sa.Column("nome_original", sa.String(255)),
        sa.Column("ativo", sa.Boolean, nullable=False),
    )
    ext=sa.Table("extratos_bancarios", meta,
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("lancamento_id", sa.Integer, sa.ForeignKey("lancamentos_financeiros.id")),
        sa.Column("tipo_movimento", sa.String(10), nullable=False),
        sa.Column("data_movimento", sa.Date, nullable=False),
        sa.Column("valor", sa.Numeric(12, 2), nullable=False),
        sa.Column("conciliado", sa.Boolean, nullable=False),
        sa.Column("ativo", sa.Boolean, nullable=False),
    )
    nn=sa.Table("conciliacao_bancaria_itens", meta,
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("extrato_id", sa.Integer, sa.ForeignKey("extratos_bancarios.id")),
        sa.Column("lancamento_id", sa.Integer, sa.ForeignKey("lancamentos_financeiros.id")),
        sa.Column("valor_conciliado", sa.Numeric(12, 2), nullable=False),
        sa.Column("ativo", sa.Boolean, nullable=False),
    )
    hist=sa.Table("historico_financeiro", meta,
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("lancamento_id", sa.Integer, sa.ForeignKey("lancamentos_financeiros.id")),
        sa.Column("campo_alterado", sa.String(50)),
        sa.Column("valor_anterior", sa.Text),
        sa.Column("valor_novo", sa.Text),
        sa.Column("usuario", sa.String(100)),
        sa.Column("data_alteracao", sa.DateTime),
        sa.Column("acao", sa.String(20)),
        sa.Column("motivo", sa.Text),
        sa.Column("criado_em", sa.DateTime),
        sa.Column("atualizado_em", sa.DateTime),
        sa.Column("ativo", sa.Boolean),
    )
    return {"meta":meta,"os":os_table,"fin":fin,"itens":items,"anexos":annex,"ext":ext,"nn":nn,"hist":hist}


@contextmanager
def ambiente(motor="sqlite",popular=True):
    schema = None
    if motor == "postgresql":
        url = os.environ.get("PR46_POSTGRES_TEST_URL")
        if not url:
            pytest.skip("PostgreSQL de testes não configurado")
        engine = sa.create_engine(url)
        schema = "os_eliana_" + uuid.uuid4().hex[:12]
        with engine.begin() as admin:
            admin.exec_driver_sql("CREATE SCHEMA " + schema)
    else:
        engine = sa.create_engine("sqlite+pysqlite:///:memory:")

    try:
        with engine.connect() as con:
            if schema:
                con.exec_driver_sql("SET search_path TO " + schema)
                con.commit()
            t = _schema()
            t["meta"].create_all(con)
            con.commit()
            if popular:
                for row in [
                    dict(id=618, numero="OS20260087", titulo="Reparo em Instalação Elétrica Predial",
                         cliente_id=51, status="concluida", status_pagamento="pago",
                         situacao_fiscal="PENDENTE", proposta_id=None,
                         valor_total=Decimal("600.00"), ativo=True,
                         atualizado_em=datetime(2026,10,29)),
                    dict(id=666, numero="OS20260101", titulo="Instalação elétrica",
                         cliente_id=51, status="concluida", status_pagamento="pago",
                         situacao_fiscal="PENDENTE", valor_total=Decimal("800.00"),
                         ativo=True),
                    dict(id=667, numero="OS20260102", titulo="Instalações elétricas",
                         cliente_id=51, status="concluida", status_pagamento="pago",
                         situacao_fiscal="PENDENTE", valor_total=Decimal("600.00"),
                         ativo=True),
                ]:
                    con.execute(sa.insert(t["os"]).values(**row))
                for row in [
                    dict(id=224, descricao="OS OS20260087 - Reparo em Instalação Elétrica Predial",
                         ordem_servico_id=618, origem="ORDEM_SERVICO",
                         cliente_id=51, conta_bancaria_id=1,
                         sem_movimentacao_bancaria=False, tipo="conta_receber",
                         valor=Decimal("600.00"), status="recebido", ativo=True,
                         data_pagamento=date(2026,9,8)),
                    dict(id=139, descricao="OS OS20260101 - INSTALAÇÃO ELÉTRICA RESIDENCIAL",
                         ordem_servico_id=666, origem="ORDEM_SERVICO",
                         cliente_id=51, conta_bancaria_id=1,
                         sem_movimentacao_bancaria=False, tipo="conta_receber",
                         valor=Decimal("800.00"), status="recebido", ativo=True,
                         data_pagamento=date(2026,9,11)),
                    dict(id=140, descricao="OS OS20260102 - INSTALAÇÕES ELÉTRICA RESIDENCIAL",
                         ordem_servico_id=667, origem="ORDEM_SERVICO",
                         cliente_id=51, conta_bancaria_id=1,
                         sem_movimentacao_bancaria=False, tipo="conta_receber",
                         valor=Decimal("600.00"), status="recebido", ativo=True,
                         data_pagamento=date(2026,9,17)),
                    dict(id=165, descricao="Pagamento de mão de obra Luã – OS20260087 – Eliana Saroba",
                         ordem_servico_id=None, origem="MANUAL", tipo="conta_pagar",
                         valor=Decimal("600.00"), status="pago", ativo=True,
                         sem_movimentacao_bancaria=False, data_pagamento=date(2026,9,11)),
                ]:
                    con.execute(sa.insert(t["fin"]).values(**row))
                con.execute(sa.insert(t["itens"]), [
                    dict(id=331,ordem_servico_id=618,descricao="Serviços de Instalação Predial",ativo=True),
                ])
                con.execute(sa.insert(t["anexos"]),[
                    dict(id=1039+i,ordem_servico_id=618,
                         nome_original=f"IMG-{i}.jpg",ativo=True) for i in range(6)
                ])
                con.execute(sa.insert(t["ext"]),[
                    dict(id=1,lancamento_id=139,tipo_movimento="credito",
                         data_movimento=date(2026,9,11),valor=Decimal("800.00"),
                         ativo=True,conciliado=True),
                    dict(id=51,lancamento_id=140,tipo_movimento="credito",
                         data_movimento=date(2026,9,17),valor=Decimal("600.00"),
                         ativo=True,conciliado=True),
                ])
                con.execute(sa.insert(t["nn"]),[
                    dict(extrato_id=1,lancamento_id=139,valor_conciliado=Decimal("800.00"),ativo=True),
                    dict(extrato_id=51,lancamento_id=140,valor_conciliado=Decimal("600.00"),ativo=True),
                ])
                con.commit()
            yield con,t
    finally:
        if schema:
            with engine.begin() as admin:
                admin.exec_driver_sql("DROP SCHEMA " + schema + " CASCADE")
        engine.dispose()


def aplicar(con):
    mig.op = Operations(MigrationContext.configure(con))
    with con.begin():
        mig.upgrade()


@pytest.mark.parametrize("motor", ["sqlite","postgresql"])
def test_inativar_preservando_extratos_anexos_os_legitimas(motor):
    with ambiente(motor) as (con,t):
        antes_ext = [dict(r) for r in con.execute(sa.select(t["ext"])).mappings()]
        antes_nn = [dict(r) for r in con.execute(sa.select(t["nn"])).mappings()]
        antes_itens = [dict(r) for r in con.execute(sa.select(t["itens"])).mappings()]
        antes_anexos = [dict(r) for r in con.execute(sa.select(t["anexos"])).mappings()]
        con.commit()
        aplicar(con)
        assert con.execute(sa.select(t["os"].c.ativo).where(t["os"].c.id==618)).scalar_one() is False
        assert con.execute(sa.select(t["fin"].c.ativo).where(t["fin"].c.id==224)).scalar_one() is False
        assert con.execute(sa.select(t["os"].c.status).where(t["os"].c.id==618)).scalar_one() == "concluida"
        assert con.execute(sa.select(t["fin"].c.status).where(t["fin"].c.id==224)).scalar_one() == "recebido"
        assert [dict(r) for r in con.execute(sa.select(t["ext"])).mappings()] == antes_ext
        assert [dict(r) for r in con.execute(sa.select(t["nn"])).mappings()] == antes_nn
        assert [dict(r) for r in con.execute(sa.select(t["itens"])).mappings()] == antes_itens
        assert [dict(r) for r in con.execute(sa.select(t["anexos"])).mappings()] == antes_anexos
        for id in [666,667]:
            assert con.execute(sa.select(t["os"].c.ativo).where(t["os"].c.id==id)).scalar_one()
        for id in [139,140,165]:
            assert con.execute(sa.select(t["fin"].c.ativo).where(t["fin"].c.id==id)).scalar_one()
        audit_os=sa.Table("os_atividade_auditoria",sa.MetaData(),autoload_with=con)
        assert con.execute(sa.select(sa.func.count()).select_from(audit_os)).scalar_one()==1
        assert con.execute(sa.select(sa.func.count()).select_from(t["hist"])).scalar_one()==1
        assert "ordem incorreta" in con.execute(sa.select(audit_os.c.motivo)).scalar_one()
        assert "R$ 600,00" in con.execute(sa.select(t["hist"].c.motivo)).scalar_one()
        con.commit()
        assert mig._preflight(con) is False  # Já foram inativados, sem nova alteração.


@pytest.mark.parametrize("motor", ["sqlite","postgresql"])
def test_referencia_fiscal_extra_bloqueia_tudo(motor):
    with ambiente(motor) as (con,t):
        other=sa.Table("nota_fiscal_os_teste",t["meta"],
            sa.Column("id",sa.Integer,primary_key=True),
            sa.Column("ordem_servico_id",sa.Integer,sa.ForeignKey("ordem_servico.id")))
        other.create(con)
        con.execute(sa.insert(other).values(id=1,ordem_servico_id=618))
        con.commit()
        mig.op=Operations(MigrationContext.configure(con))
        with pytest.raises(RuntimeError,match="vínculo com OS618"):
            with con.begin():
                mig.upgrade()
        assert con.execute(sa.select(t["os"].c.ativo).where(t["os"].c.id==618)).scalar_one()
        assert con.execute(sa.select(t["fin"].c.ativo).where(t["fin"].c.id==224)).scalar_one()


@pytest.mark.parametrize("motor", ["sqlite","postgresql"])
def test_recebimento_legitimo_alterado_bloqueia(motor):
    with ambiente(motor) as (con,t):
        con.execute(sa.update(t["nn"]).where(t["nn"].c.extrato_id==51)
                    .values(valor_conciliado=Decimal("590.00")))
        con.commit()
        mig.op=Operations(MigrationContext.configure(con))
        with pytest.raises(RuntimeError,match="conciliação legítima"):
            with con.begin():
                mig.upgrade()
        assert con.execute(sa.select(t["os"].c.ativo).where(t["os"].c.id==618)).scalar_one()
        assert con.execute(sa.select(t["fin"].c.ativo).where(t["fin"].c.id==224)).scalar_one()


@pytest.mark.parametrize("motor", ["sqlite","postgresql"])
def test_banco_novo_nao_altera_estrutura_basica(motor):
    with ambiente(motor,popular=False) as (con,t):
        aplicar(con)
        auditoria=sa.Table("os_atividade_auditoria",sa.MetaData(),autoload_with=con)
        assert con.execute(sa.select(sa.func.count()).select_from(auditoria)).scalar_one()==0
        assert con.execute(sa.select(sa.func.count()).select_from(t["os"])).scalar_one()==0
        assert con.execute(sa.select(sa.func.count()).select_from(t["fin"])).scalar_one()==0
