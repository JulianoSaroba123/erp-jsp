# -*- coding: utf-8 -*-
"""Sincronizacao transacional do saldo das contas bancarias.

Fecha lacunas historicas em que um lancamento podia nascer ou ser editado como
pago/recebido sem atualizar ``ContaBancaria.saldo_atual``.

A estrategia e por delta: para cada INSERT/UPDATE/DELETE, o impacto persistido
anterior e o novo impacto sao comparados. O snapshot anterior e lido diretamente
do banco no ``before_update`` para funcionar mesmo quando o objeto ORM esta
expirado ou quando ocorre autoflush.

Transferencias bancarias sao ignoradas aqui porque a rota legada ja movimenta
as duas contas explicitamente antes de gravar os lancamentos espelho.
"""

from decimal import Decimal
from functools import wraps

from sqlalchemy import event, select, update

from app.financeiro.financeiro_model import ContaBancaria, LancamentoFinanceiro


_STATUS_QUITADOS = {'pago', 'recebido'}
_TIPOS_ENTRADA = {'receita', 'conta_receber'}
_TIPOS_SAIDA = {'despesa', 'conta_pagar'}
_CATEGORIA_TRANSFERENCIA = 'Transferência Bancária'
_ATTR_SNAPSHOT = '_saldo_bancario_snapshot_anterior'
_ATTR_SKIP = '_saldo_bancario_event_skip'
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


def _snapshot_persistido(connection, target):
    """Le o estado antigo diretamente da linha antes do UPDATE ORM."""
    tabela = LancamentoFinanceiro.__table__
    linha = connection.execute(
        select(
            tabela.c.tipo,
            tabela.c.status,
            tabela.c.valor,
            tabela.c.conta_bancaria_id,
            tabela.c.ativo,
            tabela.c.data_pagamento,
            tabela.c.categoria,
        ).where(tabela.c.id == target.id)
    ).mappings().first()

    if linha is None:
        return None

    return {
        'tipo': linha['tipo'],
        'status': linha['status'],
        'valor': linha['valor'],
        'conta_id': linha['conta_bancaria_id'],
        'ativo': bool(linha['ativo']),
        'data_pagamento': linha['data_pagamento'],
        'categoria': linha['categoria'],
    }


def _impacto_snapshot(snapshot):
    if not snapshot:
        return Decimal('0.00')
    return _impacto(
        tipo=snapshot['tipo'],
        status=snapshot['status'],
        valor=snapshot['valor'],
        conta_id=snapshot['conta_id'],
        ativo=snapshot['ativo'],
        data_pagamento=snapshot['data_pagamento'],
        categoria=snapshot['categoria'],
    )


def _snapshot_quitado(snapshot):
    return bool(
        snapshot
        and snapshot['status'] in _STATUS_QUITADOS
        and snapshot['data_pagamento'] is not None
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
    # principal (ou somente uma conta ativa), vincula o NOVO recebimento nela.
    if _os_recebida_sem_conta(target):
        conta_id = _conta_padrao_para_os(connection)
        if conta_id is not None:
            target.conta_bancaria_id = conta_id


def _antes_atualizar(mapper, connection, target):
    anterior = _snapshot_persistido(connection, target)
    setattr(target, _ATTR_SNAPSHOT, anterior)

    # Nao retrovincula recebimentos historicos apenas porque outro campo mudou.
    # Vinculo automatico so ocorre na transicao real de nao quitado -> quitado.
    if not _os_recebida_sem_conta(target):
        return
    if _snapshot_quitado(anterior):
        return

    conta_id = _conta_padrao_para_os(connection)
    if conta_id is not None:
        target.conta_bancaria_id = conta_id


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
    if bool(getattr(target, _ATTR_SKIP, False)):
        return
    atual = _snapshot_atual(target)
    delta = _impacto_snapshot(atual)
    _aplicar_delta(connection, atual['conta_id'], delta)


def _depois_atualizar(mapper, connection, target):
    anterior = getattr(target, _ATTR_SNAPSHOT, None)
    atual = _snapshot_atual(target)

    try:
        if bool(getattr(target, _ATTR_SKIP, False)):
            return

        # Transferencias sao movimentadas pela rota especifica. Se qualquer lado
        # for transferencia, este motor fica deliberadamente fora do caminho.
        if (
            (anterior and anterior['categoria'] == _CATEGORIA_TRANSFERENCIA)
            or atual['categoria'] == _CATEGORIA_TRANSFERENCIA
        ):
            return

        impacto_anterior = _impacto_snapshot(anterior)
        impacto_atual = _impacto_snapshot(atual)

        deltas = {}
        conta_anterior = anterior['conta_id'] if anterior else None
        conta_atual = atual['conta_id']

        if conta_anterior:
            deltas[conta_anterior] = (
                deltas.get(conta_anterior, Decimal('0.00')) - impacto_anterior
            )
        if conta_atual:
            deltas[conta_atual] = (
                deltas.get(conta_atual, Decimal('0.00')) + impacto_atual
            )

        for conta_id, delta in deltas.items():
            _aplicar_delta(connection, conta_id, delta)
    finally:
        if hasattr(target, _ATTR_SNAPSHOT):
            delattr(target, _ATTR_SNAPSHOT)


def _depois_excluir(mapper, connection, target):
    if bool(getattr(target, _ATTR_SKIP, False)):
        return
    atual = _snapshot_atual(target)
    if atual['categoria'] == _CATEGORIA_TRANSFERENCIA:
        return
    impacto = _impacto_snapshot(atual)
    _aplicar_delta(connection, atual['conta_id'], -impacto)


def _proteger_metodo_legado_marcar_como_pago():
    """Evita dupla baixa no metodo legado que ja altera saldo manualmente.

    O metodo atual ``LancamentoFinanceiro.marcar_como_pago`` consulta/atualiza
    ``ContaBancaria`` e pode disparar autoflush do lancamento antes da alteracao
    manual da conta. Por isso o guard precisa existir ANTES de chamar o metodo.

    Se o lancamento ainda nao possui conta (caso comum de OS legada/automatica),
    o evento continua habilitado: no before_update ele pode vincular a conta
    padrao e aplicar o delta corretamente.
    """
    original = LancamentoFinanceiro.marcar_como_pago
    if bool(getattr(original, '_saldo_bancario_protegido', False)):
        return

    @wraps(original)
    def protegido(self, *args, **kwargs):
        deve_pular_evento = bool(self.conta_bancaria_id)
        setattr(self, _ATTR_SKIP, deve_pular_evento)
        try:
            return original(self, *args, **kwargs)
        finally:
            setattr(self, _ATTR_SKIP, False)

    protegido._saldo_bancario_protegido = True
    LancamentoFinanceiro.marcar_como_pago = protegido


def registrar_eventos_saldo_bancario():
    """Registra listeners e guard legado uma unica vez por processo Python."""
    global _REGISTRADO
    if _REGISTRADO:
        return

    _proteger_metodo_legado_marcar_como_pago()
    event.listen(LancamentoFinanceiro, 'before_insert', _antes_inserir)
    event.listen(LancamentoFinanceiro, 'before_update', _antes_atualizar)
    event.listen(LancamentoFinanceiro, 'after_insert', _depois_inserir)
    event.listen(LancamentoFinanceiro, 'after_update', _depois_atualizar)
    event.listen(LancamentoFinanceiro, 'after_delete', _depois_excluir)
    _REGISTRADO = True
