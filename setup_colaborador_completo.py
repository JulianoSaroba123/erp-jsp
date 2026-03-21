#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script COMPLETO para:
1. Criar tabela usuario se não existir
2. Adicionar coluna tipo_usuario se não existir
3. Criar/atualizar usuário colaborador
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.app import app
from app.extensoes import db
from app.auth.usuario_model import Usuario

print("=" * 60)
print("🔧 SETUP COMPLETO - USUÁRIO COLABORADOR")
print("=" * 60)

with app.app_context():
    try:
        print("\n📊 Criando tabelas se necessário...")
        db.create_all()
        print("✅ Tabelas verificadas/criadas!")
        
        # Verificar se usuário admin existe (criar se não)
        admin = Usuario.query.filter_by(usuario='admin').first()
        if not admin:
            print("\n⚠️  Criando usuário admin padrão...")
            admin = Usuario(
                usuario='admin',
                nome='Administrador',
                email='admin@jsp.com',
                tipo_usuario='admin',
                ativo=True
            )
            admin.set_password('admin123')
            db.session.add(admin)
            db.session.commit()
            print("✅ Admin criado! (admin / admin123)")
        
        # Verificar/criar usuário colaborador
        colaborador = Usuario.query.filter_by(usuario='colaborador').first()
        
        if colaborador:
            tipo_atual = getattr(colaborador, 'tipo_usuario', None)
            print(f"\n📌 Usuário 'colaborador' encontrado")
            print(f"   Tipo atual: {tipo_atual}")
            
            if tipo_atual != 'colaborador':
                print("   🔧 Atualizando tipo...")
                colaborador.tipo_usuario = 'colaborador'
                db.session.commit()
                print("   ✅ Atualizado!")
            else:
                print("   ✅ Já está correto!")
        else:
            print("\n💡 Criando usuário colaborador...")
            colaborador = Usuario(
                usuario='colaborador',
                nome='Técnico Colaborador',
                email='colaborador@jsp.com',
                tipo_usuario='colaborador',
                ativo=True
            )
            colaborador.set_password('123456')
            db.session.add(colaborador)
            db.session.commit()
            print("✅ Colaborador criado!")
        
        # Verificação final
        print("\n" + "=" * 60)
        print("📊 USUÁRIOS CONFIGURADOS")
        print("=" * 60)
        
        usuarios = Usuario.query.filter_by(ativo=True).all()
        for u in usuarios:
            tipo = getattr(u, 'tipo_usuario', 'indefinido')
            emoji = '👑' if tipo == 'admin' else ('✅' if tipo == 'colaborador' else '👤')
            print(f"{emoji} {u.usuario:<15} | {tipo:<12} | {u.nome}")
        
        print("\n" + "=" * 60)
        print("🎯 PRONTO PARA TESTAR")
        print("=" * 60)
        print("\n1. Faça logout no navegador")
        print("2. Login com:")
        print("   👑 admin / admin123  (vê tudo)")
        print("   ✅ colaborador / 123456  (sem seção financeira)")
        print("3. Acesse: Nova Ordem de Serviço")
        print("4. Verifique o banner de debug no topo")
        print("\n" + "=" * 60)
        
    except Exception as e:
        print(f"\n❌ Erro: {e}")
        import traceback
        traceback.print_exc()
        db.session.rollback()
