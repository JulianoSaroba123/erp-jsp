# -*- coding: utf-8 -*-
"""Recebimento real de parcela de OS, independente da conclusão operacional.

A baixa cria/atualiza SOMENTE o título em Contas a Receber. Não soma
ContaBancaria.saldo_atual e não cria ExtratoBancario; a conciliação N:N
existente vincula posteriormente o lançamento ao movimento importado.
"""
from datetime import date
from decimal import Decimal, InvalidOperation
import hmac
import secrets

from flask import abort, current_app, flash, redirect, request, session, url_for
from flask_login import current_user, login_required

from app.extensoes import db
from app.financeiro.financeiro_model import (
    ContaBancaria, HistoricoFinanceiro, LancamentoFinanceiro,
)
from app.financeiro.financeiro_utils import _sincronizar_status_pagamento_os
from app.ordem_servico.ordem_servico_model import OrdemServico, OrdemServicoParcela


FORMAS_VALIDAS = frozenset({
    "pix", "transferencia", "dinheiro", "boleto",
    "cartao_credito", "cartao_debito",
})
CHAVE_CSRF = "_csrf_os_recebimento_v1"
CENTAVO = Decimal("0.01")


class RecebimentoParcelaInvalido(ValueError):
    """Solicitação rejeitada sem confirmar alterações."""


def token_csrf_recebimento():
    """Cria token por sessão; independente de CSRF global opcional."""
    token = session.get(CHAVE_CSRF)
    if not token:
        token = secrets.token_urlsafe(32)
        session[CHAVE_CSRF] = token
    return token


def verificar_csrf_recebimento():
    informado = request.form.get("csrf_os_recebimento", "")
    esperado = session.get(CHAVE_CSRF, "")
    if (not isinstance(esperado, str) or not esperado or
            not hmac.compare_digest(informado.encode('utf-8'), esperado.encode('utf-8'))):
        abort(400, description="Token de segurança do recebimento inválido.")


def _valor_monetario(valor):
    texto = str(valor or "").strip().replace(",", ".")
    try:
        numero = Decimal(texto)
        if not numero.is_finite() or numero <= 0:
            raise InvalidOperation
        quantizado = numero.quantize(CENTAVO)
        if quantizado != numero:
            raise InvalidOperation
    except (InvalidOperation, ValueError, TypeError) as exc:
        raise RecebimentoParcelaInvalido("Valor de recebimento inválido.") from exc
    return quantizado


def registrar_recebimento_parcela(
    *, os_id, parcela_id, data_recebimento, valor_recebido,
    forma_pagamento, conta_bancaria_id, observacao, usuario,
):
    """Altera somente a sessão transacional atual; o chamador confirma/rollback.

    Lock OS primeiro, parcela depois, para serializar com a sincronização
    financeira. Em PostgreSQL, SELECT FOR UPDATE protege a disputa entre
    dois recebimentos da mesma parcela. Concorrência deve ainda ser testada
    em PostgreSQL isolado, pois SQLite ignora FOR UPDATE.
    """
    if not isinstance(data_recebimento, date) or data_recebimento > date.today():
        raise RecebimentoParcelaInvalido("Data efetiva de recebimento inválida ou futura.")
    valor = _valor_monetario(valor_recebido)
    forma = str(forma_pagamento or "").strip().lower()
    if forma not in FORMAS_VALIDAS:
        raise RecebimentoParcelaInvalido("Forma de pagamento não permitida.")
    texto_obs = str(observacao or "").strip()
    if len(texto_obs) > 1000:
        raise RecebimentoParcelaInvalido("Observação excede 1000 caracteres.")
    try:
        conta_id = int(conta_bancaria_id)
    except (TypeError, ValueError) as exc:
        raise RecebimentoParcelaInvalido("Selecione uma conta bancária válida.") from exc
    if conta_id <= 0:
        raise RecebimentoParcelaInvalido("Selecione uma conta bancária válida.")

    ordem = (db.session.query(OrdemServico)
             .filter_by(id=os_id, ativo=True).populate_existing()
             .with_for_update().one_or_none())
    if ordem is None or str(ordem.status or "").lower() in {"cancelada", "cancelado"}:
        raise RecebimentoParcelaInvalido("Ordem de serviço inválida ou cancelada.")

    # Releitura após adquirir o lock: outra transação pode ter quitado uma
    # parcela enquanto esta sessão ainda mantinha objetos antigos em memória.
    parcelas = (db.session.query(OrdemServicoParcela)
                .filter_by(ordem_servico_id=os_id, ativo=True)
                .order_by(OrdemServicoParcela.id)
                .populate_existing().with_for_update().all())
    parcela = next((p for p in parcelas if p.id == parcela_id), None)
    if parcela is None:
        raise RecebimentoParcelaInvalido("Parcela não pertence a esta OS.")

    conta = (db.session.query(ContaBancaria)
             .filter_by(id=conta_id, ativo=True, ativa=True).one_or_none())
    if conta is None:
        raise RecebimentoParcelaInvalido("Conta bancária inexistente ou inativa.")

    valor_parcela = _valor_monetario(parcela.valor)
    if valor != valor_parcela:
        raise RecebimentoParcelaInvalido(
            "O valor deve ser igual ao da parcela. Recebimentos parciais "
            "internos à mesma parcela exigem fluxo próprio."
        )

    existentes = (db.session.query(LancamentoFinanceiro)
                  .filter_by(ordem_servico_parcela_id=parcela.id)
                  .populate_existing().with_for_update().all())
    if any(l.ativo is False for l in existentes):
        raise RecebimentoParcelaInvalido(
            "Existe lançamento histórico inativo vinculado à parcela. "
            "Revisão financeira necessária antes da baixa."
        )
    if len(existentes) > 1:
        raise RecebimentoParcelaInvalido(
            "Mais de um lançamento ativo vinculado à parcela. Revisão financeira necessária."
        )
    lancamento = existentes[0] if existentes else None

    if parcela.pago or parcela.data_pagamento or (
        lancamento is not None and
        (lancamento.status in {"recebido", "pago"} or lancamento.data_pagamento)
    ):
        raise RecebimentoParcelaInvalido("Parcela já recebida. Nenhuma baixa adicional realizada.")

    if lancamento is not None and (
        lancamento.status == "cancelado"
        or lancamento.tipo != "conta_receber"
        or lancamento.ordem_servico_id != ordem.id
        or _valor_monetario(lancamento.valor) != valor_parcela
    ):
        raise RecebimentoParcelaInvalido(
            "Lançamento financeiro divergente. Revisão necessária antes da baixa."
        )

    if lancamento is None:
        lancamento = LancamentoFinanceiro(
            descricao=f"OS {ordem.numero} - {ordem.titulo} - Parcela {parcela.numero_parcela}",
            valor=valor_parcela, tipo="conta_receber",
            status="pendente", origem="ORDEM_SERVICO",
            categoria="Serviços", subcategoria="Ordem de Serviço",
            cliente_id=ordem.cliente_id,
            ordem_servico_id=ordem.id, ordem_servico_parcela_id=parcela.id,
            data_lancamento=ordem.data_abertura or data_recebimento,
            data_vencimento=parcela.data_vencimento,
            numero_parcela=f"{parcela.numero_parcela}/{len(ordem.parcelas)}",
        )
        db.session.add(lancamento)
        db.session.flush()  # ID para o histórico dentro da mesma transação.

    status_anterior = lancamento.status
    # O fato financeiro é registrado, mas não cria um segundo crédito bancário.
    # O marcador persiste para também impedir deltas indevidos em edições futuras.
    lancamento.sem_movimentacao_bancaria = True
    lancamento.status = "recebido"
    lancamento.data_pagamento = data_recebimento
    lancamento.forma_pagamento = forma
    lancamento.conta_bancaria_id = conta.id
    lancamento.usuario_editor = str(usuario)
    lancamento.observacoes = (
        "Recebimento manual confirmado na OS. Conciliar com movimento "
        "real do extrato, sem registrar entrada adicional."
        + (f"\n{texto_obs}" if texto_obs else "")
    )
    parcela.pago = True
    parcela.data_pagamento = data_recebimento
    _sincronizar_status_pagamento_os(ordem, parcelas)
    db.session.add(HistoricoFinanceiro(
        lancamento_id=lancamento.id,
        campo_alterado="status",
        valor_anterior=status_anterior,
        valor_novo="recebido",
        usuario=str(usuario),
        acao="pagamento",
        motivo=(
            f"OS {ordem.numero}; parcela ID {parcela.id}; "
            f"recebimento {data_recebimento.isoformat()}; "
            f"conta bancária ID {conta.id}; forma {forma}; "
            "conciliacao pendente com extrato real."
        ),
    ))
    # Nenhum incremento em ContaBancaria.saldo_atual; nenhum ExtratoBancario.
    return lancamento


def registrar_rotas_recebimento(blueprint):
    @blueprint.route("/<int:id>/parcelas/<int:parcela_id>/receber", methods=["POST"])
    @login_required
    def receber_parcela_os(id, parcela_id):
        destino = lambda: redirect(url_for("ordem_servico.visualizar", id=id))
        if getattr(current_user, "tipo_usuario", None) != "admin":
            abort(403)
        verificar_csrf_recebimento()
        try:
            data_recebimento = date.fromisoformat(
                request.form.get("data_recebimento", "")
            )
            registrar_recebimento_parcela(
                os_id=id, parcela_id=parcela_id,
                data_recebimento=data_recebimento,
                valor_recebido=request.form.get("valor_recebido"),
                forma_pagamento=request.form.get("forma_pagamento"),
                conta_bancaria_id=request.form.get("conta_bancaria_id"),
                observacao=request.form.get("observacao"),
                usuario=getattr(current_user, "id", "admin"),
            )
            db.session.commit()
            flash(
                "Parcela recebida, lançamento financeiro atualizado. "
                "Concilie com o extrato real; nenhum saldo bancário foi somado.",
                "success",
            )
        except (RecebimentoParcelaInvalido, ValueError, TypeError) as exc:
            db.session.rollback()
            flash(str(exc), "warning")
        except Exception:
            db.session.rollback()
            current_app.logger.exception(
                "Falha ao receber parcela %s da OS %s", parcela_id, id
            )
            flash("Erro ao receber parcela. Transação desfeita.", "danger")
        return destino()
