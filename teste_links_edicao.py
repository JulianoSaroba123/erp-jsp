#!/usr/bin/env python3
"""
Script para testar especificamente os links de edição
"""
import requests

def testar_links_edicao():
    print("=== TESTE ESPECÍFICO DOS LINKS DE EDIÇÃO ===\n")
    
    base_url = "http://127.0.0.1:5000"
    
    # 1. Acessar a página da lista
    print("1. Acessando página da lista...")
    try:
        response = requests.get(f"{base_url}/ordens", timeout=10)
        if response.status_code == 200:
            print("   ✓ Lista carregada com sucesso")
            
            # Extrair URLs de edição do HTML
            import re
            edit_links = re.findall(r'href="([^"]*editar[^"]*)"', response.text)
            print(f"   ✓ {len(edit_links)} links de edição encontrados")
            
            for i, link in enumerate(edit_links[:3], 1):  # Testar apenas os 3 primeiros
                print(f"\n2.{i} Testando link de edição: {link}")
                
                # Testar se o link funciona diretamente
                try:
                    full_url = f"{base_url}{link}" if link.startswith('/') else link
                    edit_response = requests.get(full_url, timeout=10)
                    print(f"     Status: {edit_response.status_code}")
                    
                    if edit_response.status_code == 200:
                        content = edit_response.text
                        if "form" in content.lower():
                            print("     ✓ Formulário de edição encontrado")
                        if "input" in content.lower():
                            print("     ✓ Campos de entrada encontrados")
                        if "cadastro" in content.lower():
                            print("     ✓ Template de cadastro carregado")
                    else:
                        print(f"     ❌ Erro: {edit_response.status_code}")
                        print(f"     Resposta: {edit_response.text[:200]}")
                        
                except Exception as e:
                    print(f"     ❌ Erro ao testar link: {e}")
        else:
            print(f"   ❌ Erro ao carregar lista: {response.status_code}")
            
    except Exception as e:
        print(f"   ❌ Erro: {e}")
    
    print("\n=== VERIFICAÇÕES ADICIONAIS ===")
    
    # Verificar se existe algum redirecionamento
    print("\n3. Testando redirecionamentos...")
    test_urls = [
        "/ordens/2/editar",
        "/ordens/3/editar", 
        "/ordens/8/editar"
    ]
    
    for url in test_urls:
        try:
            full_url = f"{base_url}{url}"
            response = requests.get(full_url, timeout=10, allow_redirects=False)
            
            if response.status_code == 302 or response.status_code == 301:
                redirect_url = response.headers.get('Location', 'N/A')
                print(f"   ⚠️ {url} -> Redirect para: {redirect_url}")
            elif response.status_code == 200:
                print(f"   ✓ {url} -> OK (200)")
            else:
                print(f"   ❌ {url} -> Erro {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ {url} -> Erro: {e}")
    
    print("\n=== DIAGNÓSTICO DO PROBLEMA ===")
    print("Se os links funcionam aqui mas não no navegador, pode ser:")
    print("1. 🔍 JavaScript interceptando cliques globalmente")
    print("2. 🔍 CSS pointer-events: none nos links")
    print("3. 🔍 Overlay invisível cobrindo os botões")
    print("4. 🔍 Event.preventDefault() sendo chamado")
    print("5. 🔍 Bootstrap/jQuery interferindo")
    
    print("\n💡 TESTE MANUAL:")
    print("1. Abra F12 -> Console")
    print("2. Digite: document.querySelectorAll('a[href*=\"editar\"]')")
    print("3. Verifique se os links estão visíveis e clicáveis")
    print("4. Teste: document.querySelector('a[href*=\"editar\"]').click()")

if __name__ == "__main__":
    testar_links_edicao()