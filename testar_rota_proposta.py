#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script de teste para rota de visualização de proposta.
Testa a rota completa como se fosse uma requisição.
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app import create_app
from app.extensoes import db
from app.proposta.proposta_model import Proposta

def testar_rota_proposta():
    """Testa a rota de visualização de proposta."""
    app = create_app()
    
    with app.app_context():
        print("=" * 60)
        print("🔍 TESTE DE ROTA - VISUALIZAÇÃO DE PROPOSTA")
        print("=" * 60)
        
        # Buscar proposta ID 19 (do screenshot)
        proposta_id = 19
        print(f"\n📋 Buscando proposta ID: {proposta_id}")
        
        proposta = Proposta.query.filter_by(id=proposta_id, ativo=True).first()
        
        if not proposta:
            print(f"❌ PROPOSTA {proposta_id} NÃO ENCONTRADA!")
            print("\n🔍 Buscando todas as propostas ativas...")
            propostas = Proposta.query.filter_by(ativo=True).all()
            print(f"   Encontradas {len(propostas)} propostas ativas:")
            for p in propostas[:10]:
                print(f"   • ID {p.id}: {p.codigo} - {p.titulo}")
        else:
            print(f"✅ Proposta encontrada: {proposta.codigo}")
            print(f"   Título: {proposta.titulo}")
            print(f"   Status: {proposta.status}")
            print(f"   Cliente: {proposta.cliente.nome if proposta.cliente else 'N/A'}")
        
        # Testar a rota usando test_client
        print(f"\n🌐 Testando rota HTTP: /propostas/{proposta_id}")
        
        with app.test_client() as client:
            # Fazer requisição GET para a rota
            response = client.get(f'/propostas/{proposta_id}')
            
            print(f"\n📊 RESULTADO DA REQUISIÇÃO:")
            print(f"   Status Code: {response.status_code}")
            print(f"   Content-Type: {response.content_type}")
            print(f"   Tamanho da resposta: {len(response.data)} bytes")
            
            if response.status_code == 200:
                content = response.data.decode('utf-8')
                
                # Verificar se tem conteúdo HTML básico
                has_html = '<html' in content.lower() or '<!doctype' in content.lower()
                has_body = '<body' in content.lower()
                has_proposta_header = 'proposta-header' in content
                has_content = len(content) > 1000
                
                print(f"\n🔍 ANÁLISE DO CONTEÚDO:")
                print(f"   {'✅' if has_html else '❌'} Tem tag HTML")
                print(f"   {'✅' if has_body else '❌'} Tem tag BODY")
                print(f"   {'✅' if has_proposta_header else '❌'} Tem header da proposta")
                print(f"   {'✅' if has_content else '❌'} Tem conteúdo suficiente (>1KB)")
                
                # Verificar se tem erros no HTML
                if 'error' in content.lower() or 'erro' in content.lower():
                    print(f"\n⚠️  POSSÍVEIS ERROS NO HTML:")
                    lines = content.split('\n')
                    for i, line in enumerate(lines):
                        if 'error' in line.lower() or 'erro' in line.lower():
                            print(f"   Linha {i+1}: {line.strip()[:100]}")
                
                # Verificar se o template está sendo renderizado
                if 'proposta.codigo' in content or '{{ proposta' in content:
                    print(f"\n❌ TEMPLATE NÃO ESTÁ SENDO RENDERIZADO!")
                    print(f"   Variáveis Jinja2 não processadas encontradas no HTML")
                
                # Mostrar primeiras linhas do HTML
                print(f"\n📄 PRIMEIRAS 20 LINHAS DO HTML:")
                lines = content.split('\n')[:20]
                for i, line in enumerate(lines, 1):
                    print(f"   {i:3d}: {line[:80]}")
                
            elif response.status_code == 404:
                print(f"\n❌ ERRO 404: Proposta não encontrada ou rota não registrada")
            elif response.status_code == 500:
                print(f"\n❌ ERRO 500: Erro interno do servidor")
                content = response.data.decode('utf-8')
                print(f"\n📄 Resposta de erro:")
                print(content[:500])
            else:
                print(f"\n⚠️  Status code inesperado: {response.status_code}")

if __name__ == '__main__':
    testar_rota_proposta()
