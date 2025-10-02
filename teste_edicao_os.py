#!/usr/bin/env python3
"""
Teste simples de edicao de ordem de servico
"""

import requests
from datetime import datetime

def teste_edicao_os():
    """Teste de edicao da OS0351"""
    base_url = "http://127.0.0.1:5000"
    
    print("=== TESTE DE EDICAO DA OS0351 ===")
    
    # Primeiro, vamos pegar os dados atuais da OS
    try:
        print("1. Buscando OS0351...")
        response = requests.get(f"{base_url}/ordens/2", timeout=5)
        if response.status_code == 200:
            print("   ✓ OS encontrada")
        else:
            print(f"   ✗ Erro ao buscar OS: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ✗ Erro: {str(e)[:100]}")
        return False
    
    # Agora vamos fazer uma edicao
    try:
        print("\n2. Testando edicao...")
        dados = {
            'cliente_id': '7',  # MR JACKY
            'solicitante': f'Teste Edicao {datetime.now().strftime("%H:%M:%S")}',
            'contato': '(11) 99999-1234',
            'data_emissao': '2025-09-26',
            'previsao_conclusao': '2025-12-31',
            'prioridade': 'Alta',
            'status': 'Em Andamento',
            'tipo_servico': 'Manutencao Corretiva',
            'equipamento_nome': f'Equipamento Atualizado {datetime.now().strftime("%H:%M:%S")}',
            'equipamento_marca': 'Samsung',
            'equipamento_modelo': 'Digital Inverter Pro',
            'equipamento_numero_serie': 'TEST123456',
            'equipamento_acessorios': 'Controle remoto, Manual',
            'descricao_problema': f'Problema atualizado em {datetime.now().strftime("%H:%M:%S")}',
            'descricao_servico_realizado': f'Servico realizado em {datetime.now().strftime("%H:%M:%S")}',
            'tecnico_responsavel': 'Tecnico Teste',
            'hora_inicio': '08:00',
            'hora_termino': '17:00',
            'total_horas': '9.0',
            'valor_mao_obra': '450.00',
            'valor_servicos': '300.00',
            'valor_produtos': '150.00',
            'valor_total': '900.00',
            'forma_pagamento': 'PIX',
            'condicoes_pagamento': 'A vista',
            'observacoes_internas': f'Observacao atualizada em {datetime.now().strftime("%H:%M:%S")}',
            'servicos_json': '[]',
            'produtos_json': '[]',
            'parcelas_json': '[]'
        }
        
        response = requests.post(f"{base_url}/ordens/2/editar", data=dados, timeout=5, allow_redirects=False)
        
        if response.status_code == 302:  # Redirect indica sucesso
            print("   ✓ Edicao realizada com sucesso!")
            location = response.headers.get('Location', '')
            print(f"   ✓ Redirecionado para: {location}")
            return True
        else:
            print(f"   ✗ Erro na edicao: {response.status_code}")
            if response.text:
                print(f"   Resposta: {response.text[:200]}")
            return False
            
    except Exception as e:
        print(f"   ✗ Erro na edicao: {str(e)[:100]}")
        return False

if __name__ == "__main__":
    sucesso = teste_edicao_os()
    print(f"\n=== RESULTADO: {'SUCESSO' if sucesso else 'FALHA'} ===")