#!/usr/bin/env python3
"""
Teste Debug da edição de OS
"""

import requests
from datetime import datetime

def debug_edicao():
    url = "http://127.0.0.1:5000/ordens/2/editar"
    
    dados = {
        'cliente_id': '7',
        'solicitante': f'DEBUG TEST {datetime.now().strftime("%H:%M:%S")}',
        'contato': '(11) 99999-8888',
        'data_emissao': '2025-09-26',
        'prioridade': 'Alta',
        'status': 'Em Andamento',
        'tipo_servico': 'Debug Test',
        'equipamento_nome': f'Debug Equipment {datetime.now().strftime("%H:%M:%S")}',
        'descricao_problema': f'Debug Problem {datetime.now().strftime("%H:%M:%S")}',
        'valor_total': '999.99',
        'servicos_json': '[]',
        'produtos_json': '[]',
        'parcelas_json': '[]'
    }
    
    print(f"=== TESTE DEBUG EDIÇÃO OS ===")
    print(f"URL: {url}")
    print(f"Dados enviados: {list(dados.keys())}")
    
    try:
        response = requests.post(url, data=dados, timeout=10, allow_redirects=False)
        print(f"Status Code: {response.status_code}")
        print(f"Headers: {dict(response.headers)}")
        
        if response.status_code == 302:
            location = response.headers.get('Location', 'Não informado')
            print(f"✓ SUCESSO - Redirect para: {location}")
            return True
        else:
            print(f"✗ ERRO - Status: {response.status_code}")
            print(f"Resposta: {response.text[:300] if response.text else 'Vazio'}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"✗ ERRO de conexão: {e}")
        return False
    except Exception as e:
        print(f"✗ ERRO geral: {e}")
        return False

if __name__ == "__main__":
    debug_edicao()