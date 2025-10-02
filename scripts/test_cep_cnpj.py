#!/usr/bin/env python3
"""Script para testar as APIs de CEP e CNPJ."""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from aplicacao import create_app

def testar_apis():
    app = create_app()
    with app.test_client() as client:
        try:
            print("=== Teste 1: Busca por CEP válido (01310-100) ===")
            response = client.get('/fornecedores/api/buscar_cep/01310-100')
            print(f"Status: {response.status_code}")
            print(f"Response: {response.json}")
            
            print("\n=== Teste 2: Busca por CEP inválido (00000-000) ===")
            response = client.get('/fornecedores/api/buscar_cep/00000-000')
            print(f"Status: {response.status_code}")
            print(f"Response: {response.json}")
            
            print("\n=== Teste 3: Busca por CNPJ válido (exemplo fictício) ===")
            # CNPJ fictício para teste - na prática você usaria um real
            response = client.get('/fornecedores/api/buscar_cnpj/11222333000181')
            print(f"Status: {response.status_code}")
            print(f"Response: {response.json}")
            
            print("\n=== Teste 4: Busca por CNPJ inválido ===")
            response = client.get('/fornecedores/api/buscar_cnpj/123')
            print(f"Status: {response.status_code}")
            print(f"Response: {response.json}")
            
        except Exception as e:
            print(f"Erro: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    testar_apis()