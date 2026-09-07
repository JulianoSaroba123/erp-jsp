# -*- coding: utf-8 -*-
"""Reconcilia somente ``saldo_atual`` de uma conta bancaria.

Uso seguro em duas etapas:

  python scripts_manutencao/reconciliar_saldo_conta.py --conta-id 1 --target 3870.19

Depois de conferir o diagnostico e o saldo real do banco naquele instante:

  python scripts_manutencao/reconciliar_saldo_conta.py --conta-id 1 \
      --target 3870.19 --expected-current 15976.92 --apply

O script NAO altera saldo_inicial, lancamentos, datas, status ou DRE. A
reconciliacao serve apenas como novo ponto de verdade operacional para o saldo
corrente depois que o motor transacional de saldos estiver corrigido.
"""

import argparse
import os
import sys
from decimal import Decimal, InvalidOperation

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.app import create_app
from app.extensoes import db
from app.financeiro.financeiro_model import ContaBancaria


CENT = Decimal('0.01')


def moeda(texto):
    try:
        return Decimal(str(texto).replace(',', '.')).quantize(CENT)
    except (InvalidOperation, ValueError, TypeError):
        raise SystemExit(f'Valor monetario invalido: {texto!r}')


def br(valor):
    valor = Decimal(str(valor or 0)).quantize(CENT)
    return f'R$ {valor:,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.')


def main():
    parser = argparse.ArgumentParser(description='Reconcilia saldo atual de conta bancaria')
    parser.add_argument('--conta-id', type=int, required=True)
    parser.add_argument('--target', required=True, help='Saldo real do banco no instante da reconciliacao')
    parser.add_argument('--expected-current', help='Saldo atual esperado no ERP; obrigatorio com --apply')
    parser.add_argument('--apply', action='store_true')
    args = parser.parse_args()

    target = moeda(args.target)
    expected = moeda(args.expected_current) if args.expected_current is not None else None

    app = create_app(os.environ.get('FLASK_CONFIG', 'production'))
    with app.app_context():
        conta = db.session.get(ContaBancaria, args.conta_id)
        if conta is None:
            raise SystemExit(f'Conta id={args.conta_id} nao encontrada.')

        atual = moeda(conta.saldo_atual)
        inicial = moeda(conta.saldo_inicial)
        delta = target - atual

        print('=' * 78)
        print('RECONCILIACAO DE SALDO BANCARIO')
        print('=' * 78)
        print(f'Conta: id={conta.id} nome={conta.nome!r} ativa={conta.ativa} principal={conta.principal}')
        print(f'Saldo inicial historico: {br(inicial)}')
        print(f'Saldo atual no ERP:      {br(atual)}')
        print(f'Saldo real informado:    {br(target)}')
        print(f'Ajuste necessario:       {br(delta)}')
        print('')
        print('IMPORTANTE: saldo_inicial e lancamentos NAO serao alterados.')

        if not args.apply:
            print('MODO DIAGNOSTICO: nenhuma alteracao realizada.')
            print('Para aplicar, repita com --expected-current <saldo acima> --apply.')
            print('=' * 78)
            return

        if expected is None:
            raise SystemExit('--expected-current e obrigatorio com --apply.')

        if atual != expected:
            raise SystemExit(
                'ABORTADO: saldo do ERP mudou desde a conferencia. '
                f'Esperado {br(expected)}, encontrado {br(atual)}. '
                'Confira novamente o banco e rode primeiro em modo diagnostico.'
            )

        # Guard rail adicional: nao aplica sobre conta desativada.
        if not bool(conta.ativo) or not bool(conta.ativa):
            raise SystemExit('ABORTADO: a conta esta inativa/desativada.')

        conta.saldo_atual = target
        db.session.commit()
        db.session.refresh(conta)

        final = moeda(conta.saldo_atual)
        if final != target:
            db.session.rollback()
            raise SystemExit(
                f'FALHA DE VALIDACAO: esperado {br(target)}, persistido {br(final)}.'
            )

        print('')
        print(f'RECONCILIACAO CONCLUIDA: saldo_atual = {br(final)}')
        print('Saldo inicial e historico financeiro foram preservados.')
        print('=' * 78)


if __name__ == '__main__':
    main()
