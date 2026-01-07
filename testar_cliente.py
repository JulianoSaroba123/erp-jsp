# -*- coding: utf-8 -*-
"""Testar rota de clientes"""

from app.app import create_app

app = create_app()

with app.test_client() as client:
    print("\n🧪 Testando rota /cliente/listar...")
    
    try:
        response = client.get('/cliente/listar')
        print(f"Status: {response.status_code}")
        
        if response.status_code == 500:
            print(f"\n❌ ERRO 500!")
            print(f"Response: {response.data.decode('utf-8')[:500]}")
        elif response.status_code == 200:
            print(f"✅ Sucesso! Página carregada")
        else:
            print(f"⚠️ Status: {response.status_code}")
            
    except Exception as e:
        print(f"\n❌ EXCEÇÃO: {type(e).__name__}")
        print(f"Mensagem: {str(e)}")
        import traceback
        traceback.print_exc()
