#!/usr/bin/env python3
"""
Script simples para testar POST de atualização
"""

import requests
import time

BASE_URL = "http://127.0.0.1:5000"

def teste_simples_post():
    # Dados mínimos para teste
    dados = {
        'cliente_id': '7',
        'solicitante': 'TESTE ATUALIZADO',
        'data_emissao': '2025-09-26',
        'prioridade': 'Urgente',
        'status': 'Em Andamento',
        'servicos_json': '[]',
        'produtos_json': '[]',
        'parcelas_json': '[]'
    }
    
    try:
        print("Enviando POST para atualização...")
        response = requests.post(f"{BASE_URL}/ordens/1/editar", data=dados, timeout=10)
        print(f"Status: {response.status_code}")
        print(f"Headers: {response.headers.get('Location', 'No redirect')}")
        
        if response.status_code == 302:
            print("✅ SUCESSO - Redirect detectado!")
            return True
        else:
            print("❌ Sem redirect - verificar resposta")
            return False
            
    except Exception as e:
        print(f"❌ Erro: {e}")
        return False

if __name__ == "__main__":
    print("🧪 TESTE SIMPLES DE ATUALIZAÇÃO")
    print("=" * 40)
    
    # Aguardar um pouco para estabilizar
    time.sleep(2)
    
    sucesso = teste_simples_post()
    
    if sucesso:
        print("✅ TESTE OK!")
    else:
        print("❌ TESTE FALHOU!")