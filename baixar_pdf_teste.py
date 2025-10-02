#!/usr/bin/env python3
import requests
import datetime

# Baixar PDF da API
url = "http://127.0.0.1:5000/ordens/2/pdf"

try:
    print(f"📥 Baixando PDF de: {url}")
    response = requests.get(url)
    
    if response.status_code == 200:
        # Salvar PDF
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"pdf_baixado_{timestamp}.pdf"
        
        with open(filename, 'wb') as f:
            f.write(response.content)
        
        print(f"✅ PDF baixado com sucesso!")
        print(f"📄 Arquivo: {filename}")
        print(f"📏 Tamanho: {len(response.content)} bytes")
        print(f"🔗 Content-Type: {response.headers.get('Content-Type', 'N/A')}")
        
        # Verificar se é um PDF válido
        if response.content.startswith(b'%PDF'):
            print("✅ Arquivo é um PDF válido")
        else:
            print("❌ Arquivo não parece ser um PDF")
            print(f"Primeiros bytes: {response.content[:50]}")
            
    else:
        print(f"❌ Erro HTTP: {response.status_code}")
        print(f"Resposta: {response.text[:200]}")
        
except Exception as e:
    print(f"❌ Erro: {e}")