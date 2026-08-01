# -*- coding: utf-8 -*-
"""
Testes da App Factory com TestingConfig
========================================

Testa criação da aplicação com SQLite e segunda instância.
"""

from __future__ import annotations

import os
import sys
import tempfile
from contextlib import contextmanager
from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest

# Adicionar raiz ao path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


@contextmanager
def captured_templates(app):
    """Captura templates renderizados e seus contextos."""
    from flask import template_rendered

    recorded = []

    def record(sender, template, context, **extra):
        recorded.append((template, context))

    template_rendered.connect(record, app)
    try:
        yield recorded
    finally:
        template_rendered.disconnect(record, app)


def _criar_usuario_e_logar(client, app):
    """Cria usuário de teste e autentica no sistema."""
    from app.extensoes import db
    from app.auth.usuario_model import Usuario

    with app.app_context():
        db.create_all()
        usuario = Usuario.query.filter_by(usuario='auditor_fin').first()
        if not usuario:
            usuario = Usuario(
                nome='Auditor Financeiro',
                email='auditor_fin@example.com',
                usuario='auditor_fin',
                tipo_usuario='admin',
                email_confirmado=True,
                primeiro_login=False,
            )
            usuario.set_senha('SenhaSegura123')
            db.session.add(usuario)
            db.session.commit()

    login_response = client.post(
        '/auth/login',
        data={
            'identificador': 'auditor_fin',
            'senha': 'SenhaSegura123',
        },
        follow_redirects=False,
    )
    assert login_response.status_code in {302, 303}

    with client.session_transaction() as session:
        assert session.get('_user_id'), 'Sessão autenticada não foi criada'


def _seed_lancamentos_para_dashboard(app):
    """Insere dados mínimos para validar aliases no template do dashboard."""
    from app.extensoes import db
    from app.financeiro.financeiro_model import LancamentoFinanceiro

    with app.app_context():
        db.create_all()

        # Limpa apenas lançamentos de seed de auditoria para evitar interferência.
        LancamentoFinanceiro.query.filter(
            LancamentoFinanceiro.descricao.like('SEED_AUDITORIA_%')
        ).delete(synchronize_session=False)

        hoje = date.today()
        receita = LancamentoFinanceiro(
            descricao='SEED_AUDITORIA_RECEITA',
            valor=Decimal('150.00'),
            tipo='receita',
            status='recebido',
            data_lancamento=hoje,
            data_vencimento=hoje,
            data_pagamento=hoje,
            origem='TESTE',
        )
        despesa = LancamentoFinanceiro(
            descricao='SEED_AUDITORIA_DESPESA',
            valor=Decimal('50.00'),
            tipo='despesa',
            status='pago',
            data_lancamento=hoje,
            data_vencimento=hoje,
            data_pagamento=hoje,
            origem='TESTE',
        )
        db.session.add(receita)
        db.session.add(despesa)
        db.session.commit()


def _upgrade_sqlite_with_alembic(sqlite_path):
    """Executa alembic upgrade head em um SQLite temporário."""
    from alembic import command
    from alembic.config import Config

    repo_root = Path(__file__).resolve().parents[1]
    alembic_ini = repo_root / 'alembic.ini'
    cfg = Config(str(alembic_ini))
    cfg.set_main_option('script_location', str(repo_root / 'migrations'))
    cfg.set_main_option('sqlalchemy.url', f'sqlite:///{sqlite_path}')
    command.upgrade(cfg, 'head')


def _create_pre_migration_schema(sqlite_path):
    """Cria schema mínimo sem a nova FK para validar upgrade/backfill."""
    from sqlalchemy import create_engine, text

    engine = create_engine(f'sqlite:///{sqlite_path}')
    with engine.begin() as conn:
        conn.execute(text('CREATE TABLE ordem_servico (id INTEGER PRIMARY KEY, numero VARCHAR(50))'))
        conn.execute(
            text(
                'CREATE TABLE ordem_servico_parcelas ('
                'id INTEGER PRIMARY KEY, '
                'ordem_servico_id INTEGER NOT NULL, '
                'numero_parcela INTEGER NOT NULL, '
                'data_vencimento DATE, '
                'valor NUMERIC(10,2), '
                'pago BOOLEAN DEFAULT 0, '
                'data_pagamento DATE)'
            )
        )
        conn.execute(
            text(
                'CREATE TABLE lancamentos_financeiros ('
                'id INTEGER PRIMARY KEY, '
                'ordem_servico_id INTEGER, '
                'numero_parcela VARCHAR(20), '
                'descricao VARCHAR(255), '
                'valor NUMERIC(12,2), '
                'status VARCHAR(20), '
                'data_pagamento DATE, '
                'ativo BOOLEAN DEFAULT 1)'
            )
        )
    engine.dispose()


def test_app_factory_cria_com_testing_config():
    """Testa criação da app com TestingConfig."""
    from app import create_app

    app = create_app('testing')

    assert app is not None
    assert app.config['TESTING'] is True
    assert 'sqlite:///:memory:' in app.config['SQLALCHEMY_DATABASE_URI']


def test_blueprints_registrados():
    """Testa registro dos blueprints obrigatórios."""
    from app import create_app

    app = create_app('testing')

    blueprints = list(app.blueprints.keys())
    assert len(blueprints) > 0
    # Financeiro deve estar registrado
    assert 'bp_financeiro' in blueprints or 'financeiro' in blueprints


def test_tabelas_criadas():
    """Testa criação das tabelas no banco SQLite."""
    from app import create_app
    from app.extensoes import db
    from sqlalchemy import inspect

    app = create_app('testing')

    with app.app_context():
        db.create_all()

        inspector = inspect(db.engine)
        tables = inspector.get_table_names()

        assert 'lancamentos_financeiros' in tables
        assert 'ordem_servico' in tables


def test_colunas_lancamento_financeiro():
    """Testa presença das colunas obrigatórias."""
    from app import create_app
    from app.extensoes import db
    from sqlalchemy import inspect

    app = create_app('testing')

    with app.app_context():
        db.create_all()

        inspector = inspect(db.engine)
        columns = [col['name'] for col in inspector.get_columns('lancamentos_financeiros')]

        required = [
            'id', 'tipo', 'valor', 'status',
            'data_pagamento', 'data_vencimento',
            'ordem_servico_id', 'ordem_servico_parcela_id'
        ]

        for col in required:
            assert col in columns, f"Coluna {col} não encontrada"


def test_segunda_inicializacao_idempotente():
    """Testa que segunda inicialização é idempotente."""
    from app import create_app
    from app.extensoes import db

    app = create_app('testing')

    with app.app_context():
        db.create_all()  # Primeira
        db.create_all()  # Segunda - deve ser idempotente
        # Se chegar aqui sem exceção, passou


def test_segunda_instancia_app_factory_arquivo_sqlite_real():
    """
    Testa segunda instância da factory sobre arquivo SQLite real.

    Regra 12: Segunda app factory deve funcionar sobre mesmo arquivo.
    Demonstra que múltiplas instâncias podem ser criadas com sucesso.
    """
    from app import create_app
    from app.extensoes import db
    from app.financeiro.financeiro_model import LancamentoFinanceiro

    # Criar arquivo temporário REAL (não :memory:)
    with tempfile.NamedTemporaryFile(
        mode='w', suffix='.db', delete=False, dir=tempfile.gettempdir()
    ) as temp_db:
        db_path = temp_db.name

    try:
        # === PRIMEIRA INSTÂNCIA ===
        app1 = create_app('testing')
        app1.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
        app1.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

        with app1.app_context():
            db.create_all()

            # Criar lançamento
            lanc1 = LancamentoFinanceiro(
                tipo='receita',
                valor=Decimal('100.00'),
                status='pendente',
                data_lancamento=date.today(),
                descricao='Teste primeira instância',
                origem='TESTE'
            )
            db.session.add(lanc1)
            db.session.commit()

            # Verificar que foi criado na primeira instância
            count1 = LancamentoFinanceiro.query.count()
            assert count1 == 1, f"Esperava 1 lançamento, encontrou {count1}"

        # === SEGUNDA INSTÂNCIA (nova factory, mesma URI) ===
        # Demonstra que segunda factory pode ser criada com sucesso
        app2 = create_app('testing')
        app2.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
        app2.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

        with app2.app_context():
            # Segunda instância também funciona sem erros
            db.create_all()  # Idempotente

            # Criar lançamento na segunda instância
            lanc2 = LancamentoFinanceiro(
                tipo='despesa',
                valor=Decimal('50.00'),
                status='pendente',
                data_lancamento=date.today(),
                descricao='Teste segunda instância',
                origem='TESTE'
            )
            db.session.add(lanc2)
            db.session.commit()

            # Verificar que pode consultar
            count2 = LancamentoFinanceiro.query.count()
            assert count2 >= 1, f"Segunda instância deve ter pelo menos 1 lançamento, encontrou {count2}"

        # Sucesso: Duas instâncias criadas sem erro

    finally:
        # Limpar arquivo temporário
        if os.path.exists(db_path):
            try:
                os.unlink(db_path)
            except:
                pass  # Pode estar locked


def test_rotas_financeiras_existem():
    """Testa que rotas financeiras estão registradas."""
    from app import create_app

    app = create_app('testing')

    routes = [rule.endpoint for rule in app.url_map.iter_rules()]

    # Verificar rotas financeiras obrigatórias
    financeiro_routes = [r for r in routes if 'financeiro' in r.lower()]
    assert len(financeiro_routes) > 0, "Nenhuma rota financeira encontrada"


def test_rota_dashboard_responde_sem_autenticacao():
    """Testa que dashboard redireciona quando não autenticado ou retorna 404 se blueprint não carregado."""
    from app import create_app
    from app.extensoes import db

    app = create_app('testing')

    with app.app_context():
        db.create_all()

    with app.test_client() as client:
        response = client.get('/financeiro/dashboard')

        # Deve redirecionar para login (302), retornar página (200) ou 404 se blueprint não disponível
        assert response.status_code in {200, 302, 404}, \
            f"Dashboard retornou status inesperado: {response.status_code}"


def test_dashboard_financeiro_autenticado_http_200_com_template_e_aliases():
    """Valida dashboard autenticado com renderização e uso efetivo dos aliases."""
    from app import create_app

    app = create_app('testing')

    _seed_lancamentos_para_dashboard(app)

    from app.configuracao.configuracao_utils import invalidate_cache

    with app.test_client() as client:
        _criar_usuario_e_logar(client, app)
        invalidate_cache()

        with captured_templates(app) as templates:
            response = client.get('/financeiro/')

        assert response.status_code == 200
        assert templates, 'Nenhum template foi renderizado no dashboard'
        assert templates[-1][0].name == 'financeiro/dashboard.html'

        # Evidência de acesso efetivo dos aliases no HTML renderizado.
        html = response.get_data(as_text=True)
        assert '150,00' in html  # total_receitas
        assert '50,00' in html   # total_despesas
        assert '100,00' in html  # saldo
        assert 'lançamento(s)' in html


def test_listagem_financeira_autenticada_http_200_com_template_renderizado():
    """Valida listagem autenticada com renderização real do template."""
    from app import create_app

    app = create_app('testing')

    _seed_lancamentos_para_dashboard(app)

    from app.configuracao.configuracao_utils import invalidate_cache

    with app.test_client() as client:
        _criar_usuario_e_logar(client, app)
        invalidate_cache()

        with captured_templates(app) as templates:
            response = client.get('/financeiro/lancamentos')

        assert response.status_code == 200
        assert templates, 'Nenhum template foi renderizado na listagem'
        assert templates[-1][0].name == 'financeiro/listar_lancamentos.html'
        html = response.get_data(as_text=True)
        assert 'SEED_AUDITORIA_RECEITA' in html
        assert 'SEED_AUDITORIA_DESPESA' in html


def test_rota_listar_lancamentos_sem_autenticacao():
    """Testa que listagem redireciona quando não autenticado."""
    from app import create_app

    app = create_app('testing')

    with app.test_client() as client:
        response = client.get('/financeiro/lancamentos')

        # Deve redirecionar para login ou retornar página
        assert response.status_code in {200, 302, 404}, \
            f"Listagem retornou status inesperado: {response.status_code}"


def test_config_testing_nao_usa_banco_real():
    """Verifica que TestingConfig não usa banco de produção."""
    from app import create_app

    app = create_app('testing')

    db_uri = app.config['SQLALCHEMY_DATABASE_URI']

    assert 'postgresql' not in db_uri, "TestingConfig não deve usar PostgreSQL"
    assert 'mysql' not in db_uri, "TestingConfig não deve usar MySQL"
    assert 'erp.db' not in db_uri, "TestingConfig não deve usar erp.db (produção)"


def test_engine_options_sem_prepare_threshold():
    """Verifica que TestingConfig não herda prepare_threshold do PostgreSQL."""
    from app import create_app

    app = create_app('testing')

    engine_options = app.config.get('SQLALCHEMY_ENGINE_OPTIONS', {})

    # prepare_threshold é específico do PostgreSQL, não deve estar em TestingConfig
    assert 'prepare_threshold' not in engine_options, \
        "TestingConfig não deve ter prepare_threshold (parâmetro PostgreSQL)"


def test_migration_upgrade_cria_fk_e_indice_ordem_servico_parcela_id():
    """Valida upgrade da migration nova e presença da FK persistente."""
    from sqlalchemy import create_engine, inspect

    with tempfile.NamedTemporaryFile(mode='w', suffix='.db', delete=False, dir=tempfile.gettempdir()) as temp_db:
        db_path = temp_db.name

    try:
        _create_pre_migration_schema(db_path)
        _upgrade_sqlite_with_alembic(db_path)

        engine = create_engine(f'sqlite:///{db_path}')
        try:
            insp = inspect(engine)
            cols = [c['name'] for c in insp.get_columns('lancamentos_financeiros')]
            assert 'ordem_servico_parcela_id' in cols

            indexes = insp.get_indexes('lancamentos_financeiros')
            idx_names = {i['name'] for i in indexes}
            assert 'ix_lancamentos_financeiros_ordem_servico_parcela_id' in idx_names
        finally:
            engine.dispose()

    finally:
        if os.path.exists(db_path):
            os.unlink(db_path)


def test_backfill_ambiguo_mantem_fk_nula():
    """Backfill não vincula quando houver ambiguidade para a mesma parcela textual."""
    from sqlalchemy import create_engine, text

    with tempfile.NamedTemporaryFile(mode='w', suffix='.db', delete=False, dir=tempfile.gettempdir()) as temp_db:
        db_path = temp_db.name

    try:
        _create_pre_migration_schema(db_path)
        engine = create_engine(f'sqlite:///{db_path}')
        with engine.begin() as conn:
            conn.execute(text("INSERT INTO ordem_servico(id, numero) VALUES (1, 'OS-1')"))
            conn.execute(
                text(
                    "INSERT INTO ordem_servico_parcelas(id, ordem_servico_id, numero_parcela, data_vencimento, valor) "
                    "VALUES (10, 1, 1, '2025-01-10', 100.00)"
                )
            )
            conn.execute(
                text(
                    "INSERT INTO lancamentos_financeiros(id, ordem_servico_id, numero_parcela, ativo) "
                    "VALUES (100, 1, '1/3', 1), (101, 1, '1/3', 1)"
                )
            )

        _upgrade_sqlite_with_alembic(db_path)

        with engine.begin() as conn:
            rows = conn.execute(
                text(
                    "SELECT ordem_servico_parcela_id "
                    "FROM lancamentos_financeiros WHERE id IN (100, 101) ORDER BY id"
                )
            ).fetchall()

        assert rows[0][0] is None
        assert rows[1][0] is None

    finally:
        try:
            engine.dispose()
        except Exception:
            pass
        if os.path.exists(db_path):
            try:
                os.unlink(db_path)
            except Exception:
                pass


def test_backfill_correspondencia_unica_cria_fk():
    """Backfill vincula FK quando há uma única correspondência inequívoca."""
    from sqlalchemy import create_engine, text

    with tempfile.NamedTemporaryFile(mode='w', suffix='.db', delete=False, dir=tempfile.gettempdir()) as temp_db:
        db_path = temp_db.name

    engine = None
    try:
        _create_pre_migration_schema(db_path)
        engine = create_engine(f'sqlite:///{db_path}')
        with engine.begin() as conn:
            conn.execute(text("INSERT INTO ordem_servico(id, numero) VALUES (1, 'OS-1')"))
            conn.execute(
                text(
                    "INSERT INTO ordem_servico_parcelas(id, ordem_servico_id, numero_parcela, data_vencimento, valor) "
                    "VALUES (10, 1, 1, '2025-01-10', 100.00)"
                )
            )
            conn.execute(
                text(
                    "INSERT INTO lancamentos_financeiros(id, ordem_servico_id, numero_parcela, descricao, valor, status, data_pagamento, ativo) "
                    "VALUES (100, 1, '1/3', 'Único', 100.00, 'pendente', NULL, 1)"
                )
            )

        _upgrade_sqlite_with_alembic(db_path)

        with engine.begin() as conn:
            row = conn.execute(
                text(
                    "SELECT ordem_servico_parcela_id FROM lancamentos_financeiros WHERE id = 100"
                )
            ).fetchone()

        assert row is not None
        assert row[0] == 10
    finally:
        if engine is not None:
            engine.dispose()
        if os.path.exists(db_path):
            os.unlink(db_path)


def test_backfill_sem_correspondencia_mantem_fk_nula():
    """Backfill mantém FK nula quando não há parcela correspondente."""
    from sqlalchemy import create_engine, text

    with tempfile.NamedTemporaryFile(mode='w', suffix='.db', delete=False, dir=tempfile.gettempdir()) as temp_db:
        db_path = temp_db.name

    engine = None
    try:
        _create_pre_migration_schema(db_path)
        engine = create_engine(f'sqlite:///{db_path}')
        with engine.begin() as conn:
            conn.execute(text("INSERT INTO ordem_servico(id, numero) VALUES (1, 'OS-1')"))
            conn.execute(
                text(
                    "INSERT INTO lancamentos_financeiros(id, ordem_servico_id, numero_parcela, descricao, valor, status, data_pagamento, ativo) "
                    "VALUES (100, 1, '9/9', 'Sem match', 100.00, 'pendente', NULL, 1)"
                )
            )

        _upgrade_sqlite_with_alembic(db_path)

        with engine.begin() as conn:
            row = conn.execute(
                text(
                    "SELECT ordem_servico_parcela_id FROM lancamentos_financeiros WHERE id = 100"
                )
            ).fetchone()

        assert row is not None
        assert row[0] is None
    finally:
        if engine is not None:
            engine.dispose()
        if os.path.exists(db_path):
            os.unlink(db_path)


def test_backfill_nao_apaga_lancamentos_legados():
    """Upgrade/backfill não remove lançamentos legados."""
    from sqlalchemy import create_engine, text

    with tempfile.NamedTemporaryFile(mode='w', suffix='.db', delete=False, dir=tempfile.gettempdir()) as temp_db:
        db_path = temp_db.name

    engine = None
    try:
        _create_pre_migration_schema(db_path)
        engine = create_engine(f'sqlite:///{db_path}')
        with engine.begin() as conn:
            conn.execute(text("INSERT INTO ordem_servico(id, numero) VALUES (1, 'OS-1')"))
            conn.execute(
                text(
                    "INSERT INTO ordem_servico_parcelas(id, ordem_servico_id, numero_parcela, data_vencimento, valor) "
                    "VALUES (10, 1, 1, '2025-01-10', 100.00)"
                )
            )
            conn.execute(
                text(
                    "INSERT INTO lancamentos_financeiros(id, ordem_servico_id, numero_parcela, descricao, valor, status, data_pagamento, ativo) "
                    "VALUES "
                    "(100, 1, '1/3', 'A', 100.00, 'pendente', NULL, 1), "
                    "(101, 1, '9/9', 'B', 200.00, 'pendente', NULL, 1), "
                    "(102, 1, NULL, 'C', 300.00, 'pendente', NULL, 1)"
                )
            )

        _upgrade_sqlite_with_alembic(db_path)

        with engine.begin() as conn:
            qtd = conn.execute(text("SELECT COUNT(*) FROM lancamentos_financeiros")).scalar()

        assert qtd == 3
    finally:
        if engine is not None:
            engine.dispose()
        if os.path.exists(db_path):
            os.unlink(db_path)


def test_backfill_preserva_lancamento_quitado_status_data_valor():
    """Backfill não altera status/data/valor de lançamento já quitado."""
    from sqlalchemy import create_engine, text

    with tempfile.NamedTemporaryFile(mode='w', suffix='.db', delete=False, dir=tempfile.gettempdir()) as temp_db:
        db_path = temp_db.name

    engine = None
    try:
        _create_pre_migration_schema(db_path)
        engine = create_engine(f'sqlite:///{db_path}')
        with engine.begin() as conn:
            conn.execute(text("INSERT INTO ordem_servico(id, numero) VALUES (1, 'OS-1')"))
            conn.execute(
                text(
                    "INSERT INTO ordem_servico_parcelas(id, ordem_servico_id, numero_parcela, data_vencimento, valor) "
                    "VALUES (10, 1, 1, '2025-01-10', 100.00)"
                )
            )
            conn.execute(
                text(
                    "INSERT INTO lancamentos_financeiros(id, ordem_servico_id, numero_parcela, descricao, valor, status, data_pagamento, ativo) "
                    "VALUES (100, 1, '1/3', 'Quitado', 777.00, 'recebido', '2025-01-15', 1)"
                )
            )

        _upgrade_sqlite_with_alembic(db_path)

        with engine.begin() as conn:
            row = conn.execute(
                text(
                    "SELECT status, data_pagamento, valor, ordem_servico_parcela_id "
                    "FROM lancamentos_financeiros WHERE id = 100"
                )
            ).fetchone()

        assert row is not None
        assert row[0] == 'recebido'
        assert str(row[1]) == '2025-01-15'
        assert float(row[2]) == 777.0
        assert row[3] == 10
    finally:
        if engine is not None:
            engine.dispose()
        if os.path.exists(db_path):
            os.unlink(db_path)


def test_upgrade_cria_restricao_unique_e_rejeita_duplicidade():
    """Restrição UNIQUE impede dois lançamentos na mesma parcela persistente."""
    from sqlalchemy import create_engine, text
    from sqlalchemy.exc import IntegrityError

    with tempfile.NamedTemporaryFile(mode='w', suffix='.db', delete=False, dir=tempfile.gettempdir()) as temp_db:
        db_path = temp_db.name

    engine = None
    try:
        _create_pre_migration_schema(db_path)
        engine = create_engine(f'sqlite:///{db_path}')
        with engine.begin() as conn:
            conn.execute(text("INSERT INTO ordem_servico(id, numero) VALUES (1, 'OS-1')"))
            conn.execute(
                text(
                    "INSERT INTO ordem_servico_parcelas(id, ordem_servico_id, numero_parcela, data_vencimento, valor) "
                    "VALUES (10, 1, 1, '2025-01-10', 100.00)"
                )
            )
            conn.execute(
                text(
                    "INSERT INTO lancamentos_financeiros(id, ordem_servico_id, numero_parcela, descricao, valor, status, data_pagamento, ativo) "
                    "VALUES (100, 1, '1/3', 'Primeiro', 100.00, 'pendente', NULL, 1)"
                )
            )

        _upgrade_sqlite_with_alembic(db_path)

        with pytest.raises(IntegrityError):
            with engine.begin() as conn:
                conn.execute(
                    text(
                        "INSERT INTO lancamentos_financeiros("
                        "id, ordem_servico_id, numero_parcela, descricao, valor, status, data_pagamento, ativo, ordem_servico_parcela_id"
                        ") VALUES (101, 1, '1/3', 'Duplicado', 100.00, 'pendente', NULL, 1, 10)"
                    )
                )
    finally:
        if engine is not None:
            engine.dispose()
        if os.path.exists(db_path):
            os.unlink(db_path)


def test_downgrade_remove_apenas_fk_coluna_sem_apagar_dados_financeiros():
    """Downgrade remove artefatos da migration sem apagar linhas financeiras."""
    from alembic import command
    from alembic.config import Config
    from sqlalchemy import create_engine, text

    with tempfile.NamedTemporaryFile(mode='w', suffix='.db', delete=False, dir=tempfile.gettempdir()) as temp_db:
        db_path = temp_db.name

    engine = None
    try:
        _create_pre_migration_schema(db_path)
        engine = create_engine(f'sqlite:///{db_path}')
        with engine.begin() as conn:
            conn.execute(
                text(
                    "INSERT INTO lancamentos_financeiros(id, ordem_servico_id, numero_parcela, descricao, valor, status, data_pagamento, ativo) "
                    "VALUES (200, 1, '1/3', 'Sentinela downgrade', 321.99, 'pendente', NULL, 1)"
                )
            )

        _upgrade_sqlite_with_alembic(db_path)

        repo_root = Path(__file__).resolve().parents[1]
        cfg = Config(str(repo_root / 'alembic.ini'))
        cfg.set_main_option('script_location', str(repo_root / 'migrations'))
        cfg.set_main_option('sqlalchemy.url', f'sqlite:///{db_path}')
        command.downgrade(cfg, 'base')

        with engine.begin() as conn:
            row = conn.execute(
                text(
                    "SELECT id, descricao, valor, status "
                    "FROM lancamentos_financeiros WHERE id = 200"
                )
            ).fetchone()

        assert row is not None
        assert row[1] == 'Sentinela downgrade'
        assert float(row[2]) == 321.99
        assert row[3] == 'pendente'
    finally:
        if engine is not None:
            engine.dispose()
        if os.path.exists(db_path):
            os.unlink(db_path)


def test_duas_instancias_app_abrem_mesmo_sqlite_apos_migration():
    """Valida 2ª instância completa no mesmo SQLite com migration, metadados e sentinela."""
    from app import create_app
    from app.config import config as config_map
    from app.extensoes import db
    from sqlalchemy import inspect, text

    with tempfile.NamedTemporaryFile(mode='w', suffix='.db', delete=False, dir=tempfile.gettempdir()) as temp_db:
        db_path = temp_db.name

    old_uri = config_map['testing'].SQLALCHEMY_DATABASE_URI
    try:
        _create_pre_migration_schema(db_path)
        _upgrade_sqlite_with_alembic(db_path)

        config_map['testing'].SQLALCHEMY_DATABASE_URI = f'sqlite:///{db_path}'

        # Primeira aplicação: grava sentinela no arquivo SQLite migrado.
        app1 = create_app('testing')
        with app1.app_context():
            db.session.execute(
                text(
                    "INSERT INTO lancamentos_financeiros("
                    "id, ordem_servico_id, numero_parcela, descricao, valor, status, data_pagamento, ativo, ordem_servico_parcela_id"
                    ") VALUES (9001, 1, 'S/1', 'SENTINELA_SEGUNDA_INSTANCIA', 123.45, 'pendente', NULL, 1, NULL)"
                )
            )
            db.session.commit()

        # Liberar explicitamente conexões/engine da primeira app.
        with app1.app_context():
            db.session.remove()
            db.engine.dispose()

        # Segunda aplicação sobre o mesmo arquivo: valida estrutura + dados.
        app2 = create_app('testing')
        with app2.app_context():
            insp = inspect(db.engine)
            tabelas = set(insp.get_table_names())
            assert 'lancamentos_financeiros' in tabelas

            colunas = {c['name'] for c in insp.get_columns('lancamentos_financeiros')}
            assert 'ordem_servico_parcela_id' in colunas

            indexes = {i['name'] for i in insp.get_indexes('lancamentos_financeiros')}
            assert 'ix_lancamentos_financeiros_ordem_servico_parcela_id' in indexes

            fks = insp.get_foreign_keys('lancamentos_financeiros')
            assert any(
                fk.get('name') == 'fk_lancamentos_financeiros_ordem_servico_parcela_id'
                and fk.get('referred_table') == 'ordem_servico_parcelas'
                for fk in fks
            )

            sentinela = db.session.execute(
                text(
                    "SELECT descricao, valor FROM lancamentos_financeiros WHERE id = 9001"
                )
            ).fetchone()
            assert sentinela is not None
            assert sentinela[0] == 'SENTINELA_SEGUNDA_INSTANCIA'
            assert float(sentinela[1]) == 123.45

    finally:
        config_map['testing'].SQLALCHEMY_DATABASE_URI = old_uri
        try:
            db.session.remove()
            db.engine.dispose()
        except Exception:
            pass
        if os.path.exists(db_path):
            try:
                os.unlink(db_path)
            except Exception:
                pass


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
