# -*- coding: utf-8 -*-
"""Sincronizacao transacional do saldo das contas bancarias.

Este modulo fecha lacunas historicas do ERP em que um lancamento podia nascer
ou ser editado como pago/recebido sem atualizar ``ContaBancaria.saldo_atual``.

A estrategia e por delta: em cada INSERT/UPDATE/DELETE de LancamentoFinanceiro,
o impacto anterior e o novo impacto sao comparados. Assim, mudancas de valor,
tipo, status, conta, ativo ou data de pagamento sao refletidas uma unica vez.

Transferencias bancarias sao ignoradas aqui porque a rota legada ja movimenta
as duas contas explicitamente antes de gravar os lancamentos espelho.
"""

from decimal import Decimal

from sqlalchemy import event, inspect, select, update
from sqlalchemy.orm import object_session

from app.financeiro.financeiro_model import ContaBancaria, LancamentoFinanceiro


_STATUS_QUITADOS = {'pago', 'recebido'}
_TIPOS_ENTRADA = {'receita', 'conta_receber'}
_TIPOS_SAIDA = {'despesa', 'conta_pagar'}
_CATEGORIA_TRANSFERENCIA = 'Transferência Bancária'
_REGISTRADO = False


def _decimal(valor):
    if valor is None:
        return Decimal('0.00')
    return Decimal(str(valor)).quantize(Decimal('0.01'))


def _impacto(*, tipo, status, valor, conta_id, ativo, data_pagamento, categoria):
    """Retorna o impacto assinado do lancamento em uma conta."""
    if not conta_id or not ativo:
        return Decimal('0.00')
    if status not in _STATUS_QUITADOS or data_pagamento is None:
        return Decimal('0.00')
    if categoria == _CATEGORIA_TRANSFERENCIA:
        return Decimal('0.00')

    valor = _decimal(valor)
    if tipo in _TIPOS_ENTRADA:
        return valor
    if tipo in _TIPOS_SAIDA:
        return -valor
    return Decimal('0.00')


def _valor_anterior(target, campo):
    estado = inspect(target)
    historico = estado.attrs[campo].history
    if historico.deleted:
        return historico.deleted[0]
    return getattr(target, campo)


def _snapshot_atual(target):
    return {
        'tipo': target.tipo,
        'status': target.status,
        'valor': target.valor,
        'conta_id': target.conta_bancaria_id,
        'ativo': bool(getattr(target, 'ativo', True)),
        'data_pagamento': target.data_pagamento,
        'categoria': target.categoria,
    }


def _snapshot_anterior(target):
    return {
        'tipo': _valor_anterior(target, 'tipo'),
        'status': _valor_anterior(target, 'status'),
        'valor': _valor_anterior(target, 'valor'),
        'conta_id': _valor_anterior(target, 'conta_bancaria_id'),
        'ativo': bool(_valor_anterior(target, 'ativo')),
        'data_pagamento': _valor_anterior(target, 'data_pagamento'),
        'categoria': _valor_anterior(target, 'categoria'),
    }


def _impacto_snapshot(snapshot):
    return _impacto(
        tipo=snapshot['tipo'],
        status=snapshot['status'],
        valor=snapshot['valor'],
        conta_id=snapshot['conta_id'],
        ativo=snapshot['ativo'],
        data_pagamento=snapshot['data_pagamento'],
        categoria=snapshot['categoria'],
    )


def _conta_padrao_para_os(connection):
    """Escolhe conta principal; se nao houver, aceita a unica conta ativa."""
    tabela = ContaBancaria.__table__
    linhas = connection.execute(
        select(tabela.c.id, tabela.c.principal).where(
            tabela.c.ativo.is_(True),
            tabela.c.ativa.is_(True),
        ).order_by(tabela.c.id)
    ).all()

    principais = [linha.id for linha in linhas if bool(linha.principal)]
    if len(principais) == 1:
        return principais[0]
    if len(linhas) == 1:
        return linhas[0].id
    return None


def _os_recebida_sem_conta(target):
    return (
        getattr(target, 'origem', None) == 'ORDEM_SERVICO'
        and target.conta_bancaria_id is None
        and target.status in _STATUS_QUITADOS
        and target.data_pagamento is not None
    )


def _antes_inserir(mapper, connection, target):
    # As telas de OS nao possuem seletor de conta. Se existir uma conta
    # principal (ou somente uma conta ativa), vincula o recebimento nela.
    if _os_recebida_sem_conta(target):
        conta_id = _conta_padrao_para_os(connection)
        if conta_id is not None:
            target.conta_bancaria_id = conta_id


def _antes_atualizar(mapper, connection, target):
    # Nao retrovincula recebimentos antigos so porque outro campo foi editado.
    # A conta automatica e aplicada apenas na transicao real para quitado.
    if not _os_recebida_sem_conta(target):
        return

    status_anterior = _valor_anterior(target, 'status')
    pagamento_anterior = _valor_anterior(target, 'data_pagamento')
    ja_estava_quitado = (
        status_anterior in _STATUS_QUITADOS and pagamento_anterior is not None
    )
    if ja_estava_quitado:
        return

    conta_id = _conta_padrao_para_os(connection)
    if conta_id is not None:
        target.conta_bancaria_id = conta_id


def _delta_ja_aplicado_manualmente(target, conta_id, delta):
    """Evita duplicar o metodo legado marcar_como_pago().

    Esse metodo altera ``ContaBancaria.saldo_atual`` antes do flush. Quando a
    conta ja esta dirty na mesma sessao exatamente pelo delta esperado, o evento
    nao reaplica a movimentacao.
    """
    sessao = object_session(target)
    if sessao is None or not conta_id or delta == 0:
        return False

    for objeto in list(sessao.dirty):
        if not isinstance(objeto, ContaBancaria) or objeto.id != conta_id:
            continue
        historico = inspect(objeto).attrs.saldo_atual.history
        if not historico.deleted or not historico.added:
            continue
        delta_manual = _decimal(historico.added[-1]) - _decimal(historico.deleted[0])
        if delta_manual == _decimal(delta):
            return True
    return False


def _aplicar_delta(connection, conta_id, delta):
    delta = _decimal(delta)
    if not conta_id or delta == 0:
        return

    tabela = ContaBancaria.__table__
    connection.execute(
        update(tabela)
        .where(tabela.c.id == conta_id)
        .values(saldo_atual=tabela.c.saldo_atual + delta)
    )


def _depois_inserir(mapper, connection, target):
    atual = _snapshot_atual(target)
    delta = _impacto_snapshot(atual)
    if delta == 0:
        return
    if _delta_ja_aplicado_manualmente(target, atual['conta_id'], delta):
        return
    _aplicar_delta(connection, atual['conta_id'], delta)


def _depois_atualizar(mapper, connection, target):
    anterior = _snapshot_anterior(target)
    atual = _snapshot_atual(target)

    # Transferencias sao movimentadas pela rota especifica. Se qualquer lado da
    # edicao for transferencia, mantemos este evento fora do caminho.
    if (
        anterior['categoria'] == _CATEGORIA_TRANSFERENCIA
        or atual['categoria'] == _CATEGORIA_TRANSFERENCIA
    ):
        return

    impacto_anterior = _impacto_snapshot(anterior)
    impacto_atual = _impacto_snapshot(atual)

    deltas = {}
    conta_anterior = anterior['conta_id']
    conta_atual = atual['conta_id']

    if conta_anterior:
        deltas[conta_anterior] = deltas.get(conta_anterior, Decimal('0.00')) - impacto_anterior
    if conta_atual:
        deltas[conta_atual] = deltas.get(conta_atual, Decimal('0.00')) + impacto_atual

    for conta_id, delta in deltas.items():
        delta = _decimal(delta)
        if delta == 0:
            continue
        if _delta_ja_aplicado_manualmente(target, conta_id, delta):
            continue
        _aplicar_delta(connection, conta_id, delta)


def _depois_excluir(mapper, connection, target):
    atual = _snapshot_atual(target)
    if atual['categoria'] == _CATEGORIA_TRANSFERENCIA:
        return
    impacto = _impacto_snapshot(atual)
    if impacto:
        _aplicar_delta(connection, atual['conta_id'], -impacto)


def registrar_eventos_saldo_bancario():
    """Registra os listeners uma unica vez por processo Python."""
    global _REGISTRADO
    if _REGISTRADO:
        return

    event.listen(LancamentoFinanceiro, 'before_insert', _antes_inserir)
    event.listen(LancamentoFinanceiro, 'before_update', _antes_atualizar)
    event.listen(LancamentoFinanceiro, 'after_insert', _depois_inserir)
    event.listen(LancamentoFinanceiro, 'after_update', _depois_atualizar)
    event.listen(LancamentoFinanceiro, 'after_delete', _depois_excluir)
    _REGISTRADO = True
