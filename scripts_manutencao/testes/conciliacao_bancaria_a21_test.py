# -*- coding: utf-8 -*-
"""
D25F01-A2.1
Testes isolados das regras matematicas da conciliacao.
"""

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
    "conciliacao_service_isolado",
    SERVICE,
)

modulo = importlib.util.module_from_spec(spec)
spec.loader.exec_module(modulo)

ConciliacaoInvalida = modulo.ConciliacaoInvalida
validar_distribuicao = modulo.validar_distribuicao


def testar_mr_jacky():
    resumo = validar_distribuicao(
        Decimal("990.00"),
        [
            Decimal("450.00"),
            Decimal("540.00"),
        ],
    )

    assert resumo.valor_extrato == Decimal("990.00")
    assert resumo.total_alocado == Decimal("990.00")
    assert resumo.restante == Decimal("0.00")
    assert resumo.status == "CONCILIADO"


def testar_parcial():
    resumo = validar_distribuicao(
        Decimal("990.00"),
        [
            Decimal("450.00"),
        ],
    )

    assert resumo.total_alocado == Decimal("450.00")
    assert resumo.restante == Decimal("540.00")
    assert resumo.status == "PARCIAL"


def testar_excesso():
    try:
        validar_distribuicao(
            Decimal("990.00"),
            [
                Decimal("450.00"),
                Decimal("600.00"),
            ],
        )
    except ConciliacaoInvalida as erro:
        assert "ultrapassa" in str(erro)
        assert "60.00" in str(erro)
    else:
        raise AssertionError(
            "Conciliacao acima do valor do extrato deveria falhar."
        )


def testar_valor_zero():
    try:
        validar_distribuicao(
            Decimal("990.00"),
            [
                Decimal("0.00"),
            ],
        )
    except ConciliacaoInvalida:
        pass
    else:
        raise AssertionError(
            "Alocacao zero deveria ser bloqueada."
        )


def testar_extrato_negativo():
    resumo = validar_distribuicao(
        Decimal("-130.00"),
        [
            Decimal("130.00"),
        ],
    )

    assert resumo.valor_extrato == Decimal("130.00")
    assert resumo.total_alocado == Decimal("130.00")
    assert resumo.restante == Decimal("0.00")
    assert resumo.status == "CONCILIADO"


def main():
    testar_mr_jacky()
    testar_parcial()
    testar_excesso()
    testar_valor_zero()
    testar_extrato_negativo()

    print("OK: MR Jacky 990 = 450 + 540.")
    print("OK: conciliacao integral retorna CONCILIADO.")
    print("OK: conciliacao incompleta retorna PARCIAL.")
    print("OK: excesso de R$ 60,00 foi bloqueado.")
    print("OK: alocacao zero foi bloqueada.")
    print("OK: debito negativo do extrato foi normalizado.")
    print("OK: nenhum Flask ou banco foi acessado.")
    print("OK: D25F01-A2.1 homologado.")


if __name__ == "__main__":
    main()
