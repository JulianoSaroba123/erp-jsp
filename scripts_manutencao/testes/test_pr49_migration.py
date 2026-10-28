"""DDL aditivo em SQLite memória / PostgreSQL local com schema exclusivo."""
import importlib.util
from pathlib import Path
import pytest
import sqlalchemy as sa
from alembic.migration import MigrationContext
from alembic.operations import Operations
from scripts_manutencao.testes.test_pr46_os_recebimento import banco_pr46


def carregar():
    path=Path(__file__).resolve().parents[2]/'migrations/versions/20261028_01_os_custos_internos.py'
    spec=importlib.util.spec_from_file_location('migration_pr49',path)
    m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m


@pytest.fixture(params=['sqlite','postgresql'])
def engine_migracao(request):
    if request.param=='sqlite':
        e=sa.create_engine('sqlite:///:memory:')
        yield e; e.dispose(); return
    # O mesmo fixture validado da PR46 exige localhost e nome exato de banco teste.
    import os
    from uuid import uuid4
    from sqlalchemy.engine import make_url
    uri=os.environ.get('PR46_POSTGRES_TEST_URL')
    if not uri: pytest.skip('PostgreSQL isolado não configurado neste host')
    url=make_url(uri)
    assert url.get_backend_name()=='postgresql' and url.host in {'127.0.0.1','localhost','::1'}
    assert url.database=='erp_jsp_pr46_test' and not os.environ.get('RENDER_SERVICE_ID')
    assert os.environ.get('RENDER','').lower() not in {'true','1','yes'}
    e=sa.create_engine(uri); schema='pr49_migration_'+uuid4().hex
    with e.begin() as c: c.execute(sa.text(f'CREATE SCHEMA {schema}'))
    isolated=sa.create_engine(uri,connect_args={'options':f'-csearch_path={schema}'})
    try: yield isolated
    finally:
        isolated.dispose()
        with e.begin() as c: c.execute(sa.text(f'DROP SCHEMA {schema} CASCADE'))
        e.dispose()


def preparar(c):
    for t in ['ordem_servico','ordem_servico_colaborador','colaborador','ordem_servico_produtos']:
        c.execute(sa.text(f'CREATE TABLE {t} (id INTEGER PRIMARY KEY)'))
    c.execute(sa.text('CREATE TABLE lancamentos_financeiros (id INTEGER PRIMARY KEY, valor NUMERIC(12,2), descricao VARCHAR(100))'))
    c.execute(sa.text("INSERT INTO lancamentos_financeiros VALUES (165,600.00,'Original preservado')"))
    c.execute(sa.text('CREATE TABLE extrato_preservado (id INTEGER PRIMARY KEY, valor NUMERIC(12,2))'))
    c.execute(sa.text('INSERT INTO extrato_preservado VALUES (45,600)'))


def test_migration_aditiva_reversao_vazia_preserva_dados(engine_migracao):
    m=carregar()
    assert m.down_revision=='20261026_01'
    with engine_migracao.begin() as c:
        preparar(c)
        antes=c.execute(sa.text('SELECT * FROM lancamentos_financeiros')).all()
        with Operations.context(MigrationContext.configure(c)): m.upgrade()
        assert {'os_custos_internos','os_custos_auditoria'} <= set(sa.inspect(c).get_table_names())
        assert c.execute(sa.text('SELECT * FROM lancamentos_financeiros')).all()==antes
        assert c.execute(sa.text('SELECT valor FROM extrato_preservado')).scalar()==600
        with Operations.context(MigrationContext.configure(c)): m.downgrade()
        assert 'os_custos_internos' not in sa.inspect(c).get_table_names()
        assert c.execute(sa.text('SELECT * FROM lancamentos_financeiros')).all()==antes


def test_downgrade_com_historico_ou_custo_bloqueado(engine_migracao):
    m=carregar()
    with engine_migracao.begin() as c:
        preparar(c)
        with Operations.context(MigrationContext.configure(c)): m.upgrade()
        c.execute(sa.text("""INSERT INTO os_custos_internos
            (id,criado_em,atualizado_em,ativo,categoria,modalidade,descricao,data_custo,quantidade,valor,situacao,fonte_custo,chave_operacao,versao,assinatura,lancamento_id)
            VALUES(1,CURRENT_TIMESTAMP,CURRENT_TIMESTAMP,true,'outros','servico','Interno','2026-09-11',1,100,'realizado','Acordo','teste',1,'assinatura',165)"""))
        with Operations.context(MigrationContext.configure(c)):
            with pytest.raises(RuntimeError,match='bloqueada'): m.downgrade()
        assert c.execute(sa.text('SELECT valor FROM os_custos_internos')).scalar()==100
        assert c.execute(sa.text('SELECT valor FROM lancamentos_financeiros')).scalar()==600
