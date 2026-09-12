# -*- coding: utf-8 -*-
"""
Regressao da conciliacao bancaria quando um lancamento nao possui data_vencimento.

Cenario:
- conta bancaria ativa;
- lancamento financeiro ativo ligado a conta;
- data_vencimento = None;
- data_lancamento preenchida.

Comportamento esperado:
- a rota /financeiro/conciliacao-bancaria carrega normalmente;
- a tela nao quebra com None.strftime();
- a data_lancamento e usada como fallback visual.
"""

import os
import sys
from datetime import date
from decimal import Decimal
from types import SimpleNamespace

os.environ["FLASK_CONFIG"] = "testing"
os.environ["FLASK_ENV"] = "testing"

sys.path.insert(
    0,
    os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "..")
    ),
)

from flask import g

from app.app import create_app
from app.extensoes import db
from app.financeiro.financeiro_model import (
    ContaBancaria,
    LancamentoFinanceiro,
)


def _login_admin(app):
    client = app.test_client()
    admin = SimpleNamespace(
    id=1,
    tipo_usuario="admin",
    is_authenticated=True,
    tem_permissao=lambda *args, **kwargs: True,
)

    @app.before_request
    def load_test_admin():
        g._login_user = admin

    return client


def test_conciliacao_aceita_lancamento_sem_data_vencimento():
    app = create_app("testing")

    with app.app_context():
        db.create_all()

        conta = ContaBancaria(
            nome="Conta Teste Conciliacao",
            tipo="conta_corrente",
            saldo_inicial=Decimal("0.00"),
            saldo_atual=Decimal("0.00"),
            limite_credito=Decimal("0.00"),
            ativa=True,
            principal=False,
            ativo=True,
        )
        db.session.add(conta)
        db.session.flush()

        lancamento = LancamentoFinanceiro(
            descricao="Lancamento sem vencimento",
            valor=Decimal("125.00"),
            tipo="despesa",
            status="pendente",
            data_lancamento=date(2026, 9, 12),
            data_vencimento=None,
            conta_bancaria_id=conta.id,
            categoria="Teste",
            ativo=True,
        )
        db.session.add(lancamento)
        db.session.commit()

        conta_id = conta.id

    client = _login_admin(app)

    response = client.get(
        f"/financeiro/conciliacao-bancaria?conta_id={conta_id}",
        follow_redirects=False,
    )

    assert response.status_code == 200

    body = response.get_data(as_text=True)

    assert "Lancamento sem vencimento" in body
    assert "12/09/2026" in body


if __name__ == "__main__":
    test_conciliacao_aceita_lancamento_sem_data_vencimento()
    print("CONCILIACAO NONE STRFTIME: OK")
