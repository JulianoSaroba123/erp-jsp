# -*- coding: utf-8 -*-
"""
D25F01-A3

Homologacao do caso real MR Jacky na conciliacao bancaria N:N.

Caso:
- 1 PIX: R$ 990,00
- OS20260082: R$ 450,00
- OS20260084: R$ 540,00

Usa:
- models reais do ERP
- db.session real do ERP
- conciliacao_adapter real
- SQLite exclusivamente em memoria

Nao executa app/__init__.py.
Nao toca no erp.db.
"""

from __future__ import annotations

import runpy
from datetime import date
from decimal import Decimal
from pathlib import Path

from flask import Flask


ROOT = Path(__file__).resolve().parents[2]

BASE = runpy.run_path(
    str(
        ROOT
        / "tests"
        / "financeiro"
        / "homologacao_conciliacao_adapter_a24.py"
    ),
    run_name="d25f01_a24_bootstrap",
)

db = BASE["db"]
ContaBancaria = BASE["ContaBancaria"]
ExtratoBancario = BASE["ExtratoBancario"]
LancamentoFinanceiro = BASE["LancamentoFinanceiro"]
ConciliacaoBancariaItem = BASE["ConciliacaoBancariaItem"]
SolicitacaoAlocacao = BASE["SolicitacaoAlocacao"]
executar_conciliacao_bancaria = BASE[
    "executar_conciliacao_bancaria"
]
sha256_arquivo = BASE["sha256_arquivo"]

ERP_DB = ROOT / "erp.db"


def executar_homologacao():
    hash_antes = sha256_arquivo(ERP_DB)

    app = Flask("d25f01_a3_mr_jacky")

    app.config.update(
        TESTING=True,
        SQLALCHEMY_DATABASE_URI="sqlite:///:memory:",
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
    )

    db.init_app(app)

    with app.app_context():
        print("=== D25F01-A3 | MR JACKY ===")
        print(f"Banco: {db.engine.url}")

        assert str(db.engine.url) == "sqlite:///:memory:"

        db.create_all()

        conta = ContaBancaria(
            nome="Cora - Homologacao A3",
            tipo="conta_corrente",
            banco="Cora",
            saldo_inicial=Decimal("0.00"),
            saldo_atual=Decimal("0.00"),
            ativa=True,
        )

        db.session.add(conta)
        db.session.flush()

        os_82 = LancamentoFinanceiro(
            descricao="MR Jacky - OS20260082",
            numero_documento="OS20260082",
            valor=Decimal("450.00"),
            tipo="conta_receber",
            status="pendente",
            data_lancamento=date(2026, 9, 17),
            conta_bancaria_id=conta.id,
            origem="ORDEM_SERVICO",
        )

        os_84 = LancamentoFinanceiro(
            descricao="MR Jacky - OS20260084",
            numero_documento="OS20260084",
            valor=Decimal("540.00"),
            tipo="conta_receber",
            status="pendente",
            data_lancamento=date(2026, 9, 17),
            conta_bancaria_id=conta.id,
            origem="ORDEM_SERVICO",
        )

        db.session.add_all([os_82, os_84])
        db.session.flush()

        extrato = ExtratoBancario(
            conta_bancaria_id=conta.id,
            data_movimento=date(2026, 9, 17),
            descricao="PIX MR JACKY",
            documento="PIX-MR-JACKY-990",
            valor=Decimal("990.00"),
            tipo_movimento="credito",
            conciliado=False,
        )

        db.session.add(extrato)
        db.session.commit()

        extrato_id = extrato.id
        os_82_id = os_82.id
        os_84_id = os_84.id
        conta_id = conta.id

        resultado = executar_conciliacao_bancaria(
            extrato_id=extrato_id,
            alocacoes=[
                SolicitacaoAlocacao(
                    lancamento_id=os_82_id,
                    valor=Decimal("450.00"),
                ),
                SolicitacaoAlocacao(
                    lancamento_id=os_84_id,
                    valor=Decimal("540.00"),
                ),
            ],
            usuario="D25F01-A3",
            observacoes=(
                "Caso real MR Jacky: "
                "PIX 990 = OS20260082 450 + OS20260084 540"
            ),
        )

        db.session.expire_all()

        itens = (
            db.session.query(ConciliacaoBancariaItem)
            .filter(
                ConciliacaoBancariaItem.extrato_id == extrato_id,
                ConciliacaoBancariaItem.ativo.is_(True),
            )
            .order_by(
                ConciliacaoBancariaItem.lancamento_id
            )
            .all()
        )

        extrato_db = db.session.get(
            ExtratoBancario,
            extrato_id,
        )

        os_82_db = db.session.get(
            LancamentoFinanceiro,
            os_82_id,
        )

        os_84_db = db.session.get(
            LancamentoFinanceiro,
            os_84_id,
        )

        conta_db = db.session.get(
            ContaBancaria,
            conta_id,
        )

        total = sum(
            (
                Decimal(str(item.valor_conciliado))
                for item in itens
            ),
            Decimal("0.00"),
        )

        valores = {
            item.lancamento_id:
                Decimal(str(item.valor_conciliado))
            for item in itens
        }

        assert len(itens) == 2

        assert valores == {
            os_82_id: Decimal("450.00"),
            os_84_id: Decimal("540.00"),
        }

        assert total == Decimal("990.00")

        assert os_82_db.numero_documento == "OS20260082"
        assert os_84_db.numero_documento == "OS20260084"

        assert os_82_db.status == "pendente"
        assert os_84_db.status == "pendente"

        assert extrato_db.conciliado is True
        assert extrato_db.data_conciliacao is not None

        # N:N nao cabe no FK legado 1:1.
        assert extrato_db.lancamento_id is None

        # Conciliacao nao movimenta ContaBancaria.
        assert (
            Decimal(str(conta_db.saldo_atual))
            == Decimal("0.00")
        )

        print()
        print("MR Jacky:")
        print("  PIX.............. R$ 990.00")
        print("  OS20260082....... R$ 450.00")
        print("  OS20260084....... R$ 540.00")
        print()
        print(f"Itens N:N......... {len(itens)}")
        print(f"Total conciliado.. R$ {total}")
        print(
            f"Extrato conciliado {extrato_db.conciliado}"
        )
        print(
            f"FK legado......... {extrato_db.lancamento_id}"
        )
        print(
            "Status OS.......... "
            f"{os_82_db.status} / {os_84_db.status}"
        )
        print(
            "Saldo conta........ "
            f"R$ {Decimal(str(conta_db.saldo_atual))}"
        )
        print(
            "Resultado.......... "
            f"{type(resultado).__name__}"
        )

        db.session.remove()

    hash_depois = sha256_arquivo(ERP_DB)

    assert hash_antes == hash_depois, (
        "erp.db foi alterado durante o A3."
    )

    print()
    print("erp.db preservado.")
    print()
    print("D25F01-A3 MR JACKY HOMOLOGADO ✅")


if __name__ == "__main__":
    executar_homologacao()