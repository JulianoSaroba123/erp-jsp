#!/usr/bin/env python3
"""
Teste completo do CRUD de Ordem de Servico
"""

import requests
import json
from datetime import datetime

BASE_URL = "http://127.0.0.1:5000"

def teste_listar_ordens():
    """Testa listagem de ordens (READ)"""
    try:
        print("Testando listagem de ordens...")
        response = requests.get(f"{BASE_URL}/ordens/")
        
        if response.status_code == 200:
            print("OK - Listagem funcionando")
            return True
        else:
            print(f"ERRO - Listagem: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"ERRO - Listagem: {e}")
        return False

def teste_criar_ordem():
    """Testa criacao de ordem (CREATE)"""
    try:
        print("Testando criacao de ordem...")
        
        dados = {
            'cliente_id': '7',  # SAROBA
            'solicitante': 'Joao Silva Teste CRUD',
            'contato': '(11) 99999-1234',
            'data_emissao': datetime.now().strftime('%Y-%m-%d'),
            'previsao_conclusao': '2025-12-31',
            'prioridade': 'Alta',
            'status': 'Aberta',
            'tipo_servico': 'Manutencao',
            'equipamento_nome': 'Ar Condicionado Split',
            'equipamento_marca': 'Samsung',
            'equipamento_modelo': 'Digital Inverter',
            'equipamento_numero_serie': 'TEST123456',
            'equipamento_acessorios': 'Controle remoto, Manual',
            'descricao_problema': 'Equipamento nao esta resfriando adequadamente',
            'descricao_servico_realizado': 'A ser realizado apos diagnostico',
            'tecnico_responsavel': 'Tecnico CRUD Test',
            'hora_inicio': '08:00',
            'hora_termino': '12:00',
            'total_horas': '4.0',
            'valor_mao_obra': '200.00',
            'valor_servicos': '150.00',
            'valor_produtos': '100.00',
            'valor_total': '450.00',
            'forma_pagamento': 'PIX',
            'condicoes_pagamento': 'A vista',
            'observacoes_internas': 'Teste de CRUD - Ordem criada automaticamente',
            'servicos_json': '[]',
            'produtos_json': '[]',
            'parcelas_json': '[]'
        }
        
        response = requests.post(f"{BASE_URL}/ordens/nova", data=dados, allow_redirects=False)
        
        if response.status_code == 302:  # Redirect apos sucesso
            print("OK - Criacao funcionando")
            location = response.headers.get('Location', '')
            # Extrair ID da ordem do redirect
            if '/ordens/' in location:
                ordem_id = location.split('/ordens/')[-1]
                print(f"Nova ordem criada com ID: {ordem_id}")
                return ordem_id
            return True
        else:
            print(f"ERRO - Criacao: {response.status_code}")
            print(response.text[:500])
            return False
            
    except Exception as e:
        print(f"ERRO - Criacao: {e}")
        return False

def teste_visualizar_ordem(ordem_id):
    """Testa visualizacao de ordem especifica (READ)"""
    try:
        print(f"Testando visualizacao da ordem {ordem_id}...")
        response = requests.get(f"{BASE_URL}/ordens/{ordem_id}")
        
        if response.status_code == 200:
            print("OK - Visualizacao funcionando")
            return True
        else:
            print(f"ERRO - Visualizacao: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"ERRO - Visualizacao: {e}")
        return False

def teste_editar_ordem(ordem_id):
    """Testa edicao de ordem (UPDATE)"""
    try:
        print(f"Testando edicao da ordem {ordem_id}...")
        
        dados = {
            'cliente_id': '7',  # SAROBA
            'solicitante': 'Joao Silva ATUALIZADO',
            'contato': '(11) 99999-9999',
            'data_emissao': datetime.now().strftime('%Y-%m-%d'),
            'previsao_conclusao': '2025-12-31',
            'prioridade': 'Urgente',  # Mudou de Alta para Urgente
            'status': 'Em Andamento',  # Mudou de Aberta para Em Andamento
            'tipo_servico': 'Manutencao Corretiva',
            'equipamento_nome': 'Ar Condicionado Split ATUALIZADO',
            'equipamento_marca': 'Samsung',
            'equipamento_modelo': 'Digital Inverter Pro',  # Atualizado
            'equipamento_numero_serie': 'TEST123456',
            'equipamento_acessorios': 'Controle remoto, Manual, Filtro extra',
            'descricao_problema': 'Equipamento nao esta resfriando adequadamente - ATUALIZADO',
            'descricao_servico_realizado': 'Diagnostico realizado, necessaria troca do gas refrigerante',
            'tecnico_responsavel': 'Tecnico CRUD Test Senior',
            'hora_inicio': '08:30',
            'hora_termino': '16:30',
            'total_horas': '8.0',
            'valor_mao_obra': '350.00',  # Atualizado
            'valor_servicos': '250.00',
            'valor_produtos': '150.00',
            'valor_total': '750.00',  # Atualizado
            'forma_pagamento': 'Cartao de Credito',
            'condicoes_pagamento': '2x sem juros',
            'observacoes_internas': 'Teste de CRUD - Ordem ATUALIZADA automaticamente',
            'servicos_json': '[]',
            'produtos_json': '[]',
            'parcelas_json': '[]'
        }
        
        response = requests.post(f"{BASE_URL}/ordens/{ordem_id}/editar", data=dados, allow_redirects=False)
        
        if response.status_code == 302:  # Redirect apos sucesso
            print("OK - Edicao funcionando")
            return True
        else:
            print(f"ERRO - Edicao: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"ERRO - Edicao: {e}")
        return False

def teste_alterar_status(ordem_id):
    """Testa alteracao de status via API (UPDATE)"""
    try:
        print(f"Testando alteracao de status da ordem {ordem_id}...")
        
        response = requests.post(
            f"{BASE_URL}/ordens/{ordem_id}/status",
            json={'status': 'Concluida'},
            headers={'Content-Type': 'application/json'}
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print("OK - Alteracao de status funcionando")
                return True
            else:
                print(f"ERRO - Alteracao de status: {data.get('message')}")
                return False
        else:
            print(f"ERRO - Alteracao de status: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"ERRO - Alteracao de status: {e}")
        return False

def teste_remover_ordem(ordem_id):
    """Testa remocao de ordem (DELETE)"""
    try:
        print(f"Testando remocao da ordem {ordem_id}...")
        
        response = requests.post(f"{BASE_URL}/ordens/{ordem_id}/remover", allow_redirects=False)
        
        if response.status_code == 302:  # Redirect apos sucesso
            print("OK - Remocao funcionando")
            return True
        else:
            print(f"ERRO - Remocao: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"ERRO - Remocao: {e}")
        return False

def teste_api_ordens():
    """Testa API JSON de ordens"""
    try:
        print("Testando API JSON...")
        response = requests.get(f"{BASE_URL}/ordens/api/ordens")
        
        if response.status_code == 200:
            data = response.json()
            print(f"OK - API JSON funcionando ({len(data)} ordens)")
            return True
        else:
            print(f"ERRO - API: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"ERRO - API: {e}")
        return False

def main():
    print("TESTE COMPLETO DO CRUD DE ORDEM DE SERVICO")
    print("=" * 60)
    
    resultados = {}
    
    # Teste 1: Listar ordens
    resultados['listar'] = teste_listar_ordens()
    
    # Teste 2: Criar nova ordem
    ordem_id = teste_criar_ordem()
    resultados['criar'] = bool(ordem_id)
    
    if ordem_id and ordem_id != True:
        # Teste 3: Visualizar ordem criada
        resultados['visualizar'] = teste_visualizar_ordem(ordem_id)
        
        # Teste 4: Editar ordem
        resultados['editar'] = teste_editar_ordem(ordem_id)
        
        # Teste 5: Alterar status via API
        resultados['alterar_status'] = teste_alterar_status(ordem_id)
        
        # Teste 6: Remover ordem
        resultados['remover'] = teste_remover_ordem(ordem_id)
    else:
        print("AVISO: Nao foi possivel obter ID da ordem criada, pulando testes dependentes")
        resultados.update({
            'visualizar': False,
            'editar': False,
            'alterar_status': False,
            'remover': False
        })
    
    # Teste 7: API JSON
    resultados['api'] = teste_api_ordens()
    
    # Resumo
    print("\n" + "=" * 60)
    print("RESUMO DOS TESTES:")
    print("=" * 60)
    
    total_testes = len(resultados)
    testes_ok = sum(resultados.values())
    
    for teste, resultado in resultados.items():
        status = "PASSOU" if resultado else "FALHOU"
        print(f"{teste.upper():15} - {status}")
    
    print("-" * 60)
    print(f"TOTAL: {testes_ok}/{total_testes} testes passaram")
    
    if testes_ok == total_testes:
        print("TODOS OS TESTES PASSARAM! CRUD FUNCIONANDO PERFEITAMENTE!")
    else:
        print(f"{total_testes - testes_ok} teste(s) falharam. Verifique os logs acima.")
    
    return testes_ok == total_testes

if __name__ == "__main__":
    main()