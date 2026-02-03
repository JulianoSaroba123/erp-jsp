# -*- coding: utf-8 -*-
"""
Script para simular localmente o erro do Render
================================================
Testa a rota /cliente/20 localmente para reproduzir o erro.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app

def testar_rota_cliente_20():
    """Testa a rota /cliente/20 localmente."""
    app = create_app('development')
    
    with app.app_context():
        with app.test_client() as client:
            print(f"\n{'='*60}")
            print("🧪 TESTANDO ROTA /cliente/20 LOCALMENTE")
            print(f"{'='*60}\n")
            
            # Teste 1: GET /cliente/20
            print("📍 Acessando GET /cliente/20...")
            response = client.get('/cliente/20', follow_redirects=False)
            
            print(f"Status Code: {response.status_code}")
            print(f"Location: {response.headers.get('Location', 'N/A')}")
            
            if response.status_code == 302:
                print(f"✅ Redirecionamento funcionou! → {response.headers.get('Location')}")
            elif response.status_code == 500:
                print("❌ ERRO 500 - Reproduzido localmente!")
                print("\nResposta:")
                print(response.data.decode('utf-8')[:500])
            elif response.status_code == 404:
                print("✅ Erro 404 retornado corretamente")
            else:
                print(f"⚠️ Status inesperado: {response.status_code}")
            
            # Teste 2: Verificar se mensagens flash foram criadas
            print(f"\n{'='*60}")
            print("🔍 VERIFICANDO MENSAGENS FLASH")
            print(f"{'='*60}\n")
            
            with client.session_transaction() as session:
                flashes = session.get('_flashes', [])
                if flashes:
                    print("📬 Mensagens flash encontradas:")
                    for categoria, mensagem in flashes:
                        print(f"   [{categoria}] {mensagem}")
                else:
                    print("📭 Nenhuma mensagem flash")

if __name__ == '__main__':
    testar_rota_cliente_20()
