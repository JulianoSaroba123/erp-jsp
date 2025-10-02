#!/usr/bin/env python3
"""
Script para testar as rotas da aplicação de ordem de serviço
"""

import requests
import json

BASE_URL = "http://127.0.0.1:5000"

def test_route(path, method='GET'):
    """Testa uma rota específica"""
    try:
        url = f"{BASE_URL}{path}"
        if method == 'GET':
            response = requests.get(url)
        elif method == 'POST':
            response = requests.post(url)
        
        print(f"[{method}] {path} -> {response.status_code} {response.reason}")
        
        # Verificar se é HTML e contém nosso comentário de debug
        if response.headers.get('content-type', '').startswith('text/html'):
            if 'TESTE CACHE: ARQUIVO ATUAL' in response.text:
                print("  ✅ Template ATUALIZADO encontrado!")
            elif 'Autocomplete de Clientes IMPLEMENTADO' in response.text:
                print("  ✅ Template com autocomplete ENCONTRADO!")
            else:
                print("  ❌ Template SEM marcadores de teste")
                
            # Verificar se há o JavaScript de autocomplete
            if 'setupClienteSelection' in response.text:
                print("  ✅ JavaScript setupClienteSelection ENCONTRADO!")
            else:
                print("  ❌ JavaScript setupClienteSelection NÃO ENCONTRADO")
        
        return response.status_code
    except Exception as e:
        print(f"[{method}] {path} -> ERRO: {str(e)}")
        return None

def main():
    print("=== TESTE DE ROTAS - ORDEM DE SERVIÇO ===\n")
    
    # Testar rotas principais
    routes_to_test = [
        '/os',           # Lista principal
        '/os/',          # Lista com slash
        '/os/nova',      # Nova OS (nossa rota)
        '/ordens',       # Lista alternativa
        '/ordens/nova',  # Nova ordem alternativa
    ]
    
    for route in routes_to_test:
        test_route(route)
        print()

if __name__ == "__main__":
    main()