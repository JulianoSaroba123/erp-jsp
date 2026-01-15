# -*- coding: utf-8 -*-
"""
Script de diagnóstico completo do sistema de login
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app.app import create_app
from app.extensoes import db, login_manager
from app.auth.usuario_model import Usuario
from flask import session

def diagnostico_completo():
    """Executa diagnóstico completo do sistema de login"""
    
    app = create_app()
    
    with app.app_context():
        print("\n" + "=" * 70)
        print("🔍 DIAGNÓSTICO COMPLETO DO SISTEMA DE LOGIN")
        print("=" * 70)
        
        # 1. Verificar SECRET_KEY
        print("\n📌 1. SECRET_KEY:")
        secret = app.config.get('SECRET_KEY')
        print(f"   Configurada: {'✅ SIM' if secret else '❌ NÃO'}")
        if secret:
            print(f"   Valor: {secret[:30]}... (primeiros 30 chars)")
            print(f"   Tamanho: {len(secret)} caracteres")
        
        # 2. Verificar LoginManager
        print("\n📌 2. FLASK-LOGIN:")
        print(f"   login_view: {login_manager.login_view}")
        print(f"   session_protection: {login_manager.session_protection}")
        print(f"   login_message: {login_manager.login_message}")
        
        # 3. Verificar sessões
        print("\n📌 3. CONFIGURAÇÕES DE SESSÃO:")
        print(f"   SESSION_COOKIE_SECURE: {app.config.get('SESSION_COOKIE_SECURE')}")
        print(f"   SESSION_COOKIE_HTTPONLY: {app.config.get('SESSION_COOKIE_HTTPONLY')}")
        print(f"   SESSION_COOKIE_SAMESITE: {app.config.get('SESSION_COOKIE_SAMESITE')}")
        print(f"   PERMANENT_SESSION_LIFETIME: {app.config.get('PERMANENT_SESSION_LIFETIME')}")
        
        # 4. Verificar banco de dados
        print("\n📌 4. BANCO DE DADOS:")
        db_uri = app.config.get('SQLALCHEMY_DATABASE_URI')
        print(f"   URI: {db_uri[:50]}...")
        
        try:
            db.session.execute(db.text('SELECT 1'))
            print("   Conexão: ✅ OK")
        except Exception as e:
            print(f"   Conexão: ❌ ERRO - {e}")
            return False
        
        # 5. Verificar usuários
        print("\n📌 5. USUÁRIOS:")
        try:
            usuarios = Usuario.query.all()
            print(f"   Total: {len(usuarios)}")
            
            for u in usuarios:
                print(f"\n   👤 {u.usuario}:")
                print(f"      ID: {u.id}")
                print(f"      Nome: {u.nome}")
                print(f"      Email: {u.email}")
                print(f"      Tipo: {u.tipo_usuario}")
                print(f"      Ativo: {'✅' if u.ativo else '❌'}")
                print(f"      Email confirmado: {'✅' if u.email_confirmado else '❌'}")
                print(f"      Pode fazer login: {'✅' if u.pode_fazer_login else '❌'}")
                
                # Testar senha
                senha_ok = u.verificar_senha('admin123')
                print(f"      Senha 'admin123': {'✅' if senha_ok else '❌'}")
                
        except Exception as e:
            print(f"   ❌ ERRO ao listar usuários: {e}")
            import traceback
            traceback.print_exc()
            return False
        
        # 6. Verificar rotas
        print("\n📌 6. ROTAS DE AUTENTICAÇÃO:")
        auth_routes = [rule for rule in app.url_map.iter_rules() if 'auth' in rule.rule]
        for route in auth_routes:
            print(f"   {route.methods} {route.rule}")
        
        # 7. Teste de login simulado
        print("\n📌 7. TESTE DE LOGIN SIMULADO:")
        admin = Usuario.query.filter_by(usuario='admin').first()
        
        if admin:
            print(f"   Usuário encontrado: {admin.usuario}")
            print(f"   ID: {admin.id}")
            print(f"   Ativo: {admin.ativo}")
            print(f"   Pode fazer login: {admin.pode_fazer_login}")
            
            # Simular login_user
            from flask_login import login_user
            from flask import session as flask_session
            
            with app.test_request_context():
                # Configurar sessão
                flask_session.permanent = True
                
                resultado = login_user(admin, remember=False)
                print(f"   login_user retornou: {resultado}")
                
                if resultado:
                    print("   ✅ Login simulado com SUCESSO!")
                else:
                    print("   ❌ Login simulado FALHOU!")
        else:
            print("   ❌ Admin não encontrado!")
        
        print("\n" + "=" * 70)
        print("✅ DIAGNÓSTICO COMPLETO!")
        print("=" * 70)
        print("\n💡 PRÓXIMOS PASSOS:")
        print("   1. Se tudo estiver OK, acesse: http://127.0.0.1:5000/auth/login")
        print("   2. Use: admin / admin123")
        print("   3. Se ainda houver loop, abra o console do navegador (F12)")
        print("   4. Verifique a aba Network ao fazer login")
        print("   5. Procure por status 302 (redirect) após POST")
        print("=" * 70 + "\n")
        
        return True

if __name__ == '__main__':
    diagnostico_completo()
