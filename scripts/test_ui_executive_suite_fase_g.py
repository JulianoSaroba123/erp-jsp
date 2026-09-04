# -*- coding: utf-8 -*-
"""Regressao visual da Fase G: contratos da interface Financeiro."""
import os
import sys
from datetime import date
from decimal import Decimal

os.environ['FLASK_CONFIG'] = 'testing'
os.environ['FLASK_ENV'] = 'testing'
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.app import create_app
from app.auth.usuario_model import Usuario
from app.configuracao import configuracao_utils
from app.extensoes import db
from app.financeiro.financeiro_model import LancamentoFinanceiro


def executar_testes():
    configuracao_utils.get_config = lambda: None
    app = create_app('testing')
    client = app.test_client()
    with app.app_context():
        db.create_all()
        admin = Usuario(nome='Admin Fase G', email='admin_faseg@example.com', usuario='admin_faseg', tipo_usuario='admin', ativo=True, email_confirmado=True, primeiro_login=False)
        admin.set_senha('SenhaForte123!')
        lancamento = LancamentoFinanceiro(descricao='TEST_FASEG_Lancamento', valor=Decimal('100.00'), tipo='conta_pagar', status='pendente', categoria='Teste', data_lancamento=date.today(), data_vencimento=date.today(), ativo=True)
        db.session.add_all([admin, lancamento])
        db.session.commit()
        lancamento_id = lancamento.id

    client.post('/auth/login', data={'identificador': 'admin_faseg', 'senha': 'SenhaForte123!'})
    paginas = {
        '/financeiro/': ('jsp-executive-suite-phase-g.css', 'id="valor-receitas"', 'id="graficoPizza"', 'id="graficoBarras"', 'id="graficoFluxoCaixa"', 'id="graficoCategorias"', 'FINANCEIRO_DASHBOARD_MES'),
        '/financeiro/?mes=1&ano=2026': ('Mês Atual', 'name="mes"', 'name="ano"'),
        '/financeiro/lancamentos?tipo=conta_pagar&status=pendente': ('cc-filter-bar', 'cc-table', 'name="tipo"', 'name="status"', 'id="modalPagamento"', 'id="formPagamento"'),
        '/financeiro/lancamentos/novo': ('cc-form-card', 'id="descricao"', 'id="valor"', 'id="tipo"', 'id="status"', 'id="conta_bancaria_id"', 'id="centro_custo_id"'),
        f'/financeiro/lancamentos/{lancamento_id}/editar': ('TEST_FASEG_Lancamento', 'id="descricao"', 'id="valor"', 'id="forma_pagamento"'),
        '/financeiro/contas-pagar': ('Contas a Pagar', 'id="modalPagamento"'),
        '/financeiro/contas-receber': ('Contas a Receber', 'id="modalRecebimento"'),
        '/financeiro/conciliacao-bancaria': ('Conciliação Bancária',),
        '/financeiro/fluxo-caixa': ('Fluxo de Caixa Projetado', 'id="chartFluxoCaixa"'),
        '/financeiro/dre': ('Demonstrativo de Resultados', 'id="chartEvolucao"'),
    }
    for url, expected in paginas.items():
        response = client.get(url)
        assert response.status_code == 200, (url, response.status_code)
        html = response.get_data(as_text=True)
        for marker in expected:
            assert marker in html, (url, marker)
    print('FASE G: Financeiro OK')


if __name__ == '__main__':
    executar_testes()
