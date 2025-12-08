"""
Testa o cadastro de cliente via POST
"""
import requests
import json

# URL local
url = "http://127.0.0.1:5001/cliente/novo"

# Dados do cliente teste
dados = {
    'nome': 'Cliente Teste Automatico',
    'tipo': 'pf',
    'cpf_cnpj': '123.456.789-00',
    'telefone': '(14) 99999-9999',
    'email': 'teste@teste.com',
    'endereco': 'Rua Teste, 123',
    'cidade': 'Botucatu',
    'estado': 'SP',
    'cep': '18600-000'
}

print("🧪 Testando cadastro de cliente...")
print(f"📋 Dados: {dados['nome']} - {dados['cpf_cnpj']}")

try:
    # Faz POST
    response = requests.post(url, data=dados, allow_redirects=False)
    
    print(f"\n✅ Status: {response.status_code}")
    print(f"📍 Redirect: {response.headers.get('Location', 'Nenhum')}")
    
    if response.status_code == 302:
        print("✅ Redirecionamento OK - Cliente cadastrado!")
        
        # Verifica se foi salvo no banco
        from app.app import create_app
        from app.cliente.cliente_model import Cliente
        
        app = create_app()
        with app.app_context():
            cliente = Cliente.query.filter_by(cpf_cnpj='123.456.789-00').first()
            if cliente:
                print(f"✅ Cliente encontrado no banco!")
                print(f"   ID: {cliente.id}")
                print(f"   Nome: {cliente.nome}")
                print(f"   Ativo: {cliente.ativo}")
            else:
                print("❌ Cliente NÃO foi salvo no banco!")
    else:
        print(f"❌ Erro no cadastro!")
        print(f"Response: {response.text[:500]}")
        
except Exception as e:
    print(f"❌ Erro: {e}")
    import traceback
    traceback.print_exc()
