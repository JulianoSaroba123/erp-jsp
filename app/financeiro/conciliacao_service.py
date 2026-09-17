# -*- coding: utf-8 -*-
"""
Regras puras da conciliacao bancaria.

Este modulo nao acessa Flask, SQLAlchemy ou banco de dados.
"""

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP


CENTAVO = Decimal("0.01")


class ConciliacaoInvalida(ValueError):
    """Regra de conciliacao bancaria violada."""


@dataclass(frozen=True)
class ResumoConciliacao:
    valor_extrato: Decimal
    total_alocado: Decimal
    restante: Decimal
    status: str


def _valor_monetario(valor, nome):
    try:
        numero = Decimal(str(valor)).quantize(
            CENTAVO,
            rounding=ROUND_HALF_UP,
        )
    except (InvalidOperation, ValueError, TypeError):
        raise ConciliacaoInvalida(
            f"{nome} possui valor monetario invalido."
        )

    if not numero.is_finite():
        raise ConciliacaoInvalida(
            f"{nome} possui valor monetario invalido."
        )

    return numero


def validar_distribuicao(valor_extrato, valores_alocados):
    """
    Valida a distribuicao de um movimento bancario.

    O valor do extrato pode ser positivo ou negativo.
    As alocacoes sao sempre informadas como valores positivos.

    Retorna:
    - CONCILIADO quando todo o movimento foi distribuido;
    - PARCIAL quando ainda existe saldo do extrato sem alocacao.
    """

    extrato = abs(
        _valor_monetario(valor_extrato, "valor_extrato")
    )

    if extrato <= 0:
        raise ConciliacaoInvalida(
            "O valor do extrato deve ser maior que zero."
        )

    valores = list(valores_alocados)

    if not valores:
        raise ConciliacaoInvalida(
            "Informe ao menos uma alocacao."
        )

    normalizados = []

    for indice, valor in enumerate(valores, start=1):
        numero = _valor_monetario(
            valor,
            f"alocacao_{indice}",
        )

        if numero <= 0:
            raise ConciliacaoInvalida(
                "Toda alocacao deve ser maior que zero."
            )

        normalizados.append(numero)

    total = sum(normalizados, Decimal("0.00")).quantize(CENTAVO)

    if total > extrato:
        excesso = (total - extrato).quantize(CENTAVO)

        raise ConciliacaoInvalida(
            f"O total alocado ultrapassa o extrato em R$ {excesso}."
        )

    restante = (extrato - total).quantize(CENTAVO)

    status = (
        "CONCILIADO"
        if restante == Decimal("0.00")
        else "PARCIAL"
    )

    return ResumoConciliacao(
        valor_extrato=extrato,
        total_alocado=total,
        restante=restante,
        status=status,
    )
