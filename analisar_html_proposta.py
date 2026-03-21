#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Analisa o HTML retornado para identificar problemas de renderização.
"""

import requests
from bs4 import BeautifulSoup
import re

def analisar_html_proposta():
    """Analisa detalhadamente o HTML da proposta."""
    
    url = "https://erp-jsp-th5o.onrender.com/propostas/19"
    
    print("=" * 100)
    print("🔬 ANÁLISE DETALHADA DO HTML DA PROPOSTA")
    print("=" * 100)
    
    try:
        print(f"\n📡 Requisitando: {url}")
        response = requests.get(url, timeout=30)
        
        print(f"✅ Status: {response.status_code}")
        print(f"📦 Tamanho: {len(response.content)} bytes")
        
        html = response.text
        soup = BeautifulSoup(html, 'html.parser')
        
        # 1. Verificar estrutura básica
        print("\n" + "="*100)
        print("1️⃣ ESTRUTURA HTML")
        print("="*100)
        
        print(f"   <!DOCTYPE>: {'✅' if '<!DOCTYPE' in html[:100].upper() else '❌'}")
        print(f"   <html>: {'✅' if soup.find('html') else '❌'}")
        print(f"   <head>: {'✅' if soup.find('head') else '❌'}")
        print(f"   <body>: {'✅' if soup.find('body') else '❌'}")
        
        # 2. Verificar título
        title = soup.find('title')
        print(f"\n📄 Título: {title.get_text() if title else 'NÃO ENCONTRADO'}")
        
        # 3. Verificar se tem conteúdo visível
        print("\n" + "="*100)
        print("2️⃣ CONTEÚDO DA PÁGINA")
        print("="*100)
        
        body = soup.find('body')
        if body:
            body_text = body.get_text(strip=True)
            print(f"   Tamanho do texto no body: {len(body_text)} caracteres")
            
            # Primeiros 500 caracteres
            print(f"\n   📝 Início do conteúdo:")
            print(f"   {body_text[:500]}")
            
            # Verificar conteúdo específico
            has_proposta_header = 'Proposta PROP' in body_text
            has_cliente = 'Cliente' in body_text
            has_valor = 'Valor Total' in body_text or 'R$' in body_text
            
            print(f"\n   ✅ Elementos esperados:")
            print(f"      {'✅' if has_proposta_header else '❌'} Header da proposta (PROP)")
            print(f"      {'✅' if has_cliente else '❌'} Informação do cliente")
            print(f"      {'✅' if has_valor else '❌'} Valores monetários")
        
        # 4. Verificar CSS carregado
        print("\n" + "="*100)
        print("3️⃣ ARQUIVOS CSS REFERENCIADOS")
        print("="*100)
        
        css_links = soup.find_all('link', rel='stylesheet')
        print(f"   Total de arquivos CSS: {len(css_links)}")
        
        for i, link in enumerate(css_links, 1):
            href = link.get('href', '')
            print(f"   {i}. {href}")
        
        # 5. Verificar JavaScript carregado
        print("\n" + "="*100)
        print("4️⃣ ARQUIVOS JAVASCRIPT REFERENCIADOS")
        print("="*100)
        
        scripts = soup.find_all('script', src=True)
        print(f"   Total de arquivos JS: {len(scripts)}")
        
        for i, script in enumerate(scripts, 1):
            src = script.get('src', '')
            print(f"   {i}. {src}")
        
        # 6. Verificar se tem elementos principais
        print("\n" + "="*100)
        print("5️⃣ ELEMENTOS PRINCIPAIS DA PROPOSTA")
        print("="*100)
        
        proposta_header = soup.find(class_='proposta-header')
        info_cards = soup.find_all(class_='info-card')
        value_highlight = soup.find(class_='value-highlight')
        
        print(f"   proposta-header: {'✅ ENCONTRADO' if proposta_header else '❌ NÃO ENCONTRADO'}")
        print(f"   info-card: {len(info_cards)} encontrados")
        print(f"   value-highlight: {'✅ ENCONTRADO' if value_highlight else '❌ NÃO ENCONTRADO'}")
        
        if proposta_header:
            print(f"\n   📋 Conteúdo do header:")
            print(f"   {proposta_header.get_text(strip=True)[:200]}")
        
        # 7. Verificar se tem estilos inline na página
        print("\n" + "="*100)
        print("6️⃣ ESTILOS E LAYOUT")
        print("="*100)
        
        style_tags = soup.find_all('style')
        print(f"   Tags <style> na página: {len(style_tags)}")
        
        # Verificar se o body tem classes
        if body:
            body_classes = body.get('class', [])
            print(f"   Classes no <body>: {body_classes if body_classes else 'Nenhuma'}")
        
        # 8. Verificar mensagens de erro/flash
        print("\n" + "="*100)
        print("7️⃣ MENSAGENS E ALERTAS")
        print("="*100)
        
        alerts = soup.find_all(class_=re.compile('alert'))
        if alerts:
            print(f"   ⚠️  {len(alerts)} alertas encontrados:")
            for alert in alerts:
                print(f"      - {alert.get_text(strip=True)[:100]}")
        else:
            print(f"   ✅ Nenhum alerta/erro")
        
        # 9. Verificar container principal
        print("\n" + "="*100)
        print("8️⃣ CONTAINER PRINCIPAL")
        print("="*100)
        
        container = soup.find(class_='container-fluid') or soup.find(class_='container')
        if container:
            print(f"   ✅ Container encontrado")
            container_text = container.get_text(strip=True)
            print(f"   📏 Tamanho do conteúdo: {len(container_text)} caracteres")
            
            if len(container_text) < 100:
                print(f"   ⚠️  AVISO: Container muito pequeno!")
                print(f"   Conteúdo: {container_text}")
        else:
            print(f"   ❌ Container NÃO encontrado")
        
        # 10. Verificar display:none ou visibility:hidden
        print("\n" + "="*100)
        print("9️⃣ ELEMENTOS OCULTOS")
        print("="*100)
        
        hidden_elements = soup.find_all(style=re.compile(r'display\s*:\s*none|visibility\s*:\s*hidden'))
        if hidden_elements:
            print(f"   ⚠️  {len(hidden_elements)} elementos com display:none ou visibility:hidden")
        else:
            print(f"   ✅ Nenhum elemento explicitamente oculto")
        
        # RESUMO FINAL
        print("\n" + "="*100)
        print("📊 DIAGNÓSTICO FINAL")
        print("="*100)
        
        problemas = []
        
        if not proposta_header:
            problemas.append("❌ Header da proposta não encontrado")
        
        if len(info_cards) == 0:
            problemas.append("❌ Cards de informação não encontrados")
        
        if not value_highlight:
            problemas.append("❌ Destaque de valor não encontrado")
        
        if body and len(body.get_text(strip=True)) < 1000:
            problemas.append("⚠️  Conteúdo do body muito pequeno")
        
        if len(css_links) < 3:
            problemas.append("⚠️  Poucos arquivos CSS carregados")
        
        if problemas:
            print("\n   🚨 PROBLEMAS IDENTIFICADOS:")
            for problema in problemas:
                print(f"      {problema}")
        else:
            print("\n   ✅ NENHUM PROBLEMA CRÍTICO DETECTADO!")
            print("\n   💡 Se a página ainda não aparece no navegador:")
            print("      1. Limpe completamente o cache (Ctrl+Shift+Delete)")
            print("      2. Teste em modo anônimo (Ctrl+Shift+N)")
            print("      3. Teste em outro navegador")
            print("      4. Verifique se há bloqueadores de anúncios ativos")
            print("      5. Verifique o console do navegador (F12)")
        
        print("\n" + "="*100)
        
    except Exception as e:
        print(f"\n❌ ERRO: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    analisar_html_proposta()
