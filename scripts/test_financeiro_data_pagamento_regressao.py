# -*- coding: utf-8 -*-
"""Regressão para impedir lançamentos quitados sem data de pagamento."""
import os
import sys
from datetime import date
from decimal import Decimal

os.environ['FLASK_CONFIG'] = 'testing'
os.environ['FLASK_ENV'] = 'testing'
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.app import create_app
from app.configuracao import configuracao_utils
from app.extensoes import db
from app.financeiro.financeiro_model import LancamentoFinanceiro
from app.financeiro.indicadores_service import periodo_mes_ano, resumir_financeiro_periodo


def criar_payload(descricao, tipo, status, data_lancamento, **extra):
    payload = {
        'descricao': descricao,
        'valor': '100,00',
        'tipo': tipo,
        'categoria': 'Teste',
        'status': status,
        'data_lancamento': data_lancamento,
    }
    payload.update(extra)
    return payload


def executar_testes():
    configuracao_utils.get_config = lambda: None
    app = create_app('testing')
    client = app.test_client()
    with app.app_context():
        assert db.engine.url.drivername == 'sqlite'
        assert db.engine.url.database == ':memory:'
        db.create_all()

        client.post('/financeiro/lancamentos/criar', data=criar_payload(
            'TEST_DATAPGTO_CriarPago', 'despesa', 'pago', '2026-09-02'))
        pago = LancamentoFinanceiro.query.filter_by(descricao='TEST_DATAPGTO_CriarPago').one()
        assert pago.data_pagamento == date(2026, 9, 2)

        client.post('/financeiro/lancamentos/criar', data=criar_payload(
            'TEST_DATAPGTO_CriarRecebido', 'receita', 'recebido', '2026-09-02', data_pagamento='2026-09-03'))
        recebido = LancamentoFinanceiro.query.filter_by(descricao='TEST_DATAPGTO_CriarRecebido').one()
        assert recebido.data_pagamento == date(2026, 9, 3)

        client.post('/financeiro/lancamentos/criar', data=criar_payload(
            'TEST_DATAPGTO_CriarPendente', 'conta_pagar', 'pendente', '2026-09-02'))
        pendente = LancamentoFinanceiro.query.filter_by(descricao='TEST_DATAPGTO_CriarPendente').one()
        assert pendente.data_pagamento is None

        client.post(f'/financeiro/lancamentos/{pendente.id}/atualizar', data=criar_payload(
            pendente.descricao, 'conta_pagar', 'pago', '2026-09-04'))
        db.session.refresh(pendente)
        assert pendente.data_pagamento == date(2026, 9, 4)

        recebimento_edicao = LancamentoFinanceiro(
            descricao='TEST_DATAPGTO_EditarRecebido', valor=Decimal('100.00'), tipo='receita',
            status='pendente', data_lancamento=date(2026, 9, 2), ativo=True)
        db.session.add(recebimento_edicao)
        db.session.commit()
        client.post(f'/financeiro/lancamentos/{recebimento_edicao.id}/atualizar', data=criar_payload(
            recebimento_edicao.descricao, 'receita', 'recebido', '2026-09-04'))
        db.session.refresh(recebimento_edicao)
        assert recebimento_edicao.data_pagamento == date(2026, 9, 4)

        data_original = recebido.data_pagamento
        client.post(f'/financeiro/lancamentos/{recebido.id}/atualizar', data=criar_payload(
            recebido.descricao, 'receita', 'recebido', '2026-09-04'))
        db.session.refresh(recebido)
        assert recebido.data_pagamento == data_original

        baixa_sem_data = LancamentoFinanceiro(
            descricao='TEST_DATAPGTO_BaixaSemData', valor=Decimal('100.00'), tipo='despesa',
            status='pendente', data_lancamento=date(2026, 9, 2), ativo=True)
        db.session.add(baixa_sem_data)
        db.session.commit()
        try:
            baixa_sem_data.marcar_como_pago()
            raise AssertionError('Baixa sem data deveria ser rejeitada')
        except ValueError:
            db.session.rollback()
        db.session.refresh(baixa_sem_data)
        assert baixa_sem_data.status == 'pendente'
        assert baixa_sem_data.data_pagamento is None

        try:
            baixa_sem_data.marcar_como_pago(data_pagamento='2026-09-02')
            raise AssertionError('Baixa com data inválida deveria ser rejeitada')
        except ValueError:
            db.session.rollback()
        db.session.refresh(baixa_sem_data)
        assert baixa_sem_data.status == 'pendente'

        inicio, fim = periodo_mes_ano(9, 2026)
        resumo = resumir_financeiro_periodo(inicio, fim)
        assert resumo.despesas_realizadas >= Decimal('200.00')
        assert resumo.receitas_realizadas >= Decimal('200.00')
        assert resumo.lancamentos_pagos_sem_data_qtd == 0
    print('REGRESSAO DATA_PAGAMENTO: OK')


if __name__ == '__main__':
    executar_testes()