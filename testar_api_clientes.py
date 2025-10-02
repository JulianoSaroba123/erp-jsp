#!/usr/bin/env python3
"""
Teste direto da API de clientes
"""

import requests
import json

def testar_api():
    print("=== TESTE DA API DE CLIENTES ===")
    
    # URLs para testar
    urls = [
        "http://127.0.0.1:5000/clientes/api/",
        "http://127.0.0.1:5000/clientes/api/busca?q=SAROBA",
        "http://127.0.0.1:5000/clientes/api/busca?q=MR",
        "http://127.0.0.1:5000/clientes/api/busca?q=",  # Busca vazia
    ]
    
    for url in urls:
        print(f"\n🔗 Testando: {url}")
        try:
            response = requests.get(url, timeout=5)
            print(f"📡 Status: {response.status_code}")
            print(f"📄 Headers: {dict(response.headers)}")
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    print(f"✅ JSON válido!")
                    print(f"📊 Dados: {json.dumps(data, indent=2, ensure_ascii=False)}")
                except Exception as e:
                    print(f"❌ Erro no JSON: {e}")
                    print(f"📄 Texto bruto: {response.text[:500]}")
            else:
                print(f"❌ Erro HTTP: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Erro na requisição: {e}")

if __name__ == "__main__":
    testar_api()