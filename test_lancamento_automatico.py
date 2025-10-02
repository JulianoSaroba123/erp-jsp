#!/usr/bin/env python3
"""
Script de teste para a funcionalidade de lançamento automático
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from aplicacao import create_app
from aplicacao.extensoes import db
from aplicacao.ordem_servico.os_model import OrdemServico
from aplicacao.financeiro.financeiro_model import LancamentoFinanceiro
from aplicacao.cliente.cliente_model import Cliente
from datetime import datetime

def test_lancamento_automatico():
    """Testa a criação automática de lançamento financeiro"""
    
    # Criar app Flask
    app = create_app()
    
    with app.app_context():
        print("=== TESTE DE LANÇAMENTO AUTOMÁTICO ===")
        
        # 1. Buscar ou criar um cliente de teste
        cliente = Cliente.query.first()
        if not cliente:
            print("❌ Nenhum cliente encontrado. Crie um cliente primeiro.")
            return
        
        print(f"✅ Cliente encontrado: {cliente.nome} (ID: {cliente.id})")
        
        # 2. Criar uma OS de teste
        nova_os = OrdemServico(
            cliente_id=cliente.id,
            tipo_servico="Teste Automático",
            status="Aberta",
            status_pagamento="pendente",
            prioridade="Média",
            valor_total=500.00,
            data_emissao=datetime.now().date(),
            equipamento_nome="Equipamento Teste",
            equipamento_problema="Problema de teste"
        )
        
        db.session.add(nova_os)
        db.session.commit()
        
        print(f"✅ OS criada: {nova_os.codigo} - Status: {nova_os.status}, Pagamento: {nova_os.status_pagamento}")
        
        # 3. Verificar que não há lançamento ainda
        lancamentos_antes = LancamentoFinanceiro.query.filter_by(
            categoria=f'Ordem de Serviço {nova_os.codigo}'
        ).count()
        print(f"📊 Lançamentos antes: {lancamentos_antes}")
        
        # 4. Atualizar OS para Concluída mas ainda pendente
        nova_os.status = "Concluída"
        nova_os.status_pagamento = "pendente"
        db.session.commit()
        
        lancamento = nova_os.criar_lancamento_financeiro()
        print(f"🔄 OS concluída mas pendente - Lançamento criado: {'Sim' if lancamento else 'Não'}")
        
        # 5. Atualizar OS para pago
        nova_os.status_pagamento = "pago"
        db.session.commit()
        
        lancamento = nova_os.criar_lancamento_financeiro()
        if lancamento:
            print(f"✅ Lançamento automático criado!")
            print(f"   - Tipo: {lancamento.tipo}")
            print(f"   - Categoria: {lancamento.categoria}")
            print(f"   - Valor: R$ {lancamento.valor}")
            print(f"   - Status: {lancamento.status}")
        else:
            print("❌ Nenhum lançamento foi criado")
        
        # 6. Tentar criar novamente (deve evitar duplicados)
        lancamento_duplicado = nova_os.criar_lancamento_financeiro()
        if lancamento_duplicado and lancamento_duplicado.id == lancamento.id:
            print("✅ Controle de duplicados funcionando - mesmo lançamento retornado")
        else:
            print("❌ Problema no controle de duplicados")
        
        # 7. Verificar total de lançamentos
        lancamentos_depois = LancamentoFinanceiro.query.filter_by(
            categoria=f'Ordem de Serviço {nova_os.codigo}'
        ).count()
        print(f"📊 Lançamentos depois: {lancamentos_depois}")
        
        # 8. Limpeza (opcional)
        print(f"\n🗑️  Para limpar o teste, delete:")
        print(f"   - OS: {nova_os.codigo} (ID: {nova_os.id})")
        if lancamento:
            print(f"   - Lançamento: {lancamento.categoria} (ID: {lancamento.id})")
        
        print("\n=== TESTE CONCLUÍDO ===")

if __name__ == "__main__":
    test_lancamento_automatico()