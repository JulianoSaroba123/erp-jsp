# -*- coding: utf-8 -*-
"""Diagnostico somente leitura para divergencia do saldo da conta Cora.

Uso no Render Shell:
    python scripts_manutencao/diagnosticar_saldo_cora.py

Nao altera nenhum dado.
"""

import os
import sys
from collections import defaultdict
from decimal import Decimal

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from app import create_app
from app.financeiro.financeiro_model import ContaBancaria, LancamentoFinanceiro


def money(valor):
    return Decimal(str(valor or 0)).quantize(Decimal("0.01"))


def fmt(valor):
    return f"R$ {money(valor):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def main():
    app = create_app()
    with app.app_context():
        contas = ContaBancaria.query.filter(ContaBancaria.nome.ilike("%cora%")).all()
        if len(contas) != 1:
            raise RuntimeError(f"Esperada exatamente 1 conta Cora; encontradas {len(contas)}")

        conta = contas[0]
        print("\n" + "=" * 92)
        print("DIAGNOSTICO DE SALDO - CORA")
        print("=" * 92)
        print(
            f"Conta: id={conta.id} nome={conta.nome!r} ativa={getattr(conta, 'ativa', None)} "
            f"principal={getattr(conta, 'principal', None)}"
        )
        print(f"Saldo inicial: {fmt(conta.saldo_inicial)}")
        print(f"Saldo atual gravado: {fmt(conta.saldo_atual)}")

        vinculados = LancamentoFinanceiro.query.filter_by(
            conta_bancaria_id=conta.id,
            ativo=True,
        ).order_by(
            LancamentoFinanceiro.data_pagamento.asc().nullslast(),
            LancamentoFinanceiro.data_lancamento.asc(),
            LancamentoFinanceiro.id.asc(),
        ).all()

        quitados = [l for l in vinculados if (l.status or "").lower() in {"pago", "recebido"}]
        pendentes = [l for l in vinculados if (l.status or "").lower() == "pendente"]

        entradas = Decimal("0.00")
        saidas = Decimal("0.00")
        ignorados = []
        por_mes = defaultdict(lambda: {"entradas": Decimal("0.00"), "saidas": Decimal("0.00"), "qtd": 0})

        print("\nMOVIMENTOS QUITADOS VINCULADOS A CORA:")
        if not quitados:
            print("  <nenhum>")

        for l in quitados:
            valor = money(l.valor)
            tipo = (l.tipo or "").lower()
            data_ref = l.data_pagamento or l.data_lancamento
            chave_mes = data_ref.strftime("%Y-%m") if data_ref else "sem-data"

            sinal = Decimal("0.00")
            if tipo in {"receita", "conta_receber"}:
                entradas += valor
                por_mes[chave_mes]["entradas"] += valor
                sinal = valor
            elif tipo in {"despesa", "conta_pagar"}:
                saidas += valor
                por_mes[chave_mes]["saidas"] += valor
                sinal = -valor
            else:
                ignorados.append(l)

            por_mes[chave_mes]["qtd"] += 1
            print(
                f"  id={l.id} data={data_ref} tipo={l.tipo} status={l.status} "
                f"valor={fmt(l.valor)} impacto={fmt(sinal)} descricao={l.descricao}"
            )

        saldo_reconstruido = money(conta.saldo_inicial) + entradas - saidas
        diferenca_gravado_reconstruido = money(conta.saldo_atual) - saldo_reconstruido

        print("\nRESUMO DOS MOVIMENTOS VINCULADOS:")
        print(f"  Entradas quitadas: {fmt(entradas)}")
        print(f"  Saidas quitadas: {fmt(saidas)}")
        print(f"  Saldo reconstruido = inicial + entradas - saidas: {fmt(saldo_reconstruido)}")
        print(f"  Diferenca saldo gravado - reconstruido: {fmt(diferenca_gravado_reconstruido)}")
        print(f"  Lancamentos pendentes vinculados: {len(pendentes)}")
        print(f"  Tipos quitados ignorados por nao serem receita/despesa: {len(ignorados)}")

        print("\nRESUMO POR MES:")
        for mes in sorted(por_mes):
            dados = por_mes[mes]
            liquido = dados["entradas"] - dados["saidas"]
            print(
                f"  {mes}: qtd={dados['qtd']} entradas={fmt(dados['entradas'])} "
                f"saidas={fmt(dados['saidas'])} liquido={fmt(liquido)}"
            )

        quitados_sem_conta = LancamentoFinanceiro.query.filter(
            LancamentoFinanceiro.ativo == True,
            LancamentoFinanceiro.conta_bancaria_id.is_(None),
            LancamentoFinanceiro.status.in_(["pago", "recebido"]),
        ).order_by(
            LancamentoFinanceiro.data_pagamento.asc().nullslast(),
            LancamentoFinanceiro.id.asc(),
        ).all()

        print("\nQUITADOS/RECEBIDOS SEM CONTA BANCARIA VINCULADA:")
        if not quitados_sem_conta:
            print("  <nenhum>")
        else:
            soma_sem_conta = Decimal("0.00")
            for l in quitados_sem_conta:
                soma_sem_conta += money(l.valor)
                print(
                    f"  id={l.id} data_pagamento={l.data_pagamento} tipo={l.tipo} "
                    f"status={l.status} valor={fmt(l.valor)} descricao={l.descricao}"
                )
            print(f"  Quantidade: {len(quitados_sem_conta)} | Soma bruta: {fmt(soma_sem_conta)}")

        print("\nOBSERVACAO:")
        print("  Este script e somente leitura. Nenhuma alteracao foi realizada.")
        print("=" * 92 + "\n")


if __name__ == "__main__":
    main()
