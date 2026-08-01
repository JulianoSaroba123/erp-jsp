# -*- coding: utf-8 -*-
"""
Módulo de Compatibilidade Financeira
=====================================

Funções de normalização e compatibilidade para consolidação financeira.
Garante consistência no processamento de dados de múltiplas fontes.

Regras implementadas:
- Normalização de tipos (Receita/Despesa)
- Normalização de status (Pago/Pendente)
- Conversão segura para Decimal
- Formatação monetária
"""

from __future__ import annotations
from decimal import Decimal, InvalidOperation

# Conjuntos de tipos aceitos como receita
TIPOS_RECEITA = {
    'receita',
    'receitas',
    'entrada',
    'entradas',
    'credito',
    'crédito',
    'conta a receber',
    'contas a receber',
    'conta_receber',
}

# Conjuntos de tipos aceitos como despesa
TIPOS_DESPESA = {
    'despesa',
    'despesas',
    'saida',
    'saída',
    'debito',
    'débito',
    'conta a pagar',
    'contas a pagar',
    'conta_pagar',
}

# Conjuntos de status considerados como pagos
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

# Conjuntos de status considerados como pendentes
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
    """
    Normaliza texto removendo espaços e tratando None.

    Args:
        valor: Valor a ser normalizado

    Returns:
        String normalizada ou string vazia
    """
    if valor is None:
        return ''
    texto = str(valor).strip()
    if texto.lower() == 'none':
        return ''
    return texto


def normalizar_chave(valor) -> str:
    """
    Normaliza texto para uso como chave de comparação (casefold).

    Args:
        valor: Valor a ser normalizado

    Returns:
        String em caixa baixa para comparação
    """
    return normalizar_texto(valor).casefold()


def normalizar_tipo(valor) -> str:
    """
    Normaliza tipo de lançamento para Receita ou Despesa.

    Regra 4: Garantir consistência na classificação de tipos.

    Args:
        valor: Tipo do lançamento

    Returns:
        'Receita', 'Despesa' ou texto original capitalizado
    """
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
    """
    Verifica se o tipo representa uma receita.

    Args:
        valor: Tipo a verificar

    Returns:
        True se for receita
    """
    return normalizar_chave(valor) in TIPOS_RECEITA


def tipo_eh_despesa(valor) -> bool:
    """
    Verifica se o tipo representa uma despesa.

    Args:
        valor: Tipo a verificar

    Returns:
        True se for despesa
    """
    return normalizar_chave(valor) in TIPOS_DESPESA


def normalizar_status(valor) -> str:
    """
    Normaliza status de lançamento para Pago ou Pendente.

    Regra 1 e 3: Status normalizado para cálculo de realizado.

    Args:
        valor: Status do lançamento

    Returns:
        'Pago', 'Pendente' ou texto original capitalizado
    """
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
    """
    Verifica se o status representa pagamento efetivado.

    Regra 1: Usado para determinar se integra o realizado.

    Args:
        valor: Status a verificar

    Returns:
        True se status indica pagamento
    """
    return normalizar_chave(valor) in STATUS_PAGO


def status_eh_pendente(valor) -> bool:
    """
    Verifica se o status representa pendência.

    Regra 2: Usado para cálculo de pendências e atrasos.

    Args:
        valor: Status a verificar

    Returns:
        True se status indica pendência
    """
    return normalizar_chave(valor) in STATUS_PENDENTE or normalizar_status(valor) == 'Pendente'


def decimal_valor(valor) -> Decimal:
    """
    Converte valor para Decimal de forma segura.

    Regra 4: Cálculos monetários devem usar Decimal.

    Args:
        valor: Valor a converter (pode ser None, string, float, int ou Decimal)

    Returns:
        Decimal válido ou Decimal('0') em caso de erro
    """
    if valor is None:
        return Decimal('0')
    if isinstance(valor, Decimal):
        return valor
    try:
        return Decimal(str(valor))
    except (InvalidOperation, ValueError, TypeError):
        return Decimal('0')


def valor_em_moeda(valor: Decimal | float | int | None) -> str:
    """
    Formata valor como moeda brasileira (R$).

    Args:
        valor: Valor a formatar

    Returns:
        String formatada como 'R$ 1.234,56'
    """
    bruto = decimal_valor(valor)
    return f'R$ {bruto:,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.')
