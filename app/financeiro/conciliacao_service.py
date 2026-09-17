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


# ============================================================
# D25F01-A2.2 - PREPARACAO DE CONCILIACAO
# ============================================================

TIPOS_LANCAMENTO_POR_MOVIMENTO = {
    "credito": {"receita", "conta_receber"},
    "debito": {"despesa", "conta_pagar"},
}


@dataclass(frozen=True)
class SolicitacaoAlocacao:
    lancamento_id: int
    valor: Decimal


@dataclass(frozen=True)
class LancamentoConciliavel:
    lancamento_id: int
    valor_total: Decimal
    tipo: str
    valor_ja_conciliado: Decimal = Decimal("0.00")
    conta_bancaria_id: int | None = None


@dataclass(frozen=True)
class PreparacaoConciliacao:
    extrato_id: int
    valor_extrato: Decimal
    valor_ja_conciliado: Decimal
    saldo_inicial_extrato: Decimal
    total_novo: Decimal
    saldo_final_extrato: Decimal
    status_final: str
    alocacoes: tuple


def preparar_conciliacao(
    *,
    extrato_id,
    valor_extrato,
    tipo_movimento,
    conta_bancaria_id,
    valor_ja_conciliado,
    alocacoes,
    lancamentos,
):
    """
    Prepara uma conciliacao sem gravar no banco.

    Valida:
    - saldo restante do extrato;
    - saldo restante de cada lancamento;
    - tipo credito/debito;
    - conta bancaria;
    - lancamentos duplicados;
    - sobrealocacao.
    """

    try:
        extrato_id = int(extrato_id)
    except (TypeError, ValueError):
        raise ConciliacaoInvalida(
            "extrato_id invalido."
        )

    if extrato_id <= 0:
        raise ConciliacaoInvalida(
            "extrato_id invalido."
        )

    movimento = str(tipo_movimento or "").strip().lower()

    if movimento not in TIPOS_LANCAMENTO_POR_MOVIMENTO:
        raise ConciliacaoInvalida(
            "Tipo de movimento bancario invalido."
        )

    total_extrato = abs(
        _valor_monetario(
            valor_extrato,
            "valor_extrato",
        )
    )

    if total_extrato <= 0:
        raise ConciliacaoInvalida(
            "O valor do extrato deve ser maior que zero."
        )

    ja_extrato = _valor_monetario(
        valor_ja_conciliado,
        "valor_ja_conciliado",
    )

    if ja_extrato < 0:
        raise ConciliacaoInvalida(
            "Valor ja conciliado do extrato nao pode ser negativo."
        )

    if ja_extrato > total_extrato:
        raise ConciliacaoInvalida(
            "Extrato possui conciliacao superior ao proprio valor."
        )

    saldo_extrato = (
        total_extrato - ja_extrato
    ).quantize(CENTAVO)

    solicitacoes = list(alocacoes)

    if not solicitacoes:
        raise ConciliacaoInvalida(
            "Informe ao menos uma alocacao."
        )

    ids_vistos = set()
    normalizadas = []

    for solicitacao in solicitacoes:
        try:
            lancamento_id = int(
                solicitacao.lancamento_id
            )
        except (TypeError, ValueError):
            raise ConciliacaoInvalida(
                "lancamento_id invalido."
            )

        if lancamento_id <= 0:
            raise ConciliacaoInvalida(
                "lancamento_id invalido."
            )

        if lancamento_id in ids_vistos:
            raise ConciliacaoInvalida(
                f"Lancamento {lancamento_id} repetido "
                "na mesma conciliacao."
            )

        ids_vistos.add(lancamento_id)

        valor_novo = _valor_monetario(
            solicitacao.valor,
            f"lancamento_{lancamento_id}",
        )

        if valor_novo <= 0:
            raise ConciliacaoInvalida(
                "Toda alocacao deve ser maior que zero."
            )

        lancamento = lancamentos.get(
            lancamento_id
        )

        if lancamento is None:
            raise ConciliacaoInvalida(
                f"Lancamento {lancamento_id} "
                "nao encontrado."
            )

        tipo_lancamento = str(
            lancamento.tipo or ""
        ).strip().lower()

        tipos_permitidos = (
            TIPOS_LANCAMENTO_POR_MOVIMENTO[
                movimento
            ]
        )

        if tipo_lancamento not in tipos_permitidos:
            raise ConciliacaoInvalida(
                f"Lancamento {lancamento_id} "
                "possui tipo incompativel com "
                f"movimento {movimento}."
            )

        if (
            conta_bancaria_id is not None
            and lancamento.conta_bancaria_id is not None
            and lancamento.conta_bancaria_id
            != conta_bancaria_id
        ):
            raise ConciliacaoInvalida(
                f"Lancamento {lancamento_id} "
                "pertence a outra conta bancaria."
            )

        total_lancamento = abs(
            _valor_monetario(
                lancamento.valor_total,
                f"valor_lancamento_{lancamento_id}",
            )
        )

        ja_lancamento = _valor_monetario(
            lancamento.valor_ja_conciliado,
            f"ja_conciliado_{lancamento_id}",
        )

        if ja_lancamento < 0:
            raise ConciliacaoInvalida(
                f"Lancamento {lancamento_id} "
                "possui valor conciliado negativo."
            )

        if ja_lancamento > total_lancamento:
            raise ConciliacaoInvalida(
                f"Lancamento {lancamento_id} "
                "esta sobreconciliado."
            )

        disponivel = (
            total_lancamento - ja_lancamento
        ).quantize(CENTAVO)

        if valor_novo > disponivel:
            excesso = (
                valor_novo - disponivel
            ).quantize(CENTAVO)

            raise ConciliacaoInvalida(
                f"Lancamento {lancamento_id} "
                "ultrapassa o saldo disponivel "
                f"em R$ {excesso}."
            )

        normalizadas.append(
            SolicitacaoAlocacao(
                lancamento_id=lancamento_id,
                valor=valor_novo,
            )
        )

    total_novo = sum(
        (
            item.valor
            for item in normalizadas
        ),
        Decimal("0.00"),
    ).quantize(CENTAVO)

    if total_novo > saldo_extrato:
        excesso = (
            total_novo - saldo_extrato
        ).quantize(CENTAVO)

        raise ConciliacaoInvalida(
            "Novas alocacoes ultrapassam "
            f"o saldo do extrato em R$ {excesso}."
        )

    saldo_final = (
        saldo_extrato - total_novo
    ).quantize(CENTAVO)

    status_final = (
        "CONCILIADO"
        if saldo_final == Decimal("0.00")
        else "PARCIAL"
    )

    return PreparacaoConciliacao(
        extrato_id=extrato_id,
        valor_extrato=total_extrato,
        valor_ja_conciliado=ja_extrato,
        saldo_inicial_extrato=saldo_extrato,
        total_novo=total_novo,
        saldo_final_extrato=saldo_final,
        status_final=status_final,
        alocacoes=tuple(normalizadas),
    )
