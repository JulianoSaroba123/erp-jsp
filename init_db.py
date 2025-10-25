# -*- coding: utf-8 -*-
"""
Script para inicializar o banco de dados do ERP JSP.
Resolve problemas de configuração e cria um banco funcional.
"""

import os
import sqlite3
from app.app import create_app
from app.extensoes import db
from app.cliente.cliente_model import Cliente
from app.fornecedor.fornecedor_model import Fornecedor  
from app.produto.produto_model import Produto

def init_database():
    """Inicializa o banco de dados com configuração funcional."""
    
    # Garantir que o diretório instance existe
    instance_dir = os.path.join(os.getcwd(), 'instance')
    if not os.path.exists(instance_dir):
        os.makedirs(instance_dir)
        print(f"Diretório {instance_dir} criado.")
    
    # Caminho do banco
    db_path = os.path.join(instance_dir, 'erp.db')
    print(f"Caminho do banco: {db_path}")
    
    # Criar aplicação com configuração simples
    app = create_app()
    
    # Forçar configuração do banco para caminho absoluto
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
    
    print(f"URI configurada: {app.config['SQLALCHEMY_DATABASE_URI']}")
    
    with app.app_context():
        try:
            # Remover todas as tabelas e recriar
            db.drop_all()
            print("Tabelas antigas removidas.")
            
            # Criar todas as tabelas novamente
            db.create_all()
            print("Tabelas criadas com sucesso!")
            
            # Testar criando um cliente
            cliente_teste = Cliente(
                nome="Cliente Teste",
                tipo="PF", 
                cpf_cnpj="123.456.789-00",
                email="teste@email.com",
                ativo=True
            )
            
            db.session.add(cliente_teste)
            db.session.commit()
            print("Cliente de teste criado!")
            
            # Verificar se consegue listar
            clientes = Cliente.query.all()
            print(f"Total de clientes no banco: {len(clientes)}")
            
            return True
            
        except Exception as e:
            print(f"Erro ao inicializar banco: {e}")
            import traceback
            traceback.print_exc()
            return False

if __name__ == '__main__':
    print("=== Inicializando Banco de Dados ERP JSP ===")
    if init_database():
        print("✅ Banco inicializado com sucesso!")
    else:
        print("❌ Erro na inicialização do banco!")