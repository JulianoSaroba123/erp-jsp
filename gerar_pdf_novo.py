#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gerar novo PDF forçando refresh e sem cache
"""

import requests
import time
import sys

def main():
    """Gera novo PDF sem cache."""
    print("🔄 GERANDO NOVO PDF (SEM CACHE)")
    print("=" * 50)
    
    # URL com timestamp para evitar cache
    timestamp = int(time.time())
    url = f"http://127.0.0.1:5001/ordem_servico/1/relatorio-pdf?t={timestamp}"
    
    # Headers para evitar cache
    headers = {
        'Cache-Control': 'no-cache, no-store, must-revalidate',
        'Pragma': 'no-cache',
        'Expires': '0'
    }
    
    try:
        print(f"🌐 Requisição: {url}")
        print("🚫 Headers anti-cache enviados")
        
        response = requests.get(url, headers=headers, timeout=15)
        
        print(f"📊 Status: {response.status_code}")
        print(f"📄 Content-Type: {response.headers.get('Content-Type', 'N/A')}")
        print(f"📏 Tamanho: {len(response.content)} bytes")
        
        if response.status_code == 200 and 'pdf' in response.headers.get('Content-Type', ''):
            # Salvar com timestamp
            filename = f"pdf_novo_{timestamp}.pdf"
            with open(filename, 'wb') as f:
                f.write(response.content)
            print(f"✅ PDF salvo como: {filename}")
            print("📋 IMPORTANTE: Use este novo arquivo para verificar os valores!")
            print("🔍 Deve mostrar os 3 serviços com valores corretos:")
            print("   - Manutenção preventiva: 2.5h × R$ 80.00 = R$ 200.00")
            print("   - Limpeza e calibração: 1.0h × R$ 120.00 = R$ 120.00")  
            print("   - Atualização de software: 0.5h × R$ 100.00 = R$ 50.00")
            return True
        else:
            print(f"❌ Erro: {response.status_code}")
            if hasattr(response, 'text'):
                print("📝 Resposta:", response.text[:300])
            return False
            
    except Exception as e:
        print(f"❌ Erro: {e}")
        return False

if __name__ == "__main__":
    success = main()
    if not success:
        print("\n🔧 Verifique se o servidor está rodando!")
        print("📍 Tente: http://127.0.0.1:5001/ordem_servico/1/relatorio-pdf")
        sys.exit(1)