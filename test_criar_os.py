#!/usr/bin/env python3
"""
Script para testar a criação de ordem de serviço
"""

import requests
from datetime import datetime

# URL base do servidor Flask
BASE_URL = "http://127.0.0.1:5000"

def teste_criar_ordem_servico():
    """Testa a criação de uma ordem de serviço"""
    
    # Dados para criar uma OS de teste
    dados_os = {
        'cliente_id': '7',  # ID do cliente SAROBA
        'cliente_input': 'SAROBA INSTALACAO E MANUTENCAO LTDA',
        'solicitante': 'João Silva',
        'contato': '(11) 99999-1111',
        'data_emissao': datetime.now().strftime('%Y-%m-%d'),
        'previsao_conclusao': '2025-01-31',
        'prioridade': 'Alta',
        'status': 'Aberta',
        'equipamento': 'Ar Condicionado',
        'marca': 'Samsung',
        'modelo': 'AR24',
        'numero_serie': '123456789',
        'defeito_relatado': 'Não está gelando',
        'tecnico_responsavel': 'Técnico Teste',
        'valor_mao_obra': '150.00',
        'valor_servicos': '200.00',
        'valor_produtos': '50.00',
        'valor_total': '400.00',
        'forma_pagamento': 'PIX',
        'observacoes_internas': 'OS criada via teste automático',
        'servicos_json': '[]',
        'produtos_json': '[]',
        'parcelas_json': '[]'
    }
    
    try:
        print("🚀 Enviando dados para criação de OS...")
        print(f"📋 Dados: {dados_os}")
        
        # Fazer POST request
        response = requests.post(
            f"{BASE_URL}/ordens/nova",
            data=dados_os,
            allow_redirects=False
        )
        
        print(f"📡 Status Code: {response.status_code}")
        print(f"📡 Headers: {dict(response.headers)}")
        
        if response.status_code == 302:  # Redirect após sucesso
            print("✅ OS criada com sucesso! (Redirect detectado)")
            location = response.headers.get('Location', '')
            print(f"🔗 Redirecionando para: {location}")
            return True
        elif response.status_code == 200:
            print("📄 Resposta (200):")
            print(response.text[:500] + "..." if len(response.text) > 500 else response.text)
            
            # Verificar se há mensagem de erro na resposta
            if "Erro" in response.text or "erro" in response.text:
                print("❌ Erro detectado na resposta")
                return False
            else:
                print("✅ OS pode ter sido criada (verificar manualmente)")
                return True
        else:
            print(f"❌ Erro HTTP {response.status_code}")
            print(response.text[:500] + "..." if len(response.text) > 500 else response.text)
            return False
            
    except Exception as e:
        print(f"❌ Erro na requisição: {str(e)}")
        return False

def verificar_ordens_existentes():
    """Verifica as ordens de serviço existentes"""
    try:
        print("\n📋 Verificando ordens existentes...")
        response = requests.get(f"{BASE_URL}/ordens/")
        
        if response.status_code == 200:
            print("✅ Lista de ordens carregada")
            # Verificar se há alguma ordem listada
            if "OS" in response.text or "Ordem" in response.text:
                print("📝 Ordens encontradas na listagem")
            else:
                print("📭 Nenhuma ordem encontrada")
        else:
            print(f"❌ Erro ao carregar lista: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Erro ao verificar ordens: {str(e)}")

if __name__ == "__main__":
    print("🧪 TESTE DE CRIAÇÃO DE ORDEM DE SERVIÇO")
    print("=" * 50)
    
    # Verificar ordens antes do teste
    verificar_ordens_existentes()
    
    # Tentar criar uma nova OS
    print("\n" + "=" * 50)
    sucesso = teste_criar_ordem_servico()
    
    # Verificar ordens após o teste
    print("\n" + "=" * 50)
    verificar_ordens_existentes()
    
    print("\n" + "=" * 50)
    if sucesso:
        print("✅ TESTE CONCLUÍDO COM SUCESSO!")
    else:
        print("❌ TESTE FALHOU!")