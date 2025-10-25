#!/usr/bin/env python
"""
ERP JSP v3.0 - Script de Deploy para Render
============================================

Este script é executado pelo Render durante o deploy.
Configura o banco de dados e cria usuário admin padrão.
"""

import os
import sys
from flask import Flask

def create_admin_user():
    """Cria usuário administrador padrão se não existir."""
    try:
        from app.app import create_app
        from app.extensoes import db
        from app.auth.usuario_model import Usuario
        
        app = create_app('production')
        
        with app.app_context():
            # Cria todas as tabelas
            db.create_all()
            
            # Verifica se já existe admin
            admin = Usuario.query.filter_by(tipo_usuario='admin', ativo=True).first()
            
            if not admin:
                # Cria admin padrão
                admin = Usuario.criar_admin_padrao()
                print(f"✅ Admin criado: {admin.usuario}")
                print(f"   Email: {admin.email}")
                print("   ⚠️  IMPORTANTE: Altere a senha padrão após o primeiro login!")
            else:
                print(f"✅ Admin já existe: {admin.usuario}")
                
    except Exception as e:
        print(f"❌ Erro ao criar admin: {e}")
        sys.exit(1)

def setup_configuration():
    """Configura dados básicos da empresa."""
    try:
        from app.app import create_app
        from app.configuracao.configuracao_model import Configuracao
        
        app = create_app('production')
        
        with app.app_context():
            config = Configuracao.get_solo()
            
            # Configura dados básicos se necessário
            if config.nome_fantasia == 'Minha Empresa':
                config.nome_fantasia = 'JSP Soluções Tecnológicas'
                config.razao_social = 'JSP Soluções Tecnológicas LTDA'
                config.email = 'contato@jspsolucoestecnologicas.com'
                config.save()
                print("✅ Configuração da empresa atualizada")
            else:
                print(f"✅ Configuração já existe: {config.nome_fantasia}")
                
    except Exception as e:
        print(f"❌ Erro ao configurar empresa: {e}")

if __name__ == '__main__':
    print("🚀 Iniciando setup de produção...")
    
    # Cria usuário admin
    create_admin_user()
    
    # Configura empresa
    setup_configuration()
    
    print("🎉 Setup de produção concluído!")