#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para configurar usuário colaborador usando Flask app context
"""

import sys
import os

# Adicionar diretório raiz ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.app import app
from app.extensoes import db
from app.auth.usuario_model import Usuario
from sqlalchemy import inspect, text

print("=" * 60)
print("🔧 CONFIGURAR USUÁRIO COLABORADOR")
print("=" * 60)

with app.app_context():
    try:
        # 1. Verificar se coluna tipo_usuario existe
        inspector = inspect(db.engine)
        colunas = [col['name'] for col in inspector.get_columns('usuario')]
        
        print(f"\n📋 Colunas na tabela usuario: {len(colunas)}")
        
        if 'tipo_usuario' not in colunas:
            print("\n⚠️  Coluna tipo_usuario não existe. Criando...")
            db.session.execute(text("ALTER TABLE usuario ADD COLUMN tipo_usuario VARCHAR(20) DEFAULT 'usuario'"))
            db.session.commit()
            print("✅ Coluna tipo_usuario criada!")
        else:
            print("\n✅ Coluna tipo_usuario já existe")
        
        # 2. Verificar se usuário colaborador existe
        usuario = Usuario.query.filter_by(username='colaborador').first()
        
        if usuario:
            tipo_atual = getattr(usuario, 'tipo_usuario', None)
            print(f"\n📌 Usuário encontrado:")
            print(f"   ID: {usuario.id}")
            print(f"   Username: {usuario.username}")
            print(f"   Nome: {usuario.nome}")
            print(f"   Tipo atual: {tipo_atual if tipo_atual else 'NÃO DEFINIDO'}")
            
            if tipo_atual != 'colaborador':
                print(f"\n🔧 Atualizando tipo_usuario para 'colaborador'...")
                usuario.tipo_usuario = 'colaborador'
                db.session.commit()
                print("✅ Tipo atualizado com sucesso!")
            else:
                print("\n✅ Tipo já está correto!")
        else:
            print("\n⚠️  Usuário 'colaborador' não existe!")
            print("\n💡 Criando usuário colaborador...")
            
            novo_usuario = Usuario(
                username='colaborador',
                nome='Técnico Colaborador',
                email='colaborador@jsp.com',
                tipo_usuario='colaborador',
                ativo=True
            )
            novo_usuario.set_password('123456')
            db.session.add(novo_usuario)
            db.session.commit()
            
            print("✅ Usuário colaborador criado!")
            print("   Username: colaborador")
            print("   Senha: 123456")
        
        # 3. Verificar resultado final
        print("\n" + "=" * 60)
        print("📊 VERIFICAÇÃO FINAL")
        print("=" * 60)
        
        usuario_final = Usuario.query.filter_by(username='colaborador').first()
        
        if usuario_final:
            tipo = getattr(usuario_final, 'tipo_usuario', 'NÃO DEFINIDO')
            print(f"\n✅ Configuração confirmada:")
            print(f"   Username: {usuario_final.username}")
            print(f"   Nome: {usuario_final.nome}")
            print(f"   Tipo: {tipo}")
            
            if tipo == 'colaborador':
                print(f"\n🎯 Pronto para usar!")
                print(f"   1. Faça logout no navegador")
                print(f"   2. Login com: colaborador / 123456")
                print(f"   3. As seções financeiras devem estar ocultas")
                print(f"   4. Verifique o banner de debug no topo do formulário")
            else:
                print(f"\n⚠️  ATENÇÃO: Tipo ainda não está correto!")
        
        # 4. Listar todos usuários
        print("\n" + "=" * 60)
        print("📊 TODOS USUÁRIOS ATIVOS")
        print("=" * 60)
        
        usuarios = Usuario.query.filter_by(ativo=True).all()
        for u in usuarios:
            tipo_u = getattr(u, 'tipo_usuario', 'NÃO_DEFINIDO')
            emoji = '👑' if tipo_u == 'admin' else ('✅' if tipo_u == 'colaborador' else '👤')
            print(f"{emoji} {u.username:<15} | Tipo: {tipo_u:<12} | {u.nome}")
        
    except Exception as e:
        print(f"\n❌ Erro: {e}")
        import traceback
        traceback.print_exc()
        db.session.rollback()

print("\n" + "=" * 60)
