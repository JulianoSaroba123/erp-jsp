#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script de diagnóstico Render - Pode ser executado via Shell
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.app import create_app
from app.extensoes import db

def diagnosticar():
    """Diagnóstico completo do ambiente Render."""
    app = create_app()
    
    with app.app_context():
        print("\n" + "="*50)
        print("🔍 DIAGNÓSTICO RENDER - ERP JSP")
        print("="*50 + "\n")
        
        # 1. Verificar DATABASE_URL
        print("1. Verificando DATABASE_URL...")
        db_url = app.config.get('SQLALCHEMY_DATABASE_URI')
        if db_url:
            # Oculta senha
            safe_url = db_url.split('@')[1] if '@' in db_url else db_url
            print(f"   ✓ Configurada: ...@{safe_url}")
        else:
            print("   ✗ NÃO CONFIGURADA!")
            return
        
        # 2. Verificar conexão com banco
        print("\n2. Testando conexão com banco...")
        try:
            from sqlalchemy import text
            db.session.execute(text('SELECT 1'))
            print("   ✓ Conexão OK")
        except Exception as e:
            print(f"   ✗ Erro na conexão: {e}")
            return
        
        # 3. Listar tabelas
        print("\n3. Verificando tabelas...")
        try:
            inspector = db.inspect(db.engine)
            tables = inspector.get_table_names()
            if tables:
                print(f"   ✓ {len(tables)} tabelas encontradas:")
                for table in sorted(tables):
                    print(f"      - {table}")
            else:
                print("   ⚠ Nenhuma tabela encontrada!")
                print("\n   🔧 Criando tabelas...")
                db.create_all()
                print("   ✓ Tabelas criadas!")
        except Exception as e:
            print(f"   ✗ Erro: {e}")
            return
        
        # 4. Verificar usuário admin
        print("\n4. Verificando usuário admin...")
        try:
            from app.auth.models import Usuario
            admin = Usuario.query.filter_by(tipo_usuario='admin').first()
            if admin:
                print(f"   ✓ Admin encontrado: {admin.usuario}")
            else:
                print("   ⚠ Admin não encontrado!")
                print("\n   🔧 Criando usuário admin...")
                from werkzeug.security import generate_password_hash
                admin = Usuario(
                    usuario='admin',
                    senha=generate_password_hash('admin123'),
                    nome_completo='Administrador',
                    email='admin@jspsolar.com.br',
                    tipo_usuario='admin',
                    ativo=True
                )
                db.session.add(admin)
                db.session.commit()
                print("   ✓ Admin criado!")
                print("      Usuario: admin")
                print("      Senha: admin123")
        except Exception as e:
            print(f"   ✗ Erro: {e}")
        
        # 5. Verificar dados
        print("\n5. Verificando dados importados...")
        try:
            from app.cliente.cliente_model import Cliente
            from app.fornecedor.fornecedor_model import Fornecedor
            from app.produto.produto_model import Produto
            from app.ordem_servico.ordem_servico_model import OrdemServico
            
            clientes = Cliente.query.filter_by(ativo=True).count()
            fornecedores = Fornecedor.query.filter_by(ativo=True).count()
            produtos = Produto.query.filter_by(ativo=True).count()
            ordens = OrdemServico.query.filter_by(ativo=True).count()
            
            print(f"   Clientes: {clientes}")
            print(f"   Fornecedores: {fornecedores}")
            print(f"   Produtos: {produtos}")
            print(f"   Ordens de Serviço: {ordens}")
            
            if clientes == 0:
                print("\n   ⚠ Sem dados! Acesse /painel/importar-auto após fazer login")
        except Exception as e:
            print(f"   ✗ Erro: {e}")
        
        print("\n" + "="*50)
        print("✅ DIAGNÓSTICO CONCLUÍDO")
        print("="*50 + "\n")
        
        print("📌 PRÓXIMOS PASSOS:")
        print("1. Se admin foi criado, faça login com:")
        print("   Usuario: admin")
        print("   Senha: admin123")
        print("2. Acesse: /painel/importar-auto")
        print("3. Isso importará todos os dados de exemplo")
        print("\n")

if __name__ == '__main__':
    diagnosticar()
