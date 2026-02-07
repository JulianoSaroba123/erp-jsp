# -*- coding: utf-8 -*-
"""
Teste rápido dos endpoints de autocomplete
"""

from app.app import app
import json

def testar_endpoints():
    """Testa os endpoints de consulta"""
    with app.test_client() as client:
        print("\n🧪 Testando endpoints de autocomplete...\n")
        
        # Teste 1: Consulta CEP
        print("1️⃣ Testando consulta de CEP...")
        response = client.get('/cliente/api/consultar-cep/01310100')
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = json.loads(response.data)
            print(f"   Sucesso: {data.get('success')}")
            if data.get('success'):
                print(f"   Endereço: {data['data'].get('logradouro')}, {data['data'].get('bairro')}")
                print(f"   Cidade: {data['data'].get('cidade')}/{data['data'].get('uf')}")
        else:
            print(f"   ❌ Erro: {response.data}")
        
        print()
        
        # Teste 2: Consulta CNPJ (usando um CNPJ de teste)
        print("2️⃣ Testando consulta de CNPJ...")
        # CNPJ da Receita Federal para teste: 00000000000191
        response = client.get('/cliente/api/consultar-cnpj/00000000000191')
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = json.loads(response.data)
            print(f"   Sucesso: {data.get('success')}")
            if data.get('success'):
                print(f"   Nome: {data['data'].get('nome')}")
                print(f"   Fantasia: {data['data'].get('fantasia')}")
            elif data.get('error'):
                print(f"   Mensagem: {data.get('error')}")
        else:
            print(f"   ❌ Erro: {response.data}")

if __name__ == '__main__':
    print("=" * 70)
    print("🧪 TESTE DE ENDPOINTS DE AUTOCOMPLETE")
    print("=" * 70)
    testar_endpoints()
    print("\n" + "=" * 70)
    print("✅ Testes concluídos!")
    print("=" * 70)
