#!/usr/bin/env python3
"""
Script para descobrir EXATAMENTE qual rota está sendo chamada
"""

import requests

def test_direct_access():
    """Testa acesso direto às URLs"""
    
    urls_to_test = [
        'http://127.0.0.1:5000/os/nova',
        'http://127.0.0.1:5000/ordens/nova',
        'http://127.0.0.1:5000/os',
        'http://127.0.0.1:5000/ordens',
        'http://127.0.0.1:5000/',
    ]
    
    for url in urls_to_test:
        try:
            print(f"\n=== TESTANDO: {url} ===")
            response = requests.get(url, timeout=5)
            print(f"Status: {response.status_code}")
            
            if response.status_code == 200:
                content = response.text
                
                # Verificar marcadores específicos
                if 'TESTE CACHE: ARQUIVO ATUAL' in content:
                    print("✅ ENCONTRADO: Template com TESTE CACHE")
                elif 'setupClienteSelection' in content:
                    print("✅ ENCONTRADO: JavaScript setupClienteSelection")
                else:
                    print("❌ Nenhum marcador encontrado")
                
                # Verificar se tem formulário de OS
                if 'name="cliente_id"' in content:
                    print("✅ ENCONTRADO: Campo cliente_id")
                elif 'Nova Ordem de Serviço' in content:
                    print("✅ ENCONTRADO: Título Nova Ordem de Serviço")
                elif 'form-control' in content:
                    print("✅ ENCONTRADO: Formulário Bootstrap")
                else:
                    print("❌ Nenhum formulário encontrado")
                    
        except Exception as e:
            print(f"❌ ERRO: {str(e)}")

if __name__ == "__main__":
    test_direct_access()