# -*- coding: utf-8 -*-
"""D26F01-A4 - Diagnostico e backfill seguro do PED0001.

Uso em producao:

    python scripts_manutencao/pedido_financeiro_backfill_d26f01.py

O comando acima e SOMENTE LEITURA.

Depois de revisar o diagnostico:

    python scripts_manutencao/pedido_financeiro_backfill_d26f01.py --apply

Regras de seguranca:
- atua exclusivamente no PED0001;
- exige pedido CONCLUIDO;
- exige venda direta, sem proposta_id;
- exige valor total R$ 1.680,00;
- exige cliente PROPOSTA ENGENHARIA AMBIENTAL LTDA.;
- exige coluna pedido_id instalada no financeiro;
- nao cria novo recebivel se ja existir vinculo por pedido_id;
- procura lancamentos legados suspeitos antes de criar;
- diante de qualquer candidato legado, ABORTA o --apply;
- usa o service oficial Pedido -> Financeiro;
- e idempotente.
"""

import argparse
import os
import sys
from decimal import Decimal

from sqlalchemy import inspect, or_


ROOT = os.path.abspath(
    os.path.join(
        os.path.dirname(__file__),
        "..",
    )
)

if ROOT not in sys.path:
    sys.path.insert(0, ROOT)


from app import create_app
from app.extensoes import db
from app.financeiro.financeiro_model import LancamentoFinanceiro
from app.financeiro.pedido_financeiro_service import (
    sincronizar_lancamentos_pedido,
)
from app.pedido.pedido_model import Pedido


PEDIDO_NUMERO = "PED0001"
VALOR_ESPERADO = Decimal("1680.00")
CLIENTE_ESPERADO = "PROPOSTA ENGENHARIA AMBIENTAL LTDA."


def money(valor):
    return Decimal(
        str(valor or 0)
    ).quantize(
        Decimal("0.01")
    )


def normalizar_texto(valor):
    return " ".join(
        str(valor or "")
        .strip()
        .upper()
        .split()
    )


def validar_schema():
    inspector = inspect(db.engine)

    tabelas = set(
        inspector.get_table_names()
    )

    if "lancamentos_financeiros" not in tabelas:
        raise RuntimeError(
            "Tabela lancamentos_financeiros nao encontrada."
        )

    colunas = {
        coluna["name"]
        for coluna in inspector.get_columns(
            "lancamentos_financeiros"
        )
    }

    if "pedido_id" not in colunas:
        raise RuntimeError(
            "Coluna pedido_id nao existe em "
            "lancamentos_financeiros. "
            "Execute a migration 20260919_03 antes "
            "do backfill."
        )


def carregar_pedido():
    pedidos = (
        Pedido.query
        .filter(Pedido.numero == PEDIDO_NUMERO)
        .all()
    )

    if len(pedidos) != 1:
        raise RuntimeError(
            f"Esperado exatamente 1 {PEDIDO_NUMERO}; "
            f"encontrados {len(pedidos)}."
        )

    return pedidos[0]


def validar_pedido(pedido):
    erros = []

    if pedido.status != Pedido.STATUS_CONCLUIDO:
        erros.append(
            f"status inesperado: {pedido.status}"
        )

    if pedido.proposta_id is not None:
        erros.append(
            "pedido possui proposta_id e nao e venda direta"
        )

    if money(pedido.valor_total) != VALOR_ESPERADO:
        erros.append(
            "valor_total inesperado: "
            f"{money(pedido.valor_total)} "
            f"(esperado {VALOR_ESPERADO})"
        )

    cliente_nome = normalizar_texto(
        getattr(
            getattr(pedido, "cliente", None),
            "nome",
            None,
        )
    )

    if cliente_nome != normalizar_texto(
        CLIENTE_ESPERADO
    ):
        erros.append(
            f"cliente inesperado: {cliente_nome!r}"
        )

    if getattr(pedido, "ativo", True) is False:
        erros.append(
            "pedido esta inativo"
        )

    if erros:
        raise RuntimeError(
            "\n- "
            + "\n- ".join(erros)
            + "\nABORTADO sem alterar o banco."
        )


def buscar_vinculados(pedido):
    return (
        LancamentoFinanceiro.query
        .filter(
            LancamentoFinanceiro.pedido_id
            == pedido.id
        )
        .order_by(
            LancamentoFinanceiro.id.asc()
        )
        .all()
    )


def buscar_candidatos_legados(pedido):
    """Busca possiveis recebiveis antigos nao vinculados ao Pedido.

    A busca e propositalmente conservadora.
    Qualquer candidato encontrado impede criacao automatica.
    """

    return (
        LancamentoFinanceiro.query
        .filter(
            LancamentoFinanceiro.pedido_id.is_(None),
            or_(
                LancamentoFinanceiro.numero_documento
                == PEDIDO_NUMERO,

                LancamentoFinanceiro.descricao.ilike(
                    f"%{PEDIDO_NUMERO}%"
                ),

                db.and_(
                    LancamentoFinanceiro.cliente_id
                    == pedido.cliente_id,
                    LancamentoFinanceiro.valor
                    == VALOR_ESPERADO,
                ),
            ),
        )
        .order_by(
            LancamentoFinanceiro.id.asc()
        )
        .all()
    )


def imprimir_lancamento(prefixo, lancamento):
    print(
        f"{prefixo} "
        f"id={lancamento.id} "
        f"ativo={getattr(lancamento, 'ativo', None)} "
        f"tipo={lancamento.tipo} "
        f"status={lancamento.status} "
        f"valor={money(lancamento.valor)} "
        f"data={lancamento.data_lancamento} "
        f"documento={lancamento.numero_documento!r} "
        f"origem={lancamento.origem!r} "
        f"cliente_id={lancamento.cliente_id} "
        f"pedido_id={getattr(lancamento, 'pedido_id', None)} "
        f"proposta_id={getattr(lancamento, 'proposta_id', None)} "
        f"os_id={getattr(lancamento, 'ordem_servico_id', None)}"
    )


def imprimir_diagnostico(
    pedido,
    vinculados,
    candidatos,
):
    print("\n" + "=" * 78)
    print("D26F01-A4 | DIAGNOSTICO PED0001")
    print("=" * 78)

    print(
        "PEDIDO: "
        f"id={pedido.id} "
        f"numero={pedido.numero} "
        f"status={pedido.status} "
        f"ativo={getattr(pedido, 'ativo', None)} "
        f"proposta_id={pedido.proposta_id} "
        f"cliente_id={pedido.cliente_id} "
        f"cliente={getattr(pedido.cliente, 'nome', None)!r} "
        f"valor_total={money(pedido.valor_total)} "
        f"data={pedido.data_pedido}"
    )

    print("\nLANCAMENTOS JA VINCULADOS:")
    if not vinculados:
        print("  <nenhum>")

    for lancamento in vinculados:
        imprimir_lancamento(
            "  ",
            lancamento,
        )

    print("\nPOSSIVEIS LANCAMENTOS LEGADOS:")
    if not candidatos:
        print("  <nenhum>")

    for lancamento in candidatos:
        imprimir_lancamento(
            "  ",
            lancamento,
        )

    print("=" * 78)


def aplicar(pedido, vinculados, candidatos):
    if len(vinculados) > 1:
        raise RuntimeError(
            "Mais de um lancamento vinculado ao pedido. "
            "ABORTADO."
        )

    if len(vinculados) == 1:
        print(
            "PED0001 ja possui lancamento financeiro "
            "vinculado. Nenhuma alteracao necessaria."
        )
        return vinculados[0]

    if candidatos:
        raise RuntimeError(
            "Foram encontrados possiveis lancamentos "
            "legados. ABORTADO para evitar duplicidade."
        )

    lancamentos = sincronizar_lancamentos_pedido(
        pedido
    )

    if len(lancamentos) != 1:
        raise RuntimeError(
            "Service nao retornou exatamente "
            "um lancamento."
        )

    db.session.commit()

    finais = buscar_vinculados(
        pedido
    )

    if len(finais) != 1:
        raise RuntimeError(
            "Validacao final encontrou quantidade "
            "inesperada de lancamentos."
        )

    final = finais[0]

    if final.tipo != "conta_receber":
        raise RuntimeError(
            f"tipo final inesperado: {final.tipo}"
        )

    if money(final.valor) != VALOR_ESPERADO:
        raise RuntimeError(
            f"valor final inesperado: {money(final.valor)}"
        )

    if final.origem != "PEDIDO":
        raise RuntimeError(
            f"origem final inesperada: {final.origem}"
        )

    return final


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Diagnostico/backfill seguro do PED0001."
        )
    )

    parser.add_argument(
        "--apply",
        action="store_true",
        help=(
            "Cria o recebivel somente apos "
            "todas as validacoes."
        ),
    )

    args = parser.parse_args()

    app = create_app()

    with app.app_context():
        validar_schema()

        pedido = carregar_pedido()
        validar_pedido(pedido)

        vinculados = buscar_vinculados(
            pedido
        )

        candidatos = buscar_candidatos_legados(
            pedido
        )

        imprimir_diagnostico(
            pedido,
            vinculados,
            candidatos,
        )

        if not args.apply:
            print(
                "\nMODO DIAGNOSTICO: "
                "nenhuma alteracao foi realizada."
            )

            if vinculados:
                print(
                    "RESULTADO: Pedido ja possui "
                    "financeiro vinculado."
                )
            elif candidatos:
                print(
                    "RESULTADO: existem candidatos "
                    "legados. NAO executar --apply "
                    "antes da revisao."
                )
            else:
                print(
                    "RESULTADO: nenhuma duplicidade "
                    "aparente encontrada. "
                    "PED0001 apto para --apply."
                )

            return

        print(
            "\nMODO APPLY solicitado. "
            "Executando validacoes finais..."
        )

        try:
            final = aplicar(
                pedido,
                vinculados,
                candidatos,
            )
        except Exception:
            db.session.rollback()
            raise

        print("\nBACKFILL CONCLUIDO:")
        imprimir_lancamento(
            "  ",
            final,
        )

        print(
            "\nD26F01-A4 CONCLUIDO E VALIDADO."
        )


if __name__ == "__main__":
    main()
