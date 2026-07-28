from __future__ import annotations

from decimal import Decimal, InvalidOperation

TIPOS_RECEITA = {
    'receita',
    'receitas',
    'entrada',
    'entradas',
    'credito',
    'crédito',
    'conta a receber',
    'contas a receber',
}

TIPOS_DESPESA = {
    'despesa',
    'despesas',
    'saida',
    'saída',
    'debito',
    'débito',
    'conta a pagar',
    'contas a pagar',
}

STATUS_PAGO = {
    'pago',
    'paga',
    'recebido',
    'recebida',
    'quitado',
    'quitada',
    'baixado',
    'baixada',
    'liquidado',
    'liquidada',
}

STATUS_PENDENTE = {
    'pendente',
    'pendentes',
    'aberto',
    'aberta',
    'em aberto',
    'a receber',
    'a pagar',
    'atrasado',
    'atrasada',
    'vencido',
    'vencida',
}


def normalizar_texto(valor) -> str:
    if valor is None:
        return ''
    texto = str(valor).strip()
    if texto.lower() == 'none':
        return ''
    return texto


def normalizar_chave(valor) -> str:
    return normalizar_texto(valor).casefold()


def normalizar_tipo(valor) -> str:
    chave = normalizar_chave(valor)
    if chave in TIPOS_RECEITA:
        return 'Receita'
    if chave in TIPOS_DESPESA:
        return 'Despesa'
    texto = normalizar_texto(valor)
    if not texto:
        return ''
    return texto[:1].upper() + texto[1:].lower()


def tipo_eh_receita(valor) -> bool:
    return normalizar_chave(valor) in TIPOS_RECEITA


def tipo_eh_despesa(valor) -> bool:
    return normalizar_chave(valor) in TIPOS_DESPESA


def normalizar_status(valor) -> str:
    chave = normalizar_chave(valor)
    if chave in STATUS_PAGO:
        return 'Pago'
    if chave in STATUS_PENDENTE:
        return 'Pendente'
    texto = normalizar_texto(valor)
    if not texto:
        return 'Pendente'
    return texto[:1].upper() + texto[1:].lower()


def status_eh_pago(valor) -> bool:
    return normalizar_chave(valor) in STATUS_PAGO


def status_eh_pendente(valor) -> bool:
    return normalizar_chave(valor) in STATUS_PENDENTE or normalizar_status(valor) == 'Pendente'


def decimal_valor(valor) -> Decimal:
    if valor is None:
        return Decimal('0')
    if isinstance(valor, Decimal):
        return valor
    try:
        return Decimal(str(valor))
    except (InvalidOperation, ValueError, TypeError):
        return Decimal('0')


def valor_em_moeda(valor: Decimal | float | int | None) -> str:
    bruto = decimal_valor(valor)
    return f'R$ {bruto:,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.')
