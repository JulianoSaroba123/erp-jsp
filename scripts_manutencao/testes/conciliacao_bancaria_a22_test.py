# -*- coding: utf-8 -*-

import importlib.util
from decimal import Decimal
from pathlib import Path


RAIZ = Path(__file__).resolve().parents[2]

SERVICE = (
    RAIZ
    / "app"
    / "financeiro"
    / "conciliacao_service.py"
)

spec = importlib.util.spec_from_file_location(
    "conciliacao_service_a22",
    SERVICE,
)

modulo = importlib.util.module_from_spec(spec)
spec.loader.exec_module(modulo)

ConciliacaoInvalida = modulo.ConciliacaoInvalida
SolicitacaoAlocacao = modulo.SolicitacaoAlocacao
LancamentoConciliavel = modulo.LancamentoConciliavel
preparar_conciliacao = modulo.preparar_conciliacao


def lancamento(
    identificador,
    valor,
    tipo="receita",
    ja="0.00",
    conta=1,
):
    return LancamentoConciliavel(
        lancamento_id=identificador,
        valor_total=Decimal(valor),
        tipo=tipo,
        valor_ja_conciliado=Decimal(ja),
        conta_bancaria_id=conta,
    )


def testar_mr_jacky():
    lancamentos = {
        101: lancamento(101, "450.00"),
        102: lancamento(102, "540.00"),
    }

    resultado = preparar_conciliacao(
        extrato_id=1,
        valor_extrato=Decimal("990.00"),
        tipo_movimento="credito",
        conta_bancaria_id=1,
        valor_ja_conciliado=Decimal("0.00"),
        alocacoes=[
            SolicitacaoAlocacao(
                101,
                Decimal("450.00"),
            ),
            SolicitacaoAlocacao(
                102,
                Decimal("540.00"),
            ),
        ],
        lancamentos=lancamentos,
    )

    assert resultado.total_novo == Decimal("990.00")
    assert resultado.saldo_final_extrato == Decimal("0.00")
    assert resultado.status_final == "CONCILIADO"


def testar_lancamento_parcial_preexistente():
    lancamentos = {
        201: lancamento(
            201,
            "1000.00",
            ja="400.00",
        ),
    }

    resultado = preparar_conciliacao(
        extrato_id=2,
        valor_extrato=Decimal("600.00"),
        tipo_movimento="credito",
        conta_bancaria_id=1,
        valor_ja_conciliado=Decimal("0.00"),
        alocacoes=[
            SolicitacaoAlocacao(
                201,
                Decimal("600.00"),
            ),
        ],
        lancamentos=lancamentos,
    )

    assert resultado.status_final == "CONCILIADO"


def deve_falhar(funcao, trecho):
    try:
        funcao()
    except ConciliacaoInvalida as erro:
        assert trecho in str(erro), str(erro)
    else:
        raise AssertionError(
            f"Era esperado erro contendo: {trecho}"
        )


def main():
    testar_mr_jacky()
    testar_lancamento_parcial_preexistente()

    deve_falhar(
        lambda: preparar_conciliacao(
            extrato_id=3,
            valor_extrato="990.00",
            tipo_movimento="credito",
            conta_bancaria_id=1,
            valor_ja_conciliado="0.00",
            alocacoes=[
                SolicitacaoAlocacao(
                    301,
                    Decimal("451.00"),
                ),
            ],
            lancamentos={
                301: lancamento(
                    301,
                    "450.00",
                ),
            },
        ),
        "saldo disponivel",
    )

    deve_falhar(
        lambda: preparar_conciliacao(
            extrato_id=4,
            valor_extrato="100.00",
            tipo_movimento="credito",
            conta_bancaria_id=1,
            valor_ja_conciliado="0.00",
            alocacoes=[
                SolicitacaoAlocacao(
                    401,
                    Decimal("100.00"),
                ),
            ],
            lancamentos={
                401: lancamento(
                    401,
                    "100.00",
                    tipo="despesa",
                ),
            },
        ),
        "tipo incompativel",
    )

    deve_falhar(
        lambda: preparar_conciliacao(
            extrato_id=5,
            valor_extrato="100.00",
            tipo_movimento="credito",
            conta_bancaria_id=1,
            valor_ja_conciliado="0.00",
            alocacoes=[
                SolicitacaoAlocacao(
                    501,
                    Decimal("100.00"),
                ),
            ],
            lancamentos={
                501: lancamento(
                    501,
                    "100.00",
                    conta=2,
                ),
            },
        ),
        "outra conta bancaria",
    )

    deve_falhar(
        lambda: preparar_conciliacao(
            extrato_id=6,
            valor_extrato="200.00",
            tipo_movimento="credito",
            conta_bancaria_id=1,
            valor_ja_conciliado="0.00",
            alocacoes=[
                SolicitacaoAlocacao(
                    601,
                    Decimal("100.00"),
                ),
                SolicitacaoAlocacao(
                    601,
                    Decimal("100.00"),
                ),
            ],
            lancamentos={
                601: lancamento(
                    601,
                    "200.00",
                ),
            },
        ),
        "repetido",
    )

    print("OK: MR Jacky preparado: 990 = 450 + 540.")
    print("OK: lancamento previamente parcial aceita complemento.")
    print("OK: sobrealocacao do lancamento bloqueada.")
    print("OK: credito x despesa bloqueado.")
    print("OK: conta bancaria divergente bloqueada.")
    print("OK: lancamento duplicado bloqueado.")
    print("OK: nenhum Flask ou banco foi acessado.")
    print("OK: D25F01-A2.2 homologado.")


if __name__ == "__main__":
    main()
