# -*- coding: utf-8 -*-
"""Regressao do saldo bancario transacional."""
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
from app.financeiro.financeiro_model import ContaBancaria, LancamentoFinanceiro


def dinheiro(valor):
    return Decimal(str(valor)).quantize(Decimal('0.01'))


def saldo(conta):
    db.session.expire(conta, ['saldo_atual'])
    return dinheiro(conta.saldo_atual)


def executar_testes():
    configuracao_utils.get_config = lambda: None
    app = create_app('testing')

    with app.app_context():
        assert db.engine.url.drivername == 'sqlite'
        assert db.engine.url.database == ':memory:'
        db.create_all()

        conta = ContaBancaria(
            nome='Cora Teste',
            tipo='conta_corrente',
            saldo_inicial=dinheiro('1000.00'),
            saldo_atual=dinheiro('1000.00'),
            limite_credito=dinheiro('0.00'),
            ativa=True,
            principal=False,
            ativo=True,
        )
        db.session.add(conta)
        db.session.commit()
        assert saldo(conta) == dinheiro('1000.00')

        # 1) Lançamento que ja nasce recebido movimenta a conta.
        receita = LancamentoFinanceiro(
            descricao='TEST_SALDO_ReceitaRecebida',
            valor=dinheiro('100.00'),
            tipo='receita',
            status='recebido',
            data_lancamento=date(2026, 9, 7),
            data_pagamento=date(2026, 9, 7),
            conta_bancaria_id=conta.id,
            categoria='Teste',
            ativo=True,
        )
        db.session.add(receita)
        db.session.commit()
        assert saldo(conta) == dinheiro('1100.00')

        # 2) Pendente nao mexe; ao virar pago, movimenta uma vez.
        despesa = LancamentoFinanceiro(
            descricao='TEST_SALDO_DespesaPendente',
            valor=dinheiro('50.00'),
            tipo='despesa',
            status='pendente',
            data_lancamento=date(2026, 9, 7),
            conta_bancaria_id=conta.id,
            categoria='Teste',
            ativo=True,
        )
        db.session.add(despesa)
        db.session.commit()
        assert saldo(conta) == dinheiro('1100.00')

        despesa.status = 'pago'
        despesa.data_pagamento = date(2026, 9, 7)
        db.session.commit()
        assert saldo(conta) == dinheiro('1050.00')

        # 3) Editar valor de quitado aplica somente a diferenca.
        despesa.valor = dinheiro('70.00')
        db.session.commit()
        assert saldo(conta) == dinheiro('1030.00')

        # 4) Soft delete estorna o impacto financeiro.
        despesa.ativo = False
        db.session.commit()
        assert saldo(conta) == dinheiro('1100.00')

        # 5) Metodo legado marcar_como_pago ja atualiza a conta; evento nao duplica.
        despesa_metodo = LancamentoFinanceiro(
            descricao='TEST_SALDO_MetodoLegado',
            valor=dinheiro('40.00'),
            tipo='conta_pagar',
            status='pendente',
            data_lancamento=date(2026, 9, 7),
            conta_bancaria_id=conta.id,
            categoria='Teste',
            ativo=True,
        )
        db.session.add(despesa_metodo)
        db.session.commit()
        despesa_metodo.marcar_como_pago(data_pagamento=date(2026, 9, 7))
        assert saldo(conta) == dinheiro('1060.00')

        # 6) Transferencia e ignorada porque a rota propria ja ajusta saldos.
        transferencia = LancamentoFinanceiro(
            descricao='TEST_SALDO_Transferencia',
            valor=dinheiro('30.00'),
            tipo='despesa',
            status='pago',
            data_lancamento=date(2026, 9, 7),
            data_pagamento=date(2026, 9, 7),
            conta_bancaria_id=conta.id,
            categoria='Transferência Bancária',
            ativo=True,
        )
        db.session.add(transferencia)
        db.session.commit()
        assert saldo(conta) == dinheiro('1060.00')

        # 7) Recebimento novo de OS, sem seletor de conta, usa a unica conta ativa.
        recebimento_os = LancamentoFinanceiro(
            descricao='TEST_SALDO_OS_Nova',
            valor=dinheiro('25.00'),
            tipo='conta_receber',
            status='recebido',
            data_lancamento=date(2026, 9, 7),
            data_pagamento=date(2026, 9, 7),
            origem='ORDEM_SERVICO',
            categoria='Serviços',
            ativo=True,
        )
        db.session.add(recebimento_os)
        db.session.commit()
        assert recebimento_os.conta_bancaria_id == conta.id
        assert saldo(conta) == dinheiro('1085.00')

        # 8) Recebimento historico ja quitado nao e retrovinculado por mera edicao.
        conta.ativa = False
        db.session.commit()
        legado = LancamentoFinanceiro(
            descricao='TEST_SALDO_OS_Legado',
            valor=dinheiro('200.00'),
            tipo='conta_receber',
            status='recebido',
            data_lancamento=date(2026, 8, 1),
            data_pagamento=date(2026, 8, 1),
            origem='ORDEM_SERVICO',
            categoria='Serviços',
            ativo=True,
        )
        db.session.add(legado)
        db.session.commit()
        assert legado.conta_bancaria_id is None
        assert saldo(conta) == dinheiro('1085.00')

        conta.ativa = True
        db.session.commit()
        legado.descricao = 'TEST_SALDO_OS_Legado_Editado'
        db.session.commit()
        assert legado.conta_bancaria_id is None
        assert saldo(conta) == dinheiro('1085.00')

    print('SALDO BANCARIO TRANSACIONAL: OK')


if __name__ == '__main__':
    executar_testes()
