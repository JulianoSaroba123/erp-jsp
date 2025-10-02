#!/usr/bin/env python3
"""
Diagnóstico específico para problema de criação de nova OS
"""

import requests
import json
import time
from urllib.parse import urljoin

BASE_URL = "http://127.0.0.1:5000"

def teste_formulario_nova_os():
    """Testar se o formulário de nova OS está funcionando"""
    print("=== DIAGNÓSTICO: NOVA OS ===\n")
    
    try:
        # 1. Testar página de nova OS (GET)
        url_nova = urljoin(BASE_URL, "/ordens/nova")
        print(f"1. Testando GET {url_nova}")
        
        response = requests.get(url_nova, timeout=10)
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            content = response.text
            
            # Verificar elementos essenciais
            checks = {
                "Formulário presente": 'id="form-os"' in content,
                "Campo cliente_id": 'name="cliente_id"' in content,
                "Botão submit": 'type="submit"' in content,
                "JavaScript setupClienteSelection": 'setupClienteSelection()' in content,
                "Função validarClienteSelecionado": 'validarClienteSelecionado' in content,
                "Lista de clientes": 'cliente_select' in content
            }
            
            for check, resultado in checks.items():
                status = "✓" if resultado else "❌"
                print(f"   {status} {check}")
            
            if all(checks.values()):
                print("   ✅ Formulário parece estar OK\n")
            else:
                print("   ❌ Problemas encontrados no formulário\n")
                return False
                
        else:
            print(f"   ❌ Erro ao carregar formulário: {response.status_code}\n")
            return False
            
        # 2. Testar dados de clientes disponíveis
        print("2. Verificando clientes disponíveis...")
        clientes_count = content.count('<option value="') - 1  # -1 para remover "Selecione..."
        print(f"   Clientes encontrados: {clientes_count}")
        
        if clientes_count == 0:
            print("   ❌ NENHUM CLIENTE DISPONÍVEL! Este pode ser o problema.")
            return False
        else:
            print(f"   ✅ {clientes_count} clientes disponíveis\n")
            
        # 3. Simular envio do formulário com dados mínimos
        print("3. Testando envio de formulário...")
        
        # Extrair primeiro cliente disponível
        import re
        cliente_match = re.search(r'<option value="(\d+)"[^>]*>([^<]+)</option>', content)
        if not cliente_match:
            print("   ❌ Não foi possível extrair ID de cliente para teste")
            return False
            
        cliente_id = cliente_match.group(1)
        cliente_nome = cliente_match.group(2).strip()
        print(f"   Usando cliente de teste: {cliente_nome} (ID: {cliente_id})")
        
        # Dados mínimos para criar uma OS
        form_data = {
            'cliente_id': cliente_id,
            'solicitante': 'Teste Diagnóstico',
            'status': 'Aberta',
            'prioridade': 'Media',
            'valor_total': '100.00',
            'servicos_json': '[]',
            'produtos_json': '[]',
            'parcelas_json': '[]'
        }
        
        # Enviar POST
        url_criar = urljoin(BASE_URL, "/ordens/nova")
        print(f"   Enviando POST para {url_criar}")
        
        response = requests.post(url_criar, data=form_data, timeout=10, allow_redirects=False)
        print(f"   Status da resposta: {response.status_code}")
        
        if response.status_code == 302:
            # Redirecionamento significa sucesso
            location = response.headers.get('Location', '')
            print(f"   ✅ Redirecionamento para: {location}")
            print("   ✅ OS criada com sucesso!\n")
            return True
            
        elif response.status_code == 200:
            # Página recarregou - pode ser erro de validação
            response_text = response.text
            if 'alert' in response_text.lower() or 'erro' in response_text.lower():
                print("   ❌ Possível erro de validação na página")
                # Procurar por mensagens de erro
                if 'Por favor, selecione um cliente' in response_text:
                    print("   ❌ Erro: Cliente não selecionado (problema no JavaScript)")
                elif 'Erro' in response_text:
                    print("   ❌ Erro encontrado na resposta")
                return False
            else:
                print("   ⚠️  Formulário recarregou sem redirecionamento")
                return False
                
        else:
            print(f"   ❌ Erro inesperado: {response.status_code}")
            print(f"   Resposta: {response.text[:200]}...")
            return False
            
    except Exception as e:
        print(f"ERRO no teste: {e}")
        return False

def main():
    # Aguardar servidor
    time.sleep(2)
    
    resultado = teste_formulario_nova_os()
    
    print("=== CONCLUSÃO ===")
    if resultado:
        print("✅ Sistema de criação de OS está funcionando!")
        print("   - O problema pode ser no navegador (cache, JavaScript desabilitado)")
        print("   - Tente fazer HARD REFRESH (Ctrl+F5)")
        print("   - Verifique console do navegador para erros JavaScript")
    else:
        print("❌ Problema encontrado no sistema de criação de OS")
        print("   - Verifique os detalhes acima")
        print("   - Pode ser problema no JavaScript do formulário")
        print("   - Ou problema na validação/processamento dos dados")

if __name__ == "__main__":
    main()