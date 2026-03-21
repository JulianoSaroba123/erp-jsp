#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Testa a URL do Render diretamente para ver o que está retornando.
"""

import requests
from bs4 import BeautifulSoup

def testar_url_render():
    """Testa a URL da proposta no Render."""
    url = "https://erp-jsp-th5o.onrender.com/propostas/19"
    
    print("=" * 80)
    print("🌐 TESTE DE URL DO RENDER")
    print("=" * 80)
    print(f"\n📍 URL: {url}")
    
    try:
        print("\n🔄 Fazendo requisição...")
        response = requests.get(url, timeout=30)
        
        print(f"\n📊 RESPOSTA:")
        print(f"   Status Code: {response.status_code}")
        print(f"   Content-Type: {response.headers.get('Content-Type', 'N/A')}")
        print(f"   Tamanho: {len(response.content)} bytes")
        
        if response.status_code == 200:
            print(f"\n✅ REQUISIÇÃO BEM-SUCEDIDA!")
            
            # Analisar HTML
            html = response.text
            soup = BeautifulSoup(html, 'html.parser')
            
            # Verificar estrutura básica
            has_doctype = html.strip().lower().startswith('<!doctype')
            has_html = soup.find('html') is not None
            has_head = soup.find('head') is not None
            has_body = soup.find('body') is not None
            has_content = len(html) > 1000
            
            print(f"\n🔍 ANÁLISE DO HTML:")
            print(f"   {'✅' if has_doctype else '❌'} DOCTYPE presente")
            print(f"   {'✅' if has_html else '❌'} Tag <html>")
            print(f"   {'✅' if has_head else '❌'} Tag <head>")
            print(f"   {'✅' if has_body else '❌'} Tag <body>")
            print(f"   {'✅' if has_content else '❌'} Conteúdo suficiente (>1KB)")
            
            # Verificar se tem erro Jinja2 não renderizado
            has_jinja_error = '{{ proposta' in html or '{% ' in html
            if has_jinja_error:
                print(f"\n❌ ERRO: Template Jinja2 não foi renderizado!")
                print(f"   Encontradas variáveis não processadas no HTML")
            
            # Verificar título
            title = soup.find('title')
            if title:
                print(f"\n📄 Título da página: {title.get_text()}")
            
            # Verificar erros no console (tags script com erro)
            scripts = soup.find_all('script')
            print(f"\n📜 Scripts encontrados: {len(scripts)}")
            
            # Verificar links CSS
            css_links = soup.find_all('link', rel='stylesheet')
            print(f"🎨 Links CSS encontrados: {len(css_links)}")
            
            # Verificar se tem conteúdo da proposta
            proposta_header = soup.find(class_='proposta-header')
            if proposta_header:
                print(f"\n✅ Header da proposta encontrado!")
            else:
                print(f"\n❌ Header da proposta NÃO encontrado!")
                
                # Verificar se tem mensagem de erro/flash
                flashes = soup.find_all(class_='alert')
                if flashes:
                    print(f"\n⚠️  Mensagens de alerta encontradas:")
                    for flash in flashes:
                        print(f"   - {flash.get_text().strip()[:100]}")
            
            # Mostrar primeiras linhas do body
            body = soup.find('body')
            if body:
                body_text = body.get_text(strip=True)[:500]
                print(f"\n📝 Primeiras palavras do body:")
                print(f"   {body_text}")
            
        elif response.status_code == 404:
            print(f"\n❌ ERRO 404: Proposta não encontrada ou rota não existe")
            print(f"\n💡 Possíveis causas:")
            print(f"   1. Proposta ID 19 não existe no banco")
            print(f"   2. Proposta está marcada como inativa (ativo=False)")
            print(f"   3. Rota não foi registrada corretamente")
            
        elif response.status_code == 302:
            print(f"\n⚠️  REDIRECT (302): Sendo redirecionado")
            location = response.headers.get('Location', 'N/A')
            print(f"   Destino: {location}")
            
        elif response.status_code == 500:
            print(f"\n❌ ERRO 500: Erro interno do servidor")
            print(f"\n📄 Conteúdo da resposta:")
            print(response.text[:1000])
            
        else:
            print(f"\n⚠️  Status inesperado: {response.status_code}")
            
    except requests.exceptions.Timeout:
        print(f"\n❌ TIMEOUT: Servidor demorou muito para responder")
    except requests.exceptions.ConnectionError:
        print(f"\n❌ ERRO DE CONEXÃO: Não foi possível conectar ao servidor")
    except Exception as e:
        print(f"\n❌ ERRO: {e}")

if __name__ == '__main__':
    # Verificar se beautifulsoup4 está instalado
    try:
        import bs4
    except ImportError:
        print("❌ BeautifulSoup4 não está instalado!")
        print("   Execute: pip install beautifulsoup4")
        exit(1)
    
    testar_url_render()
