# -*- coding: utf-8 -*-
"""Regressão da idempotência da importação bancária Cora."""

import os
import sys
from datetime import date
from decimal import Decimal

sys.path.insert(
    0,
    os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")),
)

os.environ["FLASK_CONFIG"] = "testing"
os.environ["FLASK_ENV"] = "testing"

from sqlalchemy.exc import IntegrityError

from app.app import create_app
from app.extensoes import db
from app.financeiro.financeiro_model import ContaBancaria, ExtratoBancario


FINGERPRINT = "a" * 64
FITID = "cora-fitid-001"


def _nova_conta(nome):
    conta = ContaBancaria(
        nome=nome,
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
    return conta


def _novo_extrato(conta_id, fingerprint, fitid):
    return ExtratoBancario(
        conta_bancaria_id=conta_id,
        data_movimento=date(2026, 9, 11),
        descricao="Compra no débito",
        documento="",
        valor=Decimal("20.40"),
        tipo_movimento="debito",
        arquivo_origem="teste.ofx",
        identificador_externo=fitid,
        fingerprint_importacao=fingerprint,
        ativo=True,
    )


def _commit_deve_falhar_por_unicidade(extrato):
    db.session.add(extrato)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return
    raise AssertionError("Duplicidade deveria ter sido bloqueada pelo banco.")


def test_idempotencia_extrato_bancario():
    app = create_app("testing")

    with app.app_context():
        db.drop_all()
        db.create_all()

        conta_1 = _nova_conta("Cora Teste 1")
        conta_2 = _nova_conta("Cora Teste 2")
        db.session.commit()

        primeiro = _novo_extrato(conta_1.id, FINGERPRINT, FITID)
        db.session.add(primeiro)
        db.session.commit()

        encontrado = ExtratoBancario.buscar_duplicado_importacao(
            conta_id=conta_1.id,
            fingerprint=FINGERPRINT,
        )
        assert encontrado is not None
        assert encontrado.id == primeiro.id

        encontrado_fitid = ExtratoBancario.buscar_duplicado_importacao(
            conta_id=conta_1.id,
            identificador_externo=FITID,
        )
        assert encontrado_fitid is not None
        assert encontrado_fitid.id == primeiro.id

        _commit_deve_falhar_por_unicidade(
            _novo_extrato(conta_1.id, FINGERPRINT, "cora-fitid-outro")
        )

        _commit_deve_falhar_por_unicidade(
            _novo_extrato(conta_1.id, "b" * 64, FITID)
        )

        outra_conta = _novo_extrato(conta_2.id, FINGERPRINT, FITID)
        db.session.add(outra_conta)
        db.session.commit()
        assert outra_conta.id is not None

        legado_1 = _novo_extrato(conta_1.id, None, None)
        legado_1.descricao = "Legado 1"
        legado_2 = _novo_extrato(conta_1.id, None, None)
        legado_2.descricao = "Legado 2"
        db.session.add_all([legado_1, legado_2])
        db.session.commit()

        assert ExtratoBancario.buscar_duplicado_importacao(
            conta_id=conta_1.id,
            fingerprint=None,
            identificador_externo=None,
        ) is None


if __name__ == "__main__":
    test_idempotencia_extrato_bancario()
    print("IMPORTACAO CORA IDEMPOTENCIA: OK")
