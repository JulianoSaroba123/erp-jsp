# -*- coding: utf-8 -*-
"""
Teste direto de login - verifica senha e cria usuário teste
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app.app import create_app
from app.extensoes import db
from app.auth.usuario_model import Usuario
from werkzeug.security import generate_password_hash

app = create_app()

with app.app_context():
    print("\n" + "=" * 60)
    print("🔑 TESTE DE LOGIN DIRETO")
    print("=" * 60)
    
    # Buscar admin
    admin = Usuario.query.filter_by(usuario='admin').first()
    
    if admin:
        print(f"\n✅ Usuário encontrado: {admin.usuario}")
        print(f"   ID: {admin.id}")
        print(f"   Nome: {admin.nome}")
        print(f"   Email: {admin.email}")
        print(f"   Ativo: {admin.ativo}")
        print(f"   Pode fazer login: {admin.pode_fazer_login}")
        
        # Testar senhas
        print("\n🔐 Testando senhas:")
        senhas_teste = ['admin123', 'admin', '123456', 'Admin123']
        
        for senha in senhas_teste:
            resultado = admin.verificar_senha(senha)
            print(f"   '{senha}': {'✅ CORRETA' if resultado else '❌ ERRADA'}")
        
        # Resetar senha para admin123
        print("\n🔄 Resetando senha para 'admin123'...")
        admin.senha_hash = generate_password_hash('admin123')
        admin.ativo = True
        admin.tentativas_login = 0
        admin.bloqueado_ate = None
        db.session.commit()
        
        # Verificar novamente
        if admin.verificar_senha('admin123'):
            print("✅ Senha 'admin123' configurada com SUCESSO!")
        else:
            print("❌ ERRO ao configurar senha!")
    else:
        print("\n❌ Usuário admin não encontrado!")
        print("   Criando usuário admin...")
        
        admin = Usuario(
            nome='Administrador',
            email='admin@jsp.com',
            usuario='admin',
            senha_hash=generate_password_hash('admin123'),
            tipo_usuario='admin',
            ativo=True,
            email_confirmado=True,
            primeiro_login=False
        )
        db.session.add(admin)
        db.session.commit()
        print("✅ Admin criado!")
    
    print("\n" + "=" * 60)
    print("📋 USE ESTAS CREDENCIAIS:")
    print("=" * 60)
    print("Usuário: admin")
    print("Senha: admin123")
    print("=" * 60 + "\n")
