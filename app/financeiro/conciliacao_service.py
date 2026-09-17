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


# ============================================================
# D25F01-A2.3 - PERSISTENCIA ORM TRANSACIONAL
# ============================================================

from datetime import datetime


@dataclass(frozen=True)
class ResultadoPersistenciaConciliacao:
    preparacao: PreparacaoConciliacao
    itens_criados: int
    itens_atualizados: int


def executar_conciliacao_orm(
    *,
    session,
    extrato_model,
    lancamento_model,
    item_model,
    extrato_id,
    alocacoes,
    usuario=None,
    observacoes=None,
):
    """
    Executa conciliacao usando uma sessao SQLAlchemy.

    A funcao recebe os models por injecao para permanecer desacoplada
    do bootstrap Flask.

    Regras:
    - bloqueia o extrato e os lancamentos quando o banco suporta lock;
    - considera conciliacoes ativas ja existentes;
    - valida toda a operacao antes de persistir;
    - cria ou atualiza o par extrato+lancamento;
    - commit unico;
    - rollback integral em qualquer falha;
    - nao altera status financeiro do lancamento;
    - nao movimenta saldo de conta bancaria.
    """

    try:
        try:
            chave_extrato = int(extrato_id)
        except (TypeError, ValueError):
            raise ConciliacaoInvalida(
                "extrato_id invalido."
            )

        if chave_extrato <= 0:
            raise ConciliacaoInvalida(
                "extrato_id invalido."
            )

        solicitacoes = list(alocacoes)

        extrato = (
            session.query(extrato_model)
            .filter(
                extrato_model.id == chave_extrato
            )
            .with_for_update()
            .one_or_none()
        )

        if extrato is None:
            raise ConciliacaoInvalida(
                f"Extrato {chave_extrato} nao encontrado."
            )

        ids_lancamentos = sorted(
            {
                int(item.lancamento_id)
                for item in solicitacoes
            }
        )

        lancamentos_db = (
            session.query(lancamento_model)
            .filter(
                lancamento_model.id.in_(
                    ids_lancamentos
                )
            )
            .order_by(lancamento_model.id)
            .with_for_update()
            .all()
        )

        lancamentos_por_id = {
            item.id: item
            for item in lancamentos_db
        }

        itens_extrato_todos = (
            session.query(item_model)
            .filter(
                item_model.extrato_id
                == chave_extrato
            )
            .with_for_update()
            .all()
        )

        itens_extrato_ativos = [
            item
            for item in itens_extrato_todos
            if bool(item.ativo)
        ]

        valor_ja_extrato = sum(
            (
                _valor_monetario(
                    item.valor_conciliado,
                    "valor_conciliado_extrato",
                )
                for item in itens_extrato_ativos
            ),
            Decimal("0.00"),
        ).quantize(CENTAVO)

        itens_lancamentos_ativos = (
            session.query(item_model)
            .filter(
                item_model.lancamento_id.in_(
                    ids_lancamentos
                ),
                item_model.ativo.is_(True),
            )
            .all()
        )

        conciliado_por_lancamento = {
            identificador: Decimal("0.00")
            for identificador
            in ids_lancamentos
        }

        for item in itens_lancamentos_ativos:
            atual = conciliado_por_lancamento.get(
                item.lancamento_id,
                Decimal("0.00"),
            )

            conciliado_por_lancamento[
                item.lancamento_id
            ] = (
                atual
                + _valor_monetario(
                    item.valor_conciliado,
                    "valor_conciliado_lancamento",
                )
            ).quantize(CENTAVO)

        lancamentos_dominio = {}

        for identificador, registro in (
            lancamentos_por_id.items()
        ):
            lancamentos_dominio[
                identificador
            ] = LancamentoConciliavel(
                lancamento_id=identificador,
                valor_total=_valor_monetario(
                    registro.valor,
                    f"valor_lancamento_{identificador}",
                ),
                tipo=registro.tipo,
                valor_ja_conciliado=(
                    conciliado_por_lancamento.get(
                        identificador,
                        Decimal("0.00"),
                    )
                ),
                conta_bancaria_id=(
                    registro.conta_bancaria_id
                ),
            )

        preparacao = preparar_conciliacao(
            extrato_id=chave_extrato,
            valor_extrato=extrato.valor,
            tipo_movimento=extrato.tipo_movimento,
            conta_bancaria_id=(
                extrato.conta_bancaria_id
            ),
            valor_ja_conciliado=(
                valor_ja_extrato
            ),
            alocacoes=solicitacoes,
            lancamentos=lancamentos_dominio,
        )

        pares_existentes = {
            item.lancamento_id: item
            for item in itens_extrato_todos
        }

        criados = 0
        atualizados = 0

        for alocacao in preparacao.alocacoes:
            existente = pares_existentes.get(
                alocacao.lancamento_id
            )

            if existente is None:
                novo = item_model(
                    extrato_id=chave_extrato,
                    lancamento_id=(
                        alocacao.lancamento_id
                    ),
                    valor_conciliado=alocacao.valor,
                    usuario=usuario,
                    observacoes=observacoes,
                    ativo=True,
                )

                session.add(novo)
                pares_existentes[
                    alocacao.lancamento_id
                ] = novo

                criados += 1
                continue

            if bool(existente.ativo):
                valor_atual = _valor_monetario(
                    existente.valor_conciliado,
                    "valor_conciliado_existente",
                )

                existente.valor_conciliado = (
                    valor_atual
                    + alocacao.valor
                ).quantize(CENTAVO)

            else:
                existente.ativo = True
                existente.valor_conciliado = (
                    alocacao.valor
                )

            if usuario is not None:
                existente.usuario = usuario

            if observacoes is not None:
                existente.observacoes = observacoes

            atualizados += 1

        conciliado_integral = (
            preparacao.status_final
            == "CONCILIADO"
        )

        extrato.conciliado = conciliado_integral

        if conciliado_integral:
            extrato.data_conciliacao = (
                datetime.utcnow()
            )
        else:
            extrato.data_conciliacao = None

        ids_ativos_finais = {
            item.lancamento_id
            for item in itens_extrato_ativos
        }

        ids_ativos_finais.update(
            item.lancamento_id
            for item in preparacao.alocacoes
        )

        if (
            conciliado_integral
            and len(ids_ativos_finais) == 1
        ):
            extrato.lancamento_id = next(
                iter(ids_ativos_finais)
            )
        else:
            # O campo legado nao consegue representar N:N.
            extrato.lancamento_id = None

        session.commit()

        return ResultadoPersistenciaConciliacao(
            preparacao=preparacao,
            itens_criados=criados,
            itens_atualizados=atualizados,
        )

    except Exception:
        session.rollback()
        raise
