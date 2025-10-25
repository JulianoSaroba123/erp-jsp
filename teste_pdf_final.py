#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Teste final do PDF após correção
"""

import requests
import sys

def main():
    """Testa se o PDF está sendo gerado corretamente."""
    print("🔍 TESTANDO PDF FINAL")
    print("=" * 40)
    
    url = "http://127.0.0.1:5001/ordem_servico/1/relatorio-pdf"
    
    try:
        print(f"🌐 Fazendo requisição para: {url}")
        response = requests.get(url, timeout=10)
        
        print(f"📊 Status Code: {response.status_code}")
        print(f"📄 Content-Type: {response.headers.get('Content-Type', 'N/A')}")
        print(f"📏 Content-Length: {len(response.content)} bytes")
        
        if response.status_code == 200:
            if 'application/pdf' in response.headers.get('Content-Type', ''):
                # Salvar PDF para inspeção
                with open('teste_pdf_final.pdf', 'wb') as f:
                    f.write(response.content)
                print("✅ PDF gerado com sucesso!")
                print("💾 PDF salvo como: teste_pdf_final.pdf")
                print("📋 Verifique se os valores dos serviços estão corretos no PDF")
            else:
                print("⚠️ Resposta não é um PDF")
                print("📝 Conteúdo HTML (primeiros 500 chars):")
                print(response.text[:500])
        else:
            print(f"❌ Erro HTTP {response.status_code}")
            print("📝 Resposta:")
            print(response.text[:500])
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Erro na requisição: {e}")
        print("🔧 Verifique se o servidor está rodando em http://127.0.0.1:5001")
        
    except Exception as e:
        print(f"❌ Erro geral: {e}")

if __name__ == "__main__":
    main()