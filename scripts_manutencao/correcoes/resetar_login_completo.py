# -*- coding: utf-8 -*-
"""
Script para resetar completamente o sistema de login
Resolve problemas de loop de login
"""

import sys
import os

# Adiciona o diretório raiz ao path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app.app import create_app
from app.extensoes import db
from app.auth.usuario_model import Usuario
from werkzeug.security import generate_password_hash

def resetar_login():
    """Reseta completamente o sistema de login"""
    
    app = create_app()
    
    with app.app_context():
        print("=" * 60)
        print("🔄 RESETANDO SISTEMA DE LOGIN")
        print("=" * 60)
        
        # 1. Limpar sessões antigas (se usando SQLite/PostgreSQL)
        print("\n1️⃣ Verificando usuários existentes...")
        usuarios = Usuario.query.all()
        print(f"   Usuários encontrados: {len(usuarios)}")
        
        for u in usuarios:
            print(f"   - {u.usuario} (ID: {u.id}, Ativo: {u.ativo})")
        
        # 2. Criar/Atualizar admin
        print("\n2️⃣ Verificando usuário admin...")
        admin = Usuario.query.filter_by(usuario='admin').first()
        
        senha_admin = 'admin123'
        
        if admin:
            print("   ✅ Admin encontrado - atualizando...")
            admin.senha_hash = generate_password_hash(senha_admin)
            admin.ativo = True
            admin.email_confirmado = True
            admin.tipo_usuario = 'admin'
            admin.primeiro_login = False
            admin.tentativas_login = 0
            admin.bloqueado_ate = None
        else:
            print("   ➕ Criando novo admin...")
            admin = Usuario(
                nome='Administrador',
                email='admin@jsp.com',
                usuario='admin',
                senha_hash=generate_password_hash(senha_admin),
                tipo_usuario='admin',
                ativo=True,
                email_confirmado=True,
                primeiro_login=False
            )
            db.session.add(admin)
        
        try:
            db.session.commit()
            print("   ✅ Admin configurado com sucesso!")
        except Exception as e:
            db.session.rollback()
            print(f"   ❌ Erro ao configurar admin: {e}")
            return False
        
        # 3. Verificar SECRET_KEY
        print("\n3️⃣ Verificando SECRET_KEY...")
        secret_key = app.config.get('SECRET_KEY')
        print(f"   SECRET_KEY: {secret_key[:20]}... (primeiros 20 chars)")
        
        # 4. Verificar LoginManager
        print("\n4️⃣ Verificando LoginManager...")
        from app.extensoes import login_manager
        print(f"   login_view: {login_manager.login_view}")
        print(f"   session_protection: {login_manager.session_protection}")
        
        print("\n" + "=" * 60)
        print("✅ RESET COMPLETO!")
        print("=" * 60)
        print("\n📋 CREDENCIAIS DE LOGIN:")
        print(f"   Usuário: admin")
        print(f"   Senha: {senha_admin}")
        print("\n🔗 Acesse: http://127.0.0.1:5000/auth/login")
        print("=" * 60)
        
        return True

if __name__ == '__main__':
    resetar_login()
