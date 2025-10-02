#!/usr/bin/env python3
"""
Teste simples das rotas de Ordem de Servico
"""

import requests
import json
from datetime import datetime

def teste_basico():
    """Teste basico das rotas principais"""
    base_url = "http://127.0.0.1:5000"
    
    print("=== TESTE BASICO DO CRUD ORDEM DE SERVICO ===")
    
    # Teste 1: API JSON de ordens (mais simples)
    try:
        print("\n1. Testando API JSON...")
        response = requests.get(f"{base_url}/ordens/api/ordens", timeout=5)
        if response.status_code == 200:
            ordens = response.json()
            print(f"   ✓ API funcionando - {len(ordens)} ordens encontradas")
        else:
            print(f"   ✗ API falhou - Status: {response.status_code}")
    except Exception as e:
        print(f"   ✗ Erro na API: {str(e)[:100]}")
    
    # Teste 2: Pagina de listagem
    try:
        print("\n2. Testando pagina de listagem...")
        response = requests.get(f"{base_url}/ordens/", timeout=5)
        if response.status_code == 200:
            print("   ✓ Listagem funcionando")
        else:
            print(f"   ✗ Listagem falhou - Status: {response.status_code}")
    except Exception as e:
        print(f"   ✗ Erro na listagem: {str(e)[:100]}")
    
    # Teste 3: Pagina de nova ordem
    try:
        print("\n3. Testando pagina de nova ordem...")
        response = requests.get(f"{base_url}/ordens/nova", timeout=5)
        if response.status_code == 200:
            print("   ✓ Formulario de nova ordem funcionando")
        else:
            print(f"   ✗ Nova ordem falhou - Status: {response.status_code}")
    except Exception as e:
        print(f"   ✗ Erro no formulario: {str(e)[:100]}")
    
    # Teste 4: Criacao de ordem (POST)
    try:
        print("\n4. Testando criacao de ordem...")
        dados = {
            'cliente_id': '7',  # SAROBA
            'solicitante': 'Teste CRUD Automatico',
            'contato': '(11) 99999-1234',
            'data_emissao': datetime.now().strftime('%Y-%m-%d'),
            'previsao_conclusao': '2025-12-31',
            'prioridade': 'Media',
            'status': 'Aberta',
            'tipo_servico': 'Teste',
            'equipamento_nome': 'Equipamento de Teste',
            'descricao_problema': 'Teste automatico do CRUD',
            'valor_total': '100.00',
            'servicos_json': '[]',
            'produtos_json': '[]',
            'parcelas_json': '[]'
        }
        
        response = requests.post(f"{base_url}/ordens/nova", data=dados, timeout=5, allow_redirects=False)
        if response.status_code == 302:  # Redirect indica sucesso
            print("   ✓ Criacao de ordem funcionando")
            # Tentar extrair ID da ordem do redirect
            location = response.headers.get('Location', '')
            if 'ordens' in location:
                print(f"   ✓ Redirect para: {location}")
        else:
            print(f"   ✗ Criacao falhou - Status: {response.status_code}")
    except Exception as e:
        print(f"   ✗ Erro na criacao: {str(e)[:100]}")
    
    print("\n=== FIM DOS TESTES ===")

if __name__ == "__main__":
    teste_basico()