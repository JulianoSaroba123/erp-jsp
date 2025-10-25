#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script para configurar logo da empresa no sistema
"""

from app.app import create_app
from app.extensoes import db
from app.configuracao.configuracao_model import Configuracao
import os

print("🎨 Configurando logo da empresa...")

app = create_app()

with app.app_context():
    try:
        # Busca configuração existente
        config = Configuracao.get_solo()
        
        print(f"📋 Configuração atual:")
        print(f"  Nome: {config.nome_fantasia}")
        print(f"  Logo: {config.logo or 'Não configurada'}")
        
        # Verifica logos disponíveis
        logos_disponiveis = []
        
        # Verifica logo na pasta uploads/configuracao
        uploads_path = os.path.join(os.path.dirname(__file__), 'uploads', 'configuracao')
        if os.path.exists(uploads_path):
            for arquivo in os.listdir(uploads_path):
                if arquivo.lower().endswith(('.jpg', '.jpeg', '.png', '.gif')):
                    logos_disponiveis.append(f"configuracao/{arquivo}")
                    print(f"  📁 Encontrada: uploads/{arquivo}")
        
        # Verifica logo na pasta static
        static_path = os.path.join(os.path.dirname(__file__), 'static', 'img')
        if os.path.exists(static_path):
            for arquivo in os.listdir(static_path):
                if arquivo.lower().endswith(('.jpg', '.jpeg', '.png', '.gif')):
                    logos_disponiveis.append(f"img/{arquivo}")
                    print(f"  📁 Encontrada: static/img/{arquivo}")
        
        if logos_disponiveis:
            print(f"\n🖼️  Logos disponíveis: {len(logos_disponiveis)}")
            for i, logo in enumerate(logos_disponiveis, 1):
                print(f"  {i}. {logo}")
            
            # Configura a primeira logo encontrada se não houver uma configurada
            if not config.logo and logos_disponiveis:
                # Prioriza a logo da configuracao se existir
                logo_escolhida = None
                for logo in logos_disponiveis:
                    if 'configuracao' in logo:
                        logo_escolhida = logo
                        break
                
                if not logo_escolhida:
                    logo_escolhida = logos_disponiveis[0]
                
                config.logo = logo_escolhida
                
                # Configura também o nome da empresa se não estiver configurado
                if config.nome_fantasia == 'Minha Empresa':
                    config.nome_fantasia = 'JSP Soluções Tecnológicas'
                    config.razao_social = 'JSP Soluções Tecnológicas LTDA'
                
                config.save()
                
                print(f"\n✅ Logo configurada: {logo_escolhida}")
                print(f"✅ Nome da empresa: {config.nome_fantasia}")
            elif config.logo:
                print(f"\n✅ Logo já configurada: {config.logo}")
        else:
            print("\n❌ Nenhuma logo encontrada nas pastas:")
            print("  - uploads/configuracao/")
            print("  - static/img/")
        
        print(f"\n🎉 Configuração finalizada!")
        print(f"🌐 Teste acessando: http://127.0.0.1:5001/auth/login")
        
    except Exception as e:
        print(f"❌ Erro: {e}")
        import traceback
        traceback.print_exc()