# -*- coding: utf-8 -*-
"""Diagnostica e reconcilia, de forma idempotente, a OS20260081.

Uso em produção (Render Shell):

    python scripts_manutencao/reconciliar_os20260081.py

O comando acima é SOMENTE LEITURA e imprime o estado atual.

Depois de revisar o diagnóstico, para aplicar a correção conhecida:

    python scripts_manutencao/reconciliar_os20260081.py --apply

Regras de segurança:
- atua exclusivamente na OS20260081;
- exige exatamente duas parcelas, números 1 e 2;
- exige R$ 2.800,00 em cada parcela e total da OS R$ 5.600,00;
- aceita como histórico somente lançamento legado sem parcela que esteja
  inativo, pendente, sem pagamento, origem ORDEM_SERVICO e valor R$ 5.600,00;
- aborta diante de qualquer outro lançamento solto ou duplicado;
- preserva juros, multa, desconto, comprovante e demais metadados;
- não recria lançamentos já existentes;
- pode ser executado novamente sem duplicar registros.
"""

import argparse
import os
import sys
from datetime import date
from decimal import Decimal

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from app import create_app
from app.extensoes import db
from app.financeiro.financeiro_model import LancamentoFinanceiro
from app.financeiro.financeiro_utils import gerar_lancamento_ordem_servico
from app.ordem_servico.ordem_servico_model import OrdemServico, OrdemServicoParcela


OS_NUMERO = "OS20260081"
VALOR_TOTAL = Decimal("5600.00")
VALOR_PARCELA = Decimal("2800.00")
P1_VENCIMENTO = date(2026, 8, 11)
P1_PAGAMENTO = date(2026, 8, 11)
P2_VENCIMENTO = date(2026, 8, 28)
P2_PAGAMENTO = date(2026, 9, 4)


def money(valor):
    if valor is None:
        return "None"
    return f"{Decimal(str(valor)):.2f}"


def fmt_data(valor):
    return valor.isoformat() if valor else "None"


def imprimir_estado(ordem, parcelas, lancamentos):
    print("\n" + "=" * 78)
    print(f"DIAGNOSTICO {OS_NUMERO}")
    print("=" * 78)
    print(
        "OS: "
        f"id={ordem.id} status={ordem.status} "
        f"status_pagamento={ordem.status_pagamento} "
        f"valor_total={money(ordem.valor_total)} "
        f"condicao={ordem.condicao_pagamento} "
        f"numero_parcelas={ordem.numero_parcelas} "
        f"valor_entrada={money(ordem.valor_entrada)} "
        f"data_primeira_parcela={fmt_data(ordem.data_primeira_parcela)} "
        f"data_vencimento_pagamento={fmt_data(ordem.data_vencimento_pagamento)}"
    )

    print("\nPARCELAS:")
    if not parcelas:
        print("  <nenhuma>")
    for p in parcelas:
        print(
            f"  id={p.id} numero={p.numero_parcela} ativo={getattr(p, 'ativo', None)} "
            f"valor={money(p.valor)} venc={fmt_data(p.data_vencimento)} "
            f"pago={getattr(p, 'pago', None)} pagamento={fmt_data(getattr(p, 'data_pagamento', None))}"
        )

    print("\nLANCAMENTOS FINANCEIROS DA OS:")
    if not lancamentos:
        print("  <nenhum>")
    for l in lancamentos:
        print(
            f"  id={l.id} ativo={getattr(l, 'ativo', None)} "
            f"parcela_id={l.ordem_servico_parcela_id} "
            f"numero_parcela={getattr(l, 'numero_parcela', None)} "
            f"valor={money(l.valor)} venc={fmt_data(l.data_vencimento)} "
            f"status={l.status} pagamento={fmt_data(l.data_pagamento)} "
            f"forma={getattr(l, 'forma_pagamento', None)} origem={getattr(l, 'origem', None)}"
        )
    print("=" * 78 + "\n")


def carregar_estado():
    ordens = OrdemServico.query.filter_by(numero=OS_NUMERO).all()
    if len(ordens) != 1:
        raise RuntimeError(
            f"Esperada exatamente 1 OS {OS_NUMERO}; encontradas {len(ordens)}. ABORTADO."
        )

    ordem = ordens[0]
    parcelas = OrdemServicoParcela.query.filter_by(
        ordem_servico_id=ordem.id
    ).order_by(OrdemServicoParcela.numero_parcela, OrdemServicoParcela.id).all()

    lancamentos = LancamentoFinanceiro.query.filter_by(
        ordem_servico_id=ordem.id
    ).order_by(LancamentoFinanceiro.id).all()

    return ordem, parcelas, lancamentos


def _legado_inativo_seguro(lancamento):
    """Reconhece exclusivamente o padrão legado observado no diagnóstico."""
    if lancamento.ordem_servico_parcela_id is not None:
        return False

    valor = Decimal(str(lancamento.valor or 0)).quantize(Decimal("0.01"))
    return (
        getattr(lancamento, "ativo", True) is False
        and lancamento.status == "pendente"
        and lancamento.data_pagamento is None
        and getattr(lancamento, "origem", None) == "ORDEM_SERVICO"
        and valor == VALOR_TOTAL
    )


def validar_para_aplicar(ordem, parcelas, lancamentos):
    erros = []

    if Decimal(str(ordem.valor_total or 0)).quantize(Decimal("0.01")) != VALOR_TOTAL:
        erros.append(
            f"valor_total da OS inesperado: {money(ordem.valor_total)} (esperado 5600.00)"
        )

    if len(parcelas) != 2:
        erros.append(f"quantidade de parcelas inesperada: {len(parcelas)} (esperado 2)")
    else:
        numeros = [p.numero_parcela for p in parcelas]
        if numeros != [1, 2]:
            erros.append(f"numeração das parcelas inesperada: {numeros} (esperado [1, 2])")

        for p in parcelas:
            if Decimal(str(p.valor or 0)).quantize(Decimal("0.01")) != VALOR_PARCELA:
                erros.append(
                    f"parcela id={p.id} tem valor {money(p.valor)} (esperado 2800.00)"
                )

    parcela_ids = {p.id for p in parcelas}
    por_parcela = {}
    soltos_invalidos = []
    legados_inativos = []

    for l in lancamentos:
        pid = l.ordem_servico_parcela_id

        if pid is None:
            if _legado_inativo_seguro(l):
                legados_inativos.append(l)
                continue
            soltos_invalidos.append(l)
            continue

        if pid not in parcela_ids:
            soltos_invalidos.append(l)
            continue

        por_parcela.setdefault(pid, []).append(l)

    if legados_inativos:
        print(
            "LEGADOS INATIVOS PRESERVADOS: "
            + ", ".join(str(l.id) for l in legados_inativos)
        )

    if soltos_invalidos:
        erros.append(
            "existem lançamentos sem vínculo válido que NÃO atendem ao padrão legado seguro: "
            + ", ".join(str(l.id) for l in soltos_invalidos)
        )

    duplicados = {
        pid: regs for pid, regs in por_parcela.items() if len(regs) > 1
    }
    if duplicados:
        erros.append(
            "existem lançamentos duplicados por parcela: "
            + ", ".join(
                f"parcela_id={pid} lancamentos={[l.id for l in regs]}"
                for pid, regs in duplicados.items()
            )
        )

    if erros:
        raise RuntimeError("\n- " + "\n- ".join(erros) + "\nABORTADO sem alterar o banco.")


def aplicar_reconciliacao(ordem, parcelas, lancamentos):
    validar_para_aplicar(ordem, parcelas, lancamentos)

    p1, p2 = parcelas

    # Corrige somente os fatos conhecidos da OS e das parcelas.
    ordem.status = "concluida"
    ordem.condicao_pagamento = "parcelado"
    ordem.numero_parcelas = 2
    ordem.valor_entrada = VALOR_PARCELA
    ordem.data_primeira_parcela = P1_VENCIMENTO
    ordem.data_vencimento_pagamento = P2_VENCIMENTO
    ordem.status_pagamento = "pago"

    p1.numero_parcela = 1
    p1.valor = VALOR_PARCELA
    p1.data_vencimento = P1_VENCIMENTO
    p1.pago = True
    p1.data_pagamento = P1_PAGAMENTO
    p1.ativo = True

    p2.numero_parcela = 2
    p2.valor = VALOR_PARCELA
    p2.data_vencimento = P2_VENCIMENTO
    p2.pago = True
    p2.data_pagamento = P2_PAGAMENTO
    p2.ativo = True

    db.session.commit()

    # Se algum lançamento estiver faltando, usa a integração oficial para criá-lo.
    vinculados = {
        l.ordem_servico_parcela_id: l
        for l in LancamentoFinanceiro.query.filter_by(ordem_servico_id=ordem.id).all()
        if l.ordem_servico_parcela_id in {p1.id, p2.id}
    }
    if p1.id not in vinculados or p2.id not in vinculados:
        gerar_lancamento_ordem_servico(ordem, forma_pagamento="pix")

    # Reconsulta e corrige APENAS os campos factuais dos lançamentos.
    # Campos como juros, multa, desconto, comprovante e auditoria ficam intactos.
    lancamentos_finais = LancamentoFinanceiro.query.filter_by(
        ordem_servico_id=ordem.id
    ).order_by(LancamentoFinanceiro.id).all()

    validar_para_aplicar(ordem, [p1, p2], lancamentos_finais)

    por_parcela = {
        l.ordem_servico_parcela_id: l
        for l in lancamentos_finais
        if l.ordem_servico_parcela_id in {p1.id, p2.id}
    }

    l1 = por_parcela[p1.id]
    l1.valor = VALOR_PARCELA
    l1.data_vencimento = P1_VENCIMENTO
    l1.status = "recebido"
    l1.data_pagamento = P1_PAGAMENTO
    l1.numero_parcela = "1/2"
    if not l1.forma_pagamento:
        l1.forma_pagamento = "pix"
    if hasattr(l1, "origem") and not l1.origem:
        l1.origem = "ORDEM_SERVICO"
    l1.ativo = True

    l2 = por_parcela[p2.id]
    l2.valor = VALOR_PARCELA
    l2.data_vencimento = P2_VENCIMENTO
    l2.status = "recebido"
    l2.data_pagamento = P2_PAGAMENTO
    l2.numero_parcela = "2/2"
    if not l2.forma_pagamento:
        l2.forma_pagamento = "pix"
    if hasattr(l2, "origem") and not l2.origem:
        l2.origem = "ORDEM_SERVICO"
    l2.ativo = True

    ordem.status_pagamento = "pago"
    db.session.commit()


def main():
    parser = argparse.ArgumentParser(
        description=f"Diagnóstico/reconciliação segura da {OS_NUMERO}."
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Aplica a correção após todas as validações de segurança.",
    )
    args = parser.parse_args()

    app = create_app()
    with app.app_context():
        ordem, parcelas, lancamentos = carregar_estado()
        imprimir_estado(ordem, parcelas, lancamentos)

        if not args.apply:
            print("MODO DIAGNOSTICO: nenhuma alteração foi realizada.")
            print("Revise a saída antes de executar novamente com --apply.")
            return

        print("MODO APPLY solicitado. Validando estrutura antes de alterar...")
        aplicar_reconciliacao(ordem, parcelas, lancamentos)

        ordem, parcelas, lancamentos = carregar_estado()
        imprimir_estado(ordem, parcelas, lancamentos)

        # Verificação final objetiva.
        assert ordem.status == "concluida"
        assert ordem.status_pagamento == "pago"
        assert ordem.condicao_pagamento == "parcelado"
        assert ordem.numero_parcelas == 2
        assert ordem.valor_entrada == VALOR_PARCELA
        assert ordem.data_primeira_parcela == P1_VENCIMENTO
        assert ordem.data_vencimento_pagamento == P2_VENCIMENTO
        assert len(parcelas) == 2
        assert parcelas[0].data_vencimento == P1_VENCIMENTO
        assert parcelas[0].data_pagamento == P1_PAGAMENTO
        assert parcelas[0].pago is True
        assert parcelas[1].data_vencimento == P2_VENCIMENTO
        assert parcelas[1].data_pagamento == P2_PAGAMENTO
        assert parcelas[1].pago is True

        vinculados = {
            l.ordem_servico_parcela_id: l
            for l in lancamentos
            if l.ordem_servico_parcela_id in {parcelas[0].id, parcelas[1].id}
        }
        assert vinculados[parcelas[0].id].data_vencimento == P1_VENCIMENTO
        assert vinculados[parcelas[0].id].data_pagamento == P1_PAGAMENTO
        assert vinculados[parcelas[0].id].status == "recebido"
        assert vinculados[parcelas[0].id].ativo is True
        assert vinculados[parcelas[1].id].data_vencimento == P2_VENCIMENTO
        assert vinculados[parcelas[1].id].data_pagamento == P2_PAGAMENTO
        assert vinculados[parcelas[1].id].status == "recebido"
        assert vinculados[parcelas[1].id].ativo is True

        print("RECONCILIACAO CONCLUIDA E VALIDADA COM SUCESSO.")


if __name__ == "__main__":
    main()
