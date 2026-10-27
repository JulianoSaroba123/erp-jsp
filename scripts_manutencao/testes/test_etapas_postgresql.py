import pytest
from scripts_manutencao.testes.test_receita_etapas import (
    banco_pr46, caso_jumirim_ficticio,
    test_etapas_separam_competencia_de_caixa_e_sao_idempotentes,
    test_http_etapas_restricao_e_csrf,
    test_reducao_da_os_abaixo_das_etapas_e_revertida,
    test_estorno_auditavel_sem_alterar_caixa,
)
pytestmark = pytest.mark.parametrize('banco_pr46', ['postgresql'], indirect=True)


def test_duas_sessoes_nao_registram_etapa_duplicada(caso_jumirim_ficticio):
    from concurrent.futures import ThreadPoolExecutor
    from threading import Barrier
    from datetime import date
    from app.extensoes import db
    from app.ordem_servico.receita_etapas import registrar_etapa
    from app.ordem_servico.ordem_servico_model import ReconhecimentoReceitaOS
    app, ids = caso_jumirim_ficticio
    barreira = Barrier(2)
    def registrar(indice):
        with app.app_context():
            try:
                barreira.wait(timeout=15)
                registrar_etapa(os_id=ids['os'], competencia=date(2026,9,20),
                    descricao='Etapa fictícia', valor='4000.00', usuario='9',
                    chave=f'chave-concorrente-{indice}')
                db.session.commit()
                return 'registrada'
            except ValueError:
                db.session.rollback()
                return 'duplicada'
            finally:
                db.session.remove()
    with ThreadPoolExecutor(max_workers=2) as pool:
        assert sorted(pool.map(registrar, [1, 2])) == ['duplicada', 'registrada']
    with app.app_context():
        assert ReconhecimentoReceitaOS.query.filter_by(ordem_servico_id=ids['os']).count() == 1


def test_migration_etapas_postgresql(banco_pr46):
    import importlib.util
    from pathlib import Path
    from sqlalchemy import create_engine, text, inspect
    from alembic.migration import MigrationContext
    from alembic.operations import Operations
    from app.config import config
    path = Path(__file__).resolve().parents[2] / 'migrations/versions/20261027_01_os_receita_etapas.py'
    spec = importlib.util.spec_from_file_location('migration_etapas_pg', path)
    migration = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(migration)
    engine = create_engine(banco_pr46, **config['testing'].SQLALCHEMY_ENGINE_OPTIONS)
    try:
        with engine.begin() as conn:
            conn.execute(text('CREATE TABLE ordem_servico (id INTEGER PRIMARY KEY)'))
            conn.execute(text('INSERT INTO ordem_servico (id) VALUES (1)'))
            with Operations.context(MigrationContext.configure(conn)):
                migration.upgrade()
                assert inspect(conn).has_table('os_receita_etapas')
                conn.execute(text("INSERT INTO os_receita_etapas (id,ordem_servico_id,data_competencia,descricao,valor,usuario,chave_operacao,criado_em,atualizado_em) VALUES (1,1,'2026-09-20','Teste',100,'9','teste','2026-09-20','2026-09-20')"))
                with pytest.raises(RuntimeError, match='bloqueado'):
                    migration.downgrade()
                conn.execute(text('DELETE FROM os_receita_etapas'))
                migration.downgrade()
                assert not inspect(conn).has_table('os_receita_etapas')
    finally:
        engine.dispose()
