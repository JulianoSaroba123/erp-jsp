# -*- coding: utf-8 -*-
"""Reparo legado em banco PostgreSQL descartável: NUNCA usa Render."""
from datetime import date
from decimal import Decimal
from importlib.util import spec_from_file_location, module_from_spec
import os
from pathlib import Path
from unittest.mock import patch
from uuid import uuid4

import pytest
import sqlalchemy as sa


@pytest.fixture
def banco_reparo():
    url = os.environ.get("PR46_POSTGRES_TEST_URL")
    if not url:
        pytest.skip("PostgreSQL de teste não configurado")
    u = sa.engine.make_url(url)
    assert u.get_backend_name() == "postgresql"
    assert u.host in ("localhost", "127.0.0.1", "::1")
    assert u.database == "erp_jsp_pr46_test"
    assert not os.environ.get("RENDER_SERVICE_ID")
    assert os.environ.get("RENDER", "").lower() not in ("true", "yes", "1")
    schema = "reparo_" + uuid4().hex
    admin = sa.create_engine(url)
    with admin.begin() as c:
        c.execute(sa.text(f"CREATE SCHEMA {schema}"))
    engine = sa.create_engine(url,connect_args={"options":f"-csearch_path={schema}"})
    try:
        with engine.begin() as c:
            for stmt in (
                "CREATE TABLE ordem_servico (id INTEGER PRIMARY KEY, numero TEXT, ativo BOOLEAN, valor_total NUMERIC, status_pagamento TEXT)",
                "CREATE TABLE ordem_servico_parcelas (id INTEGER PRIMARY KEY, ordem_servico_id INTEGER, numero_parcela INTEGER, valor NUMERIC, pago BOOLEAN, data_pagamento DATE, ativo BOOLEAN, atualizado_em TIMESTAMP)",
                "CREATE TABLE lancamentos_financeiros (id INTEGER PRIMARY KEY, ordem_servico_id INTEGER, ordem_servico_parcela_id INTEGER, ativo BOOLEAN, tipo TEXT, status TEXT, valor NUMERIC, data_pagamento DATE)",
                "CREATE TABLE extratos_bancarios (id INTEGER PRIMARY KEY, ativo BOOLEAN, conciliado BOOLEAN, tipo_movimento TEXT, valor NUMERIC, data_movimento DATE)",
                "CREATE TABLE conciliacao_bancaria_itens (id INTEGER PRIMARY KEY, extrato_id INTEGER, lancamento_id INTEGER, valor_conciliado NUMERIC, ativo BOOLEAN)",
                "CREATE TABLE historico_financeiro (id SERIAL PRIMARY KEY,lancamento_id INTEGER,campo_alterado TEXT,valor_anterior TEXT,valor_novo TEXT,usuario TEXT,data_alteracao TIMESTAMP,acao TEXT,motivo TEXT,criado_em TIMESTAMP,atualizado_em TIMESTAMP,ativo BOOLEAN)",
            ):
                c.execute(sa.text(stmt))
            c.execute(sa.text("INSERT INTO ordem_servico VALUES (672,'OS20260107',true,7100,'pendente')"))
            c.execute(sa.text("INSERT INTO ordem_servico_parcelas (id,ordem_servico_id,numero_parcela,valor,pago,data_pagamento,ativo) VALUES (36,672,1,3550,false,NULL,true),(37,672,2,3550,false,NULL,true)"))
            c.execute(sa.text("INSERT INTO lancamentos_financeiros VALUES (336,672,36,true,'conta_receber','recebido',3550,'2026-11-05'),(337,672,37,true,'conta_receber','pendente',3550,NULL),(338,625,NULL,true,'conta_receber','recebido',6000,'2026-11-05')"))
            c.execute(sa.text("INSERT INTO extratos_bancarios VALUES (223,true,true,'credito',9550,'2026-11-05')"))
            c.execute(sa.text("INSERT INTO conciliacao_bancaria_itens VALUES (222,223,336,3550,true),(223,223,338,6000,true)"))
        p = Path(__file__).resolve().parents[2] / "migrations/versions/20261107_01_reparo_os20260107_parcela36.py"
        spec = spec_from_file_location("reparo_os_parcela_test",p)
        modulo=module_from_spec(spec)
        spec.loader.exec_module(modulo)
        yield engine,modulo
    finally:
        engine.dispose()
        with admin.begin() as c:
            c.execute(sa.text(f"DROP SCHEMA IF EXISTS {schema} CASCADE"))
        admin.dispose()


def aplicar(c, modulo):
    with patch.object(modulo.op,"get_bind",return_value=c):
        modulo.upgrade()


def test_reparo_realizado_com_auditoria_e_idempotencia(banco_reparo):
    eng,m=banco_reparo
    with eng.begin() as c:
        aplicar(c,m)
        aplicar(c,m)
    with eng.connect() as c:
        p=c.execute(sa.text("SELECT pago,data_pagamento FROM ordem_servico_parcelas WHERE id=36")).one()
        assert p.pago and p.data_pagamento==date(2026,11,5)
        p2=c.execute(sa.text("SELECT pago,data_pagamento FROM ordem_servico_parcelas WHERE id=37")).one()
        assert not p2.pago and p2.data_pagamento is None
        assert c.execute(sa.text("SELECT status_pagamento FROM ordem_servico WHERE id=672")).scalar_one()=="parcial"
        assert c.execute(sa.text("SELECT count(*) FROM historico_financeiro")).scalar_one()==1
        assert c.execute(sa.text("SELECT count(*) FROM conciliacao_bancaria_itens WHERE ativo=true")).scalar_one()==2
        assert c.execute(sa.text("SELECT count(*) FROM lancamentos_financeiros")).scalar_one()==3


def test_valor_divergente_aborta_sem_alteracoes(banco_reparo):
    eng,m=banco_reparo
    with eng.begin() as c:
        c.execute(sa.text("UPDATE lancamentos_financeiros SET valor=3549 WHERE id=336"))
    with pytest.raises(RuntimeError,match="primeiro título divergente"):
        with eng.begin() as c:
            aplicar(c,m)
    with eng.connect() as c:
        assert not c.execute(sa.text("SELECT pago FROM ordem_servico_parcelas WHERE id=36")).scalar_one()
        assert c.execute(sa.text("SELECT count(*) FROM historico_financeiro")).scalar_one()==0


def test_pedido_de_reparo_em_base_sem_os_eh_inerte(banco_reparo):
    eng,m=banco_reparo
    with eng.begin() as c:
        c.execute(sa.text("DELETE FROM ordem_servico WHERE id=672"))
        aplicar(c,m)
    with eng.connect() as c:
        assert c.execute(sa.text("SELECT count(*) FROM historico_financeiro")).scalar_one()==0
