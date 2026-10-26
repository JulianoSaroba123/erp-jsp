"""Concorrência real em PostgreSQL LOCAL descartável; nunca usa DATABASE_URL."""
from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal
from threading import Barrier

import pytest

from app.extensoes import db
from app.financeiro.financeiro_model import (
    ContaBancaria, HistoricoFinanceiro, LancamentoFinanceiro,
)
from app.financeiro.financeiro_utils import gerar_lancamento_ordem_servico
from app.ordem_servico.ordem_servico_model import OrdemServico, OrdemServicoParcela
from app.ordem_servico.recebimento_parcelas import RecebimentoParcelaInvalido
from scripts_manutencao.testes.test_pr46_os_recebimento import (
    banco_pr46, caso_jumirim_ficticio, _registrar,
    test_conciliacao_nn_extrato_existente_nao_duplica_saldo,
)

pytestmark = pytest.mark.parametrize('banco_pr46', ['postgresql'], indirect=True)


@pytest.mark.parametrize('parcelas_distintas', [False, True])
def test_recebimentos_concorrentes_com_objetos_precarregados(
    caso_jumirim_ficticio, parcelas_distintas,
):
    app, ids = caso_jumirim_ficticio
    with app.app_context():
        gerar_lancamento_ordem_servico(db.session.get(OrdemServico, ids['os']))
        if parcelas_distintas:
            _registrar(ids, parcela_id=ids['parcelas'][2], valor_recebido='7500.00')
            db.session.commit()

    barreira = Barrier(2)

    def receber(indice):
        with app.app_context():
            try:
                # Simula sessão que leu a OS antes de outra confirmar a baixa.
                ordem = db.session.get(OrdemServico, ids['os'])
                parcelas = list(ordem.parcelas)
                assert not parcelas[0].pago and not parcelas[1].pago
                alvo = indice if parcelas_distintas else 0
                barreira.wait(timeout=15)
                _registrar(
                    ids, parcela_id=ids['parcelas'][alvo],
                    valor_recebido='15000.00' if alvo == 0 else '7500.00',
                )
                db.session.commit()
                return 'recebida'
            except RecebimentoParcelaInvalido:
                db.session.rollback()
                return 'duplicada'
            finally:
                db.session.remove()

    with ThreadPoolExecutor(max_workers=2) as executor:
        resultados = list(executor.map(receber, [0, 1]))
    assert sorted(resultados) == (
        ['recebida', 'recebida'] if parcelas_distintas else ['duplicada', 'recebida']
    )
    with app.app_context():
        pagos = OrdemServicoParcela.query.filter_by(
            ordem_servico_id=ids['os'], pago=True,
        ).count()
        assert pagos == (3 if parcelas_distintas else 1)
        assert HistoricoFinanceiro.query.filter_by(acao='pagamento').count() == pagos
        assert LancamentoFinanceiro.query.filter_by(ordem_servico_id=ids['os']).count() == 3
        assert db.session.get(OrdemServico, ids['os']).status == 'iniciada'
        assert db.session.get(OrdemServico, ids['os']).status_pagamento == (
            'pago' if parcelas_distintas else 'parcial'
        )
        assert db.session.get(ContaBancaria, ids['conta']).saldo_atual == Decimal('15000.00')


def test_geracao_concorrente_idempotente(caso_jumirim_ficticio):
    app, ids = caso_jumirim_ficticio
    barreira = Barrier(2)

    def gerar(_):
        with app.app_context():
            try:
                ordem = db.session.get(OrdemServico, ids['os'])
                barreira.wait(timeout=15)
                return len(gerar_lancamento_ordem_servico(ordem))
            finally:
                db.session.remove()

    with ThreadPoolExecutor(max_workers=2) as executor:
        assert list(executor.map(gerar, [0, 1])) == [3, 3]
    with app.app_context():
        assert LancamentoFinanceiro.query.filter_by(ordem_servico_id=ids['os']).count() == 3


def test_migration_postgresql_preserva_historico(banco_pr46):
    from sqlalchemy import create_engine, text, inspect
    from alembic.migration import MigrationContext
    from alembic.operations import Operations
    from app.config import config
    from scripts_manutencao.testes.test_pr46_migration_isolada import carregar_migracao

    engine = create_engine(banco_pr46, **config['testing'].SQLALCHEMY_ENGINE_OPTIONS)
    modulo = carregar_migracao()
    try:
        with engine.begin() as conn:
            conn.execute(text('CREATE TABLE lancamentos_financeiros (id INTEGER PRIMARY KEY)'))
            conn.execute(text('INSERT INTO lancamentos_financeiros (id) VALUES (1)'))
            with Operations.context(MigrationContext.configure(conn)):
                modulo.upgrade()
                assert conn.execute(text(
                    'SELECT sem_movimentacao_bancaria FROM lancamentos_financeiros WHERE id = 1'
                )).scalar_one() is False
                conn.execute(text(
                    'UPDATE lancamentos_financeiros SET sem_movimentacao_bancaria = true'
                ))
                with pytest.raises(RuntimeError, match='Downgrade bloqueado'):
                    modulo.downgrade()
                conn.execute(text(
                    'UPDATE lancamentos_financeiros SET sem_movimentacao_bancaria = false'
                ))
                modulo.downgrade()
                assert 'sem_movimentacao_bancaria' not in {
                    c['name'] for c in inspect(conn).get_columns('lancamentos_financeiros')
                }
    finally:
        engine.dispose()
