#!/usr/bin/env python3
"""
Script para verificar e criar clientes de teste
"""

from aplicacao import create_app
from aplicacao.cliente.cliente_model import Cliente
from aplicacao.extensoes import db

def main():
    app = create_app()
    
    with app.app_context():
        print("=== VERIFICAÇÃO DE CLIENTES ===")
        
        # Contar clientes existentes
        total_clientes = Cliente.query.count()
        print(f"Total de clientes no banco: {total_clientes}")
        
        if total_clientes == 0:
            print("\n❌ Não há clientes cadastrados!")
            print("💾 Criando clientes de teste...")
            
            # Criar clientes de teste
            clientes_teste = [
                Cliente(
                    nome="João Silva Santos",
                    email="joao.silva@email.com",
                    telefone="(11) 99999-1111",
                    cpf_cnpj="123.456.789-01",
                    endereco="Rua das Flores, 123",
                    apelido="João"
                ),
                Cliente(
                    nome="Maria Oliveira Pereira",
                    email="maria.oliveira@email.com", 
                    telefone="(11) 99999-2222",
                    cpf_cnpj="987.654.321-02",
                    endereco="Av. Brasil, 456",
                    apelido="Maria"
                ),
                Cliente(
                    nome="Pedro Costa Ferreira",
                    email="pedro.costa@email.com",
                    telefone="(11) 99999-3333", 
                    cpf_cnpj="456.789.123-03",
                    endereco="Rua São Paulo, 789",
                    apelido="Pedro"
                ),
                Cliente(
                    nome="Ana Souza Lima",
                    email="ana.souza@email.com",
                    telefone="(11) 99999-4444",
                    cpf_cnpj="789.123.456-04", 
                    endereco="Rua Rio de Janeiro, 321",
                    apelido="Ana"
                ),
                Cliente(
                    nome="Carlos Mendes Rocha",
                    email="carlos.mendes@email.com",
                    telefone="(11) 99999-5555",
                    cpf_cnpj="321.654.987-05",
                    endereco="Av. Paulista, 1000",
                    apelido="Carlos"
                )
            ]
            
            try:
                for cliente in clientes_teste:
                    db.session.add(cliente)
                
                db.session.commit()
                print(f"✅ {len(clientes_teste)} clientes de teste criados com sucesso!")
                
            except Exception as e:
                db.session.rollback()
                print(f"❌ Erro ao criar clientes: {str(e)}")
        
        else:
            print(f"✅ Encontrados {total_clientes} clientes no banco")
            
            # Mostrar alguns clientes
            clientes = Cliente.query.limit(5).all()
            print("\n📋 Clientes encontrados:")
            for cliente in clientes:
                print(f"  - ID: {cliente.id} | Nome: {cliente.nome} | Email: {cliente.email}")

if __name__ == "__main__":
    main()