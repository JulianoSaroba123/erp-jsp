# -*- coding: utf-8 -*-
"""
Script para criar contas bancárias no Render (PostgreSQL)
Execute este script UMA VEZ no Render para popular as contas
"""

from app.app import app
from app.extensoes import db
from app.financeiro.financeiro_model import ContaBancaria
from decimal import Decimal

def criar_contas_render():
    """Cria contas bancárias no Render"""
    with app.app_context():
        print("\n🔍 Verificando contas no Render...")
        
        contas_existentes = ContaBancaria.query.all()
        print(f"📊 Contas existentes: {len(contas_existentes)}")
        
        # Contas padrão
        contas_padrao = [
            {
                'nome': 'Banco do Brasil - Conta Corrente',
                'tipo': 'conta_corrente',
                'banco': 'Banco do Brasil',
                'agencia': '1234-5',
                'numero_conta': '98765-4',
                'saldo_inicial': Decimal('10000.00'),
                'saldo_atual': Decimal('10000.00'),
                'limite_credito': Decimal('5000.00'),
                'ativa': True,
                'ativo': True,
                'principal': True,
                'observacoes': 'Conta principal da empresa'
            },
            {
                'nome': 'Itaú - Cartão Corporativo',
                'tipo': 'conta_corrente',
                'banco': 'Itaú',
                'agencia': '5678',
                'numero_conta': '12345-6',
                'saldo_inicial': Decimal('0.00'),
                'saldo_atual': Decimal('0.00'),
                'limite_credito': Decimal('10000.00'),
                'ativa': True,
                'ativo': True,
                'principal': False,
                'observacoes': 'Cartão corporativo'
            },
            {
                'nome': 'Caixa Geral',
                'tipo': 'caixa',
                'banco': None,
                'agencia': None,
                'numero_conta': None,
                'saldo_inicial': Decimal('500.00'),
                'saldo_atual': Decimal('500.00'),
                'limite_credito': Decimal('0.00'),
                'ativa': True,
                'ativo': True,
                'principal': False,
                'observacoes': 'Caixa para pequenas despesas'
            },
            {
                'nome': 'Banco do Brasil - Salários',
                'tipo': 'conta_corrente',
                'banco': 'Banco do Brasil',
                'agencia': '1234-5',
                'numero_conta': '55555-5',
                'saldo_inicial': Decimal('0.00'),
                'saldo_atual': Decimal('0.00'),
                'limite_credito': Decimal('0.00'),
                'ativa': True,
                'ativo': True,
                'principal': False,
                'observacoes': 'Conta para salários'
            },
            {
                'nome': 'Santander Empresarial',
                'tipo': 'conta_corrente',
                'banco': 'Santander',
                'agencia': '0033',
                'numero_conta': '01000123456-7',
                'saldo_inicial': Decimal('5000.00'),
                'saldo_atual': Decimal('5000.00'),
                'limite_credito': Decimal('3000.00'),
                'ativa': True,
                'ativo': True,
                'principal': False,
                'observacoes': 'Conta secundária'
            }
        ]
        
        print("\n📝 Criando contas bancárias...\n")
        criadas = 0
        
        for dados in contas_padrao:
            # Verificar se já existe
            existe = ContaBancaria.query.filter_by(nome=dados['nome']).first()
            
            if not existe:
                conta = ContaBancaria(**dados)
                db.session.add(conta)
                print(f"  ✅ {dados['nome']}")
                criadas += 1
            else:
                print(f"  ⏭️  {dados['nome']} (já existe)")
        
        if criadas > 0:
            db.session.commit()
            print(f"\n✅ {criadas} conta(s) criada(s) com sucesso!")
        else:
            print(f"\n✅ Todas as contas já existem!")
        
        # Listar todas
        print("\n📋 Contas no sistema:")
        todas = ContaBancaria.query.filter_by(ativo=True).all()
        for c in todas:
            print(f"  • {c.nome} - Ativa: {c.ativa} - Saldo: {c.saldo_formatado}")

if __name__ == '__main__':
    print("=" * 70)
    print("🏦 CRIAÇÃO DE CONTAS BANCÁRIAS - RENDER")
    print("=" * 70)
    criar_contas_render()
    print("\n" + "=" * 70)
    print("✅ Concluído!")
    print("=" * 70)
