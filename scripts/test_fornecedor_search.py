#!/usr/bin/env python3
"""Script para testar a busca de fornecedores."""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from aplicacao import create_app
import requests

def testar_busca_fornecedor():
    app = create_app()
    with app.test_client() as client:
        try:
            # Testar busca vazia
            print("=== Teste 1: Busca com termo 'Tech' ===")
            response = client.get('/produtos/fornecedor_buscar?q=Tech')
            print(f"Status: {response.status_code}")
            print(f"Response: {response.json}")
            
            print("\n=== Teste 2: Busca com termo 'Mega' ===")
            response = client.get('/produtos/fornecedor_buscar?q=Mega')
            print(f"Status: {response.status_code}")
            print(f"Response: {response.json}")
            
            print("\n=== Teste 3: Busca com termo 'Global' ===")
            response = client.get('/produtos/fornecedor_buscar?q=Global')
            print(f"Status: {response.status_code}")
            print(f"Response: {response.json}")
            
            print("\n=== Teste 4: Busca sem termo ===")
            response = client.get('/produtos/fornecedor_buscar')
            print(f"Status: {response.status_code}")
            print(f"Response: {response.json}")
            
        except Exception as e:
            print(f"Erro: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    testar_busca_fornecedor()