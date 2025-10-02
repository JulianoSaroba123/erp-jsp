#!/usr/bin/env python3
"""
Teste específico para auto-complete em ordem de serviço
"""

import requests
from urllib.parse import urljoin
import re

def test_autocomplete():
    base_url = "http://127.0.0.1:5000"
    session = requests.Session()
    
    # Login
    print("🔐 Fazendo login...")
    login_data = {'username': 'julia', 'senha': '1234'}
    login_response = session.post(urljoin(base_url, '/login'), data=login_data, allow_redirects=True)
    
    if login_response.status_code != 200:
        print(f"❌ Erro no login: {login_response.status_code}")
        return
    
    # Acessar página
    print("📄 Acessando página de ordem de serviço...")
    page_response = session.get(urljoin(base_url, '/ordens/nova'))
    
    if page_response.status_code != 200:
        print(f"❌ Erro ao carregar página: {page_response.status_code}")
        return
    
    content = page_response.text
    
    print("\n🔍 ANALISANDO AUTO-COMPLETE...")
    
    # Verificar se há clientes no select
    cliente_options = re.findall(r'<option[^>]*value="(\d+)"[^>]*data-nome="([^"]*)"', content)
    print(f"👤 Clientes encontrados: {len(cliente_options)}")
    if cliente_options:
        print(f"   Primeiro: ID {cliente_options[0][0]}, Nome: {cliente_options[0][1]}")
    else:
        print("   ❌ Nenhum cliente encontrado no select!")
    
    # Verificar se há serviços no select
    servico_pattern = r'<select[^>]*id="servico_select"[^>]*>(.*?)</select>'
    servico_match = re.search(servico_pattern, content, re.DOTALL)
    if servico_match:
        servico_options = re.findall(r'<option[^>]*value="(\d+)"', servico_match.group(1))
        print(f"🔧 Serviços encontrados: {len(servico_options)}")
    else:
        print("❌ Select de serviços não encontrado!")
    
    # Verificar se há produtos no select
    produto_pattern = r'<select[^>]*id="produto_select"[^>]*>(.*?)</select>'
    produto_match = re.search(produto_pattern, content, re.DOTALL)
    if produto_match:
        produto_options = re.findall(r'<option[^>]*value="(\d+)"', produto_match.group(1))
        print(f"📦 Produtos encontrados: {len(produto_options)}")
    else:
        print("❌ Select de produtos não encontrado!")
    
    # Verificar se há datalists
    datalists = re.findall(r'<datalist[^>]*id="([^"]*)"', content)
    print(f"📋 Datalists encontrados: {datalists}")
    
    # Verificar se funções JavaScript estão presentes
    js_functions = [
        'setupClienteSelection', 'setupServicoSelection', 'setupProdutoSelection'
    ]
    
    print(f"\n🧩 FUNÇÕES JAVASCRIPT:")
    for func in js_functions:
        if func in content:
            print(f"   ✅ {func}")
        else:
            print(f"   ❌ {func} - NÃO ENCONTRADA!")
    
    # Verificar se event listeners estão sendo configurados
    if 'addEventListener' in content and 'DOMContentLoaded' in content:
        print("✅ Event listeners configurados corretamente")
    else:
        print("❌ Problema na configuração dos event listeners")
    
    print(f"\n📊 RESUMO:")
    print(f"   • Clientes: {len(cliente_options) if cliente_options else 0}")
    print(f"   • Serviços: {len(servico_options) if 'servico_options' in locals() else 0}")
    print(f"   • Produtos: {len(produto_options) if 'produto_options' in locals() else 0}")

if __name__ == "__main__":
    test_autocomplete()