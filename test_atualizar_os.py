#!/usr/bin/env python3
"""
Script para testar a atualização de ordem de serviço
"""

import requests
from datetime import datetime

# URL base do servidor Flask
BASE_URL = "http://127.0.0.1:5000"

def teste_atualizar_ordem_servico(ordem_id=1):
    """Testa a atualização de uma ordem de serviço"""
    
    # Primeiro, vamos buscar a ordem existente
    try:
        print(f"🔍 Buscando ordem de serviço #{ordem_id}...")
        response = requests.get(f"{BASE_URL}/ordens/{ordem_id}/editar")
        
        if response.status_code == 200:
            print("✅ Ordem encontrada para edição")
        else:
            print(f"❌ Erro ao buscar ordem: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Erro ao buscar ordem: {str(e)}")
        return False
    
    # Dados para atualizar a OS
    dados_atualizacao = {
        'cliente_id': '7',  # ID do cliente SAROBA
        'cliente_input': 'SAROBA INSTALACAO E MANUTENCAO LTDA',
        'solicitante': 'João Silva Atualizado',
        'contato': '(11) 99999-9999',
        'data_emissao': datetime.now().strftime('%Y-%m-%d'),
        'previsao_conclusao': '2025-02-28',
        'prioridade': 'Urgente',
        'status': 'Em Andamento',
        'equipamento': 'Ar Condicionado Split ATUALIZADO',
        'marca': 'LG',
        'modelo': 'DUAL INVERTER',
        'numero_serie': 'LG123456789',
        'acessorios': 'Controle remoto, Manual',
        'problema_equipamento': 'Não resfria adequadamente',
        'defeito_relatado': 'Cliente relata que não está gelando - ATUALIZADO',
        'descricao_problema': 'Equipamento apresenta problemas de refrigeração',
        'servico_realizado': 'Limpeza do evaporador e recarga de gás',
        'solucao': 'Problema resolvido após manutenção completa',
        'tecnico_responsavel': 'Técnico Senior Atualizado',
        'hora_inicio': '08:30',
        'hora_termino': '12:30',
        'total_horas': '4.0',
        'valor_mao_obra': '250.00',
        'valor_servicos': '350.00',
        'valor_produtos': '100.00',
        'valor_total': '700.00',
        'forma_pagamento': 'Cartão de Crédito',
        'condicoes_pagamento': '2x sem juros',
        'observacoes_internas': 'OS atualizada via teste automático - ' + datetime.now().strftime('%Y-%m-%d %H:%M'),
        'outras_informacoes': 'Teste de atualização realizado com sucesso',
        'servicos_json': '[]',
        'produtos_json': '[]',
        'parcelas_json': '[]'
    }
    
    try:
        print("🔄 Enviando dados de atualização...")
        print(f"📋 Alguns dados: {{'solicitante': '{dados_atualizacao['solicitante']}', 'prioridade': '{dados_atualizacao['prioridade']}', 'status': '{dados_atualizacao['status']}'}}")
        
        # Fazer POST request para atualizar
        response = requests.post(
            f"{BASE_URL}/ordens/{ordem_id}/editar",
            data=dados_atualizacao,
            allow_redirects=False
        )
        
        print(f"📡 Status Code: {response.status_code}")
        print(f"📡 Headers: {dict(response.headers)}")
        
        if response.status_code == 302:  # Redirect após sucesso
            print("✅ OS atualizada com sucesso! (Redirect detectado)")
            location = response.headers.get('Location', '')
            print(f"🔗 Redirecionando para: {location}")
            return True
        elif response.status_code == 200:
            print("📄 Resposta (200):")
            # Verificar se há mensagem de erro na resposta
            if "Erro" in response.text or "erro" in response.text:
                print("❌ Erro detectado na resposta")
                # Mostrar parte relevante da resposta
                lines = response.text.split('\n')
                for i, line in enumerate(lines):
                    if 'erro' in line.lower() or 'error' in line.lower():
                        print(f"Linha {i}: {line.strip()}")
                return False
            else:
                print("✅ OS pode ter sido atualizada (verificar manualmente)")
                return True
        else:
            print(f"❌ Erro HTTP {response.status_code}")
            print(response.text[:1000] + "..." if len(response.text) > 1000 else response.text)
            return False
            
    except Exception as e:
        print(f"❌ Erro na requisição de atualização: {str(e)}")
        return False

def verificar_ordem_atualizada(ordem_id=1):
    """Verifica se a ordem foi realmente atualizada"""
    try:
        print(f"\n🔍 Verificando se ordem #{ordem_id} foi atualizada...")
        response = requests.get(f"{BASE_URL}/ordens/{ordem_id}/editar")
        
        if response.status_code == 200:
            # Verificar se os dados atualizados estão presentes
            if "João Silva Atualizado" in response.text:
                print("✅ Solicitante foi atualizado corretamente")
            else:
                print("❌ Solicitante não foi atualizado")
                
            if "Urgente" in response.text:
                print("✅ Prioridade foi atualizada corretamente")
            else:
                print("❌ Prioridade não foi atualizada")
                
            if "Em Andamento" in response.text:
                print("✅ Status foi atualizado corretamente")
            else:
                print("❌ Status não foi atualizado")
                
            if "LG" in response.text:
                print("✅ Marca foi atualizada corretamente")
            else:
                print("❌ Marca não foi atualizada")
                
        else:
            print(f"❌ Erro ao verificar ordem: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Erro ao verificar ordem: {str(e)}")

if __name__ == "__main__":
    print("🧪 TESTE DE ATUALIZAÇÃO DE ORDEM DE SERVIÇO")
    print("=" * 55)
    
    # Tentar atualizar a ordem ID 1
    sucesso = teste_atualizar_ordem_servico(1)
    
    # Verificar se a atualização funcionou
    if sucesso:
        verificar_ordem_atualizada(1)
    
    print("\n" + "=" * 55)
    if sucesso:
        print("✅ TESTE DE ATUALIZAÇÃO CONCLUÍDO COM SUCESSO!")
    else:
        print("❌ TESTE DE ATUALIZAÇÃO FALHOU!")