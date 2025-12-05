#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script COMPLETO para setup inicial do Render
Execute no Shell do Render: python setup_render.py
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def setup_completo():
    """Setup completo do banco Render."""
    print("\n" + "="*60)
    print("🚀 SETUP COMPLETO RENDER - ERP JSP")
    print("="*60 + "\n")
    
    from app.app import create_app
    from app.extensoes import db
    
    app = create_app()
    
    with app.app_context():
        # 1. Criar todas as tabelas
        print("📋 PASSO 1: Criando tabelas...")
        try:
            db.create_all()
            print("   ✓ Tabelas criadas com sucesso!\n")
        except Exception as e:
            print(f"   ✗ Erro ao criar tabelas: {e}\n")
            return False
        
        # 2. Criar usuário admin
        print("👤 PASSO 2: Criando usuário admin...")
        try:
            from app.auth.models import Usuario
            from werkzeug.security import generate_password_hash
            
            admin = Usuario.query.filter_by(usuario='admin').first()
            if admin:
                print("   ℹ Admin já existe\n")
            else:
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
                print("      👉 Usuario: admin")
                print("      👉 Senha: admin123\n")
        except Exception as e:
            print(f"   ✗ Erro ao criar admin: {e}\n")
            db.session.rollback()
        
        # 3. Criar configuração inicial
        print("⚙️ PASSO 3: Criando configuração inicial...")
        try:
            from app.configuracao.configuracao_model import Configuracao
            
            config = Configuracao.get_solo()
            if not config:
                config = Configuracao(
                    nome_fantasia='JSP ELÉTRICA',
                    razao_social='JSP ELÉTRICA INDUSTRIAL LTDA',
                    cnpj='12.345.678/0001-90',
                    telefone='(14) 3815-3649',
                    email='contato@jspsolar.com.br',
                    banco='Banco do Brasil',
                    agencia='0001-9',
                    conta='12345-6'
                )
                db.session.add(config)
                db.session.commit()
                print("   ✓ Configuração criada!\n")
            else:
                print("   ℹ Configuração já existe\n")
        except Exception as e:
            print(f"   ✗ Erro ao criar configuração: {e}\n")
            db.session.rollback()
        
        # 4. Testar conexão e listar tabelas
        print("🔍 PASSO 4: Verificando banco de dados...")
        try:
            from sqlalchemy import text, inspect
            
            # Testar conexão
            db.session.execute(text('SELECT 1'))
            print("   ✓ Conexão com banco OK")
            
            # Listar tabelas
            inspector = inspect(db.engine)
            tables = inspector.get_table_names()
            print(f"   ✓ {len(tables)} tabelas encontradas:")
            for table in sorted(tables)[:10]:  # Primeiras 10
                print(f"      • {table}")
            if len(tables) > 10:
                print(f"      ... e mais {len(tables) - 10} tabelas")
            print()
        except Exception as e:
            print(f"   ✗ Erro: {e}\n")
            return False
        
        # 5. Verificar dados
        print("📊 PASSO 5: Contando registros...")
        try:
            from app.cliente.cliente_model import Cliente
            from app.fornecedor.fornecedor_model import Fornecedor
            from app.produto.produto_model import Produto
            
            clientes = Cliente.query.count()
            fornecedores = Fornecedor.query.count()
            produtos = Produto.query.count()
            
            print(f"   • Clientes: {clientes}")
            print(f"   • Fornecedores: {fornecedores}")
            print(f"   • Produtos: {produtos}\n")
        except Exception as e:
            print(f"   ⚠ Erro ao contar: {e}\n")
        
        # 6. Teste de inserção
        print("🧪 PASSO 6: Testando inserção no banco...")
        try:
            from app.cliente.cliente_model import Cliente
            
            # Tentar inserir cliente teste
            teste = Cliente(
                nome='CLIENTE TESTE RENDER',
                tipo_pessoa='juridica',
                cnpj='00.000.000/0001-00',
                email='teste@render.com',
                telefone='(00) 0000-0000',
                ativo=True
            )
            db.session.add(teste)
            db.session.commit()
            
            # Verificar se foi salvo
            verificar = Cliente.query.filter_by(nome='CLIENTE TESTE RENDER').first()
            if verificar:
                print("   ✓ Teste de inserção OK!")
                # Deletar teste
                db.session.delete(verificar)
                db.session.commit()
                print("   ✓ Teste de exclusão OK!\n")
            else:
                print("   ✗ Registro não foi salvo!\n")
                return False
        except Exception as e:
            print(f"   ✗ Erro no teste: {e}\n")
            db.session.rollback()
            return False
        
        # 7. Resumo final
        print("="*60)
        print("✅ SETUP CONCLUÍDO COM SUCESSO!")
        print("="*60)
        print("\n📝 Próximos passos:")
        print("   1. Acesse seu app no Render")
        print("   2. Faça login com: admin / admin123")
        print("   3. Vá em Painel → Importar dados (se necessário)")
        print("   4. Configure a empresa em Configurações")
        print("\n🔗 URL do app: https://erp-jsp-th5o.onrender.com")
        print("\n" + "="*60 + "\n")
        
        return True

if __name__ == '__main__':
    try:
        sucesso = setup_completo()
        sys.exit(0 if sucesso else 1)
    except Exception as e:
        print(f"\n❌ ERRO FATAL: {e}\n")
        import traceback
        traceback.print_exc()
        sys.exit(1)
