#!/usr/bin/env python3
"""
Teste para verificar se os clientes estão sendo carregados nas rotas da OS
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from aplicacao import create_app
from aplicacao.extensoes import db
from aplicacao.cliente.cliente_model import Cliente

def test_clientes_rotas():
    """Testa se existem clientes para o autocomplete"""
    
    app = create_app()
    
    with app.app_context():
        print("=== TESTE DE CLIENTES PARA AUTOCOMPLETE ===")
        
        # Verificar quantos clientes existem
        clientes = Cliente.query.filter_by(ativo=True).order_by(Cliente.nome).all()
        
        print(f"✅ Total de clientes ativos: {len(clientes)}")
        
        if len(clientes) > 0:
            print("📋 Primeiros 5 clientes:")
            for i, cliente in enumerate(clientes[:5]):
                print(f"   {i+1}. {cliente.nome} - {cliente.cpf_cnpj or 'Sem CPF/CNPJ'}")
        else:
            print("❌ Nenhum cliente encontrado!")
            print("   Você precisa cadastrar pelo menos um cliente primeiro.")
        
        print("\n=== TESTE CONCLUÍDO ===")

if __name__ == "__main__":
    test_clientes_rotas()