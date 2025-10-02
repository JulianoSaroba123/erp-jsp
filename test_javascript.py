#!/usr/bin/env python3
"""
Script para testar se o JavaScript da página de ordem de serviço está funcionando.
"""

import requests
import time
from urllib.parse import urljoin

def test_javascript_loading():
    """Testa se a página está carregando e se não há erros óbvios."""
    
    base_url = "http://127.0.0.1:5000"
    session = requests.Session()
    
    try:
        # Fazer login primeiro
        print("🔐 Fazendo login...")
        login_data = {
            'username': 'julia',
            'senha': '1234'
        }
        
        login_response = session.post(
            urljoin(base_url, '/login'), 
            data=login_data,
            allow_redirects=True
        )
        
        if login_response.status_code == 200:
            print("✅ Login realizado com sucesso")
        else:
            print(f"❌ Erro no login: {login_response.status_code}")
            return False
        
        # Acessar página de cadastro de ordem de serviço
        print("📄 Acessando página de cadastro de ordem de serviço...")
        page_response = session.get(urljoin(base_url, '/ordens/nova'))
        
        if page_response.status_code == 200:
            print("✅ Página carregada com sucesso")
            
            # Verificar se elementos importantes estão presentes no HTML
            content = page_response.text
            
            checks = [
                ('jQuery carregado', 'jquery' in content.lower()),
                ('Função setupClienteSelection', 'setupClienteSelection' in content),
                ('Função calcularTotais', 'calcularTotais' in content),
                ('Campo cliente_select', 'id="cliente_select"' in content),
                ('Campo servico_select', 'id="servico_select"' in content),
                ('Campo produto_select', 'id="produto_select"' in content),
                ('DOMContentLoaded', 'DOMContentLoaded' in content),
            ]
            
            print("\n📊 Verificações de conteúdo:")
            for check_name, check_result in checks:
                status = "✅" if check_result else "❌"
                print(f"{status} {check_name}")
            
            # Verificar se há selects populados com dados
            if 'option value=' in content:
                print("✅ Há options nos selects (dados carregados)")
            else:
                print("❌ Selects parecem vazios")
                
            return True
            
        else:
            print(f"❌ Erro ao carregar página: {page_response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Erro durante teste: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Testando carregamento de JavaScript...")
    test_javascript_loading()