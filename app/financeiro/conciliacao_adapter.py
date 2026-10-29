# -*- coding: utf-8 -*-
"""
ERP JSP - Adaptador da conciliacao bancaria N:N.

Integra o motor transacional puro de conciliacao com a infraestrutura
real do ERP, mantendo as dependencias ORM concentradas nesta camada.
"""

from decimal import Decimal
from datetime import datetime

from app.extensoes import db
from app.financeiro.financeiro_model import (
    ExtratoBancario,
    LancamentoFinanceiro,
    ConciliacaoBancariaItem,
)
from app.financeiro.conciliacao_service import (
    executar_conciliacao_orm,
    ConciliacaoInvalida,
)


CENTAVO = Decimal("0.01")

_TIPOS_RECEBIVEIS = {
    "receita",
    "conta_receber",
}


def _dinheiro(valor):
    return Decimal(
        str(valor or 0)
    ).quantize(CENTAVO)


def _finalizar_baixas_proposta(
    *,
    session,
    extrato,
    lancamentos,
    preparacao,
    conciliado_por_lancamento,
    usuario=None,
):
    """Baixa recebiveis de proposta integralmente conciliados.

    Restrito a origem PROPOSTA.
    OS e demais origens preservam o comportamento do D25F01.
    """

    propostas_ids = set()

    for alocacao in preparacao.alocacoes:
        lancamento = lancamentos.get(
            alocacao.lancamento_id
        )

        if lancamento is None:
            continue

        origem = str(
            getattr(
                lancamento,
                "origem",
                "",
            )
            or ""
        ).strip().upper()

        tipo = str(
            getattr(
                lancamento,
                "tipo",
                "",
            )
            or ""
        ).strip().lower()

        if origem != "PROPOSTA":
            continue

        if tipo not in _TIPOS_RECEBIVEIS:
            continue

        if not getattr(
            lancamento,
            "proposta_id",
            None,
        ):
            continue

        if not getattr(
            lancamento,
            "proposta_parcela_id",
            None,
        ):
            continue

        total_antes = _dinheiro(
            conciliado_por_lancamento.get(
                lancamento.id,
                Decimal("0.00"),
            )
        )

        total_depois = (
            total_antes
            + _dinheiro(
                alocacao.valor
            )
        ).quantize(CENTAVO)

        total_lancamento = abs(
            _dinheiro(
                lancamento.valor
            )
        )

        # Pagamento parcial continua pendente.
        if total_depois != total_lancamento:
            continue

        lancamento.status = "recebido"

        # Data do movimento bancario passa a ser
        # a data canonica do recebimento.
        lancamento.data_pagamento = (
            extrato.data_movimento
        )

        if usuario:
            lancamento.usuario_editor = usuario

        propostas_ids.add(
            lancamento.proposta_id
        )

    if not propostas_ids:
        return

    # Imports tardios preservam testes isolados da conciliacao.
    from app.proposta.proposta_model import Proposta
    from app.financeiro.proposta_financeiro_service import (
        sincronizar_lancamentos_proposta,
    )

    for proposta_id in sorted(
        propostas_ids
    ):
        proposta = session.get(
            Proposta,
            proposta_id,
        )

        if proposta is not None:
            sincronizar_lancamentos_proposta(
                proposta
            )


def executar_conciliacao_bancaria(
    extrato_id,
    alocacoes,
    usuario=None,
    observacoes=None,
):
    """
    Executa a conciliacao bancaria usando os models e a sessao reais do ERP.

    Validacao e persistencia continuam centralizadas no motor N:N.
    O adaptador acrescenta apenas a sincronizacao transacional
    de recebiveis originados por PROPOSTA.
    """

    return executar_conciliacao_orm(
        session=db.session,
        extrato_model=ExtratoBancario,
        lancamento_model=LancamentoFinanceiro,
        item_model=ConciliacaoBancariaItem,
        extrato_id=extrato_id,
        alocacoes=alocacoes,
        usuario=usuario,
        observacoes=observacoes,
        finalizador_transacional=(
            _finalizar_baixas_proposta
        ),
    )


def desfazer_conciliacao_bancaria(
    extrato_id,
    *,
    lancamento_id=None,
    usuario=None,
    motivo=None,
):
    """Desfaz uma alocacao N:N (ou o vinculo 1:1 legado) numa transacao.

    Nao apaga movimentos financeiros, extratos nem alocacoes historicas.
    Um extrato com multiplos vinculos requer o ID do lancamento a retirar.
    Permite reparar extratos que foram marcados pendentes pelo desfazer
    legado, mas ainda possuem alocacoes N:N ativas.
    """
    motivo = str(motivo or "").strip()
    if len(motivo) < 8 or len(motivo) > 1000:
        raise ConciliacaoInvalida(
            "Informe um motivo de 8 a 1000 caracteres para auditoria."
        )

    try:
        extrato_id = int(extrato_id)
        if extrato_id <= 0:
            raise ValueError()
        if lancamento_id is not None:
            lancamento_id = int(lancamento_id)
            if lancamento_id <= 0:
                raise ValueError()
    except (ValueError, TypeError) as exc:
        raise ConciliacaoInvalida(
            "Identificador do extrato ou do lancamento invalido."
        ) from exc

    try:
        extrato = (
            db.session.query(ExtratoBancario)
            .filter(
                ExtratoBancario.id == extrato_id,
                ExtratoBancario.ativo.is_(True),
            )
            .with_for_update()
            .one_or_none()
        )
        if extrato is None:
            raise ConciliacaoInvalida("Extrato inexistente ou inativo.")

        # O reconciliador atualiza receitas de propostas e pode refletir
        # baixas de OS. Sem estorno integrado de cada origem, impedir que
        # a reversao bancaria deixe o titulo como recebido sem lastro.
        if extrato.tipo_movimento != "debito":
            raise ConciliacaoInvalida(
                "Desconciliacao de creditos exige reversao financeira "
                "especifica. Nao foi alterado nenhum vinculo."
            )

        # Mesma ordem de locks do conciliador N:N: extrato, titulos e itens.
        # Isso evita que outra conciliacao reutilize o saldo do titulo
        # simultaneamente ao desfazer deste vinculo.
        ids_vinculados = {
            linha[0]
            for linha in db.session.query(
                ConciliacaoBancariaItem.lancamento_id
            ).filter(
                ConciliacaoBancariaItem.extrato_id == extrato_id
            ).all()
        }
        if extrato.lancamento_id is not None:
            ids_vinculados.add(extrato.lancamento_id)

        if ids_vinculados:
            db.session.query(LancamentoFinanceiro).filter(
                LancamentoFinanceiro.id.in_(sorted(ids_vinculados))
            ).order_by(
                LancamentoFinanceiro.id
            ).with_for_update().all()

        itens = (
            db.session.query(ConciliacaoBancariaItem)
            .filter(ConciliacaoBancariaItem.extrato_id == extrato_id)
            .order_by(ConciliacaoBancariaItem.id)
            .with_for_update()
            .all()
        )
        ativos = [item for item in itens if item.ativo]

        if lancamento_id is None and len(ativos) > 1:
            raise ConciliacaoInvalida(
                "Extrato com multiplas alocacoes: selecione o lancamento."
            )

        selecionados = [
            item for item in ativos
            if lancamento_id is None or item.lancamento_id == lancamento_id
        ]

        agora = datetime.utcnow()
        anotacao = (
            f"Desconciliacao em {agora:%Y-%m-%d %H:%M:%S} UTC "
            f"por {usuario or 'usuario nao identificado'}. "
            f"Motivo: {motivo}"
        )

        if selecionados:
            for item in selecionados:
                item.ativo = False
                anterior = str(item.observacoes or "").strip()
                nota_item = (
                    f"{anotacao} "
                    f"Financeiro ID: {item.lancamento_id}. "
                    f"Valor desfeito: R$ {Decimal(str(item.valor_conciliado)):.2f}."
                )
                item.observacoes = (
                    f"{anterior}\n{nota_item}" if anterior else nota_item
                )

            restantes = [
                item for item in ativos if item not in selecionados
            ]
            total_restante = sum(
                (Decimal(str(item.valor_conciliado)) for item in restantes),
                Decimal("0.00"),
            )
            total_extrato = abs(Decimal(str(extrato.valor)))
            if total_restante > total_extrato:
                raise ConciliacaoInvalida(
                    "Alocacoes remanescentes excedem o valor do extrato."
                )

            integral = total_restante == total_extrato
            extrato.conciliado = integral
            extrato.data_conciliacao = (
                max(item.data_conciliacao for item in restantes)
                if integral and restantes else None
            )
            extrato.lancamento_id = (
                restantes[0].lancamento_id
                if integral and len(restantes) == 1 else None
            )

        elif (
            not ativos
            and extrato.conciliado
            and extrato.lancamento_id is not None
            and (
                lancamento_id is None
                or extrato.lancamento_id == lancamento_id
            )
        ):
            # Compativel com extratos 1:1 antigos sem alocacao N:N.
            anterior = str(extrato.observacoes or "").strip()
            nota_legado = (
                f"{anotacao} "
                f"Financeiro ID: {extrato.lancamento_id}. "
                f"Valor desfeito: R$ {abs(Decimal(str(extrato.valor))):.2f}."
            )
            extrato.observacoes = (
                f"{anterior}\n{nota_legado}" if anterior else nota_legado
            )
            extrato.conciliado = False
            extrato.lancamento_id = None
            extrato.data_conciliacao = None

        else:
            raise ConciliacaoInvalida(
                "Nenhum vinculo ativo correspondente para desfazer."
            )

        db.session.commit()
        return {
            "extrato_id": extrato_id,
            "lancamento_id": lancamento_id,
            "alocacoes_desfeitas": len(selecionados),
            "conciliado": bool(extrato.conciliado),
        }

    except Exception:
        db.session.rollback()
        raise
