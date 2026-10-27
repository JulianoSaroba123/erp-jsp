from pathlib import Path
import importlib.util
import pytest
import sqlalchemy as sa
from alembic.migration import MigrationContext
from alembic.operations import Operations


def test_migration_cria_tabela_e_protege_historico():
    path = Path(__file__).resolve().parents[2] / 'migrations/versions/20261027_01_os_receita_etapas.py'
    spec = importlib.util.spec_from_file_location('etapas_migration', path)
    migration = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(migration)
    engine = sa.create_engine('sqlite:///:memory:')
    with engine.begin() as conn:
        conn.execute(sa.text('CREATE TABLE ordem_servico (id INTEGER PRIMARY KEY)'))
        conn.execute(sa.text('INSERT INTO ordem_servico (id) VALUES (1)'))
        with Operations.context(MigrationContext.configure(conn)):
            migration.upgrade()
            conn.execute(sa.text("INSERT INTO os_receita_etapas (id,ordem_servico_id,data_competencia,descricao,valor,usuario,chave_operacao,criado_em,atualizado_em) VALUES (1,1,'2026-09-20','Teste',100,'9','teste','2026-09-20','2026-09-20')"))
            with pytest.raises(RuntimeError, match='bloqueado'):
                migration.downgrade()
            conn.execute(sa.text('DELETE FROM os_receita_etapas'))
            migration.downgrade()
        assert not sa.inspect(conn).has_table('os_receita_etapas')
    engine.dispose()
