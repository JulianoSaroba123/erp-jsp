#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Teste específico para simular POST do formulário de Ordem de Serviço
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import requests
import json
from datetime import datetime

def test_form_post():
    """Simula exatamente o que acontece quando o usuário submete o formulário"""
    
    print("=== TESTE POST FORMULÁRIO ORDEM DE SERVIÇO ===")
    
    # URL do endpoint
    url = "http://127.0.0.1:5000/ordens/nova"
    
    # Dados simulando preenchimento do formulário
    form_data = {
        'cliente_id': '7',  # ID de cliente existente
        'solicitante': 'João da Silva',
        'contato': '(11) 99999-9999',
        'data_emissao': datetime.now().strftime('%Y-%m-%d'),
        'previsao_conclusao': datetime.now().strftime('%Y-%m-%d'),
        'prioridade': 'Normal',
        'status': 'Aberta',
        'equipamento_nome': 'Computador Desktop',
        'equipamento_marca': 'Dell',
        'equipamento_modelo': 'OptiPlex 3070',
        'equipamento_numero_serie': 'DL123456789',
        'equipamento_acessorios': 'Mouse, teclado, monitor',
        'problema_descrito': 'Computador não liga',
        'descricao_servico_realizado': '',
        'tecnico_responsavel': 'Técnico Teste',
        'hora_inicio': '08:00',
        'hora_termino': '10:00',
        'km_inicial': '100.0',
        'km_final': '120.0',
        'outras_informacoes': 'Teste de criação via formulário',
        'servicos_json': '[]',
        'produtos_json': '[]',
        'parcelas_json': '[]',
        'valor_servicos': '0',
        'valor_produtos': '0',
        'valor_descontos': '0',
        'valor_total': '150.00'
    }
    
    print(f"\n1. Enviando POST para: {url}")
    print(f"   Dados: {len(form_data)} campos preenchidos")
    print(f"   Cliente ID: {form_data['cliente_id']}")
    print(f"   Solicitante: {form_data['solicitante']}")
    
    try:
        # Fazer requisição POST
        response = requests.post(url, data=form_data, allow_redirects=False)
        
        print(f"\n2. Resposta recebida:")
        print(f"   Status Code: {response.status_code}")
        print(f"   Headers: {dict(response.headers)}")
        
        if response.status_code == 302:
            # Redirecionamento esperado após sucesso
            location = response.headers.get('Location', 'N/A')
            print(f"   Redirecionamento para: {location}")
            
            if '/ordens/' in location:
                print("   ✓ SUCESSO: OS criada com sucesso!")
                return True
            else:
                print("   ⚠ AVISO: Redirecionamento inesperado")
                
        elif response.status_code == 200:
            # Formulário retornado (possível erro)
            print("   ⚠ AVISO: Formulário retornado - possível erro de validação")
            print(f"   Conteúdo: {response.text[:500]}...")
            
        else:
            print(f"   ❌ ERRO: Status inesperado {response.status_code}")
            print(f"   Conteúdo: {response.text[:500]}...")
            
        return False
        
    except Exception as e:
        print(f"\n   ❌ ERRO na requisição: {str(e)}")
        return False

def test_list_orders():
    """Testa a listagem para ver se a OS foi criada"""
    
    print("\n3. Verificando listagem de ordens...")
    
    try:
        url = "http://127.0.0.1:5000/ordens/"
        response = requests.get(url)
        
        if response.status_code == 200:
            # Verificar se contém ordens
            content = response.text
            if 'OS0' in content:
                print("   ✓ Listagem carregada com ordens de serviço")
                
                # Contar quantas OS aparecem
                import re
                os_codes = re.findall(r'OS\d{4}', content)
                print(f"   Total de OS encontradas: {len(set(os_codes))}")
                
                for code in set(os_codes):
                    print(f"   - {code}")
                
                return True
            else:
                print("   ⚠ Listagem carregada mas sem ordens visíveis")
                return False
        else:
            print(f"   ❌ ERRO: Status {response.status_code}")
            return False
            
    except Exception as e:
        print(f"   ❌ ERRO: {str(e)}")
        return False

if __name__ == "__main__":
    print("Aguardando servidor Flask...")
    
    # Verificar se servidor está ativo
    try:
        response = requests.get("http://127.0.0.1:5000/ordens/", timeout=5)
        print("✓ Servidor Flask ativo")
    except:
        print("❌ Servidor Flask não está ativo")
        sys.exit(1)
    
    # Executar testes
    post_success = test_form_post()
    list_success = test_list_orders()
    
    if post_success and list_success:
        print("\n=== TODOS OS TESTES PASSARAM ===")
        sys.exit(0)
    else:
        print("\n=== FALHAS DETECTADAS ===")
        sys.exit(1)