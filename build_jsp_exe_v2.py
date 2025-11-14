#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🔧 Build JSP Sistema Executável - Versão Melhorada v2
====================================================

Script para gerar executável do JSP Sistema usando PyInstaller
com Flask integrado e todos os recursos necessários.

Autor: JSP Soluções  
Data: 2025
"""

import os
import sys
import shutil
import subprocess

def build_jsp_executable():
    """Gera o executável JSP Sistema com configuração otimizada"""
    
    print("🔨 CONSTRUINDO EXECUTÁVEL JSP SISTEMA v2")
    print("=" * 50)
    
    # Limpar builds anteriores
    if os.path.exists('dist'):
        print("🧹 Limpando builds anteriores...")
        shutil.rmtree('dist')
    
    if os.path.exists('build'):
        shutil.rmtree('build')
    
    # Comando PyInstaller otimizado para Flask
    cmd = [
        'pyinstaller',
        '--onefile',                    # Arquivo único
        '--windowed',                   # Sem console
        '--name=JSP_Sistema',           # Nome do executável
        
        # ========== DADOS E RECURSOS ==========
        '--add-data=app;app',                    # Aplicação Flask
        '--add-data=static;static',              # Arquivos estáticos  
        '--add-data=database;database',          # Banco de dados
        
        # ========== IMPORTS HIDDEN FLASK ==========
        '--hidden-import=app.app',               # App principal
        '--hidden-import=app.config',            # Configurações
        '--hidden-import=app.auth.auth_routes',  # Rotas auth
        '--hidden-import=app.cliente.cliente_routes',  # Rotas cliente
        '--hidden-import=app.fornecedor.fornecedor_routes',  # Rotas fornecedor
        '--hidden-import=app.produto.produto_routes',  # Rotas produto
        '--hidden-import=app.painel.painel_routes',  # Rotas painel
        '--hidden-import=app.financeiro.financeiro_routes',  # Rotas financeiro
        
        # ========== IMPORTS HIDDEN MODELOS ==========
        '--hidden-import=app.auth.auth_model',
        '--hidden-import=app.cliente.cliente_model', 
        '--hidden-import=app.fornecedor.fornecedor_model',
        '--hidden-import=app.produto.produto_model',
        '--hidden-import=app.financeiro.financeiro_model',
        
        # ========== IMPORTS FLASK ESSENCIAIS ==========
        '--hidden-import=flask',
        '--hidden-import=flask_sqlalchemy',
        '--hidden-import=sqlalchemy',
        '--hidden-import=werkzeug',
        '--hidden-import=jinja2',
        '--hidden-import=markupsafe',
        
        # ========== IMPORTS SISTEMA ==========
        '--hidden-import=sqlite3',
        '--hidden-import=hashlib',
        '--hidden-import=datetime',
        '--hidden-import=decimal',
        
        # ========== CONFIGURAÇÕES AVANÇADAS ==========
        '--noconfirm',                  # Não pedir confirmação
        '--clean',                      # Limpeza antes do build
        '--log-level=WARN',            # Log apenas warnings
        
        'jsp_launcher.py'              # Script principal
    ]
    
    print("📦 Iniciando build com PyInstaller...")
    print("⚙️ Incluindo Flask integrado e todos os recursos...")
    
    try:
        # Executar PyInstaller
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        
        print("✅ BUILD CONCLUÍDO COM SUCESSO!")
        print("=" * 50)
        
        # Verificar arquivo gerado
        exe_path = 'dist/JSP_Sistema.exe'
        if os.path.exists(exe_path):
            size_mb = os.path.getsize(exe_path) / (1024 * 1024)
            print(f"📁 Executável criado: {exe_path}")
            print(f"📏 Tamanho: {size_mb:.1f} MB")
            print(f"🎯 Flask integrado diretamente no executável")
            print(f"🔧 Todos os recursos incluídos")
        else:
            print("❌ Arquivo executável não foi encontrado!")
            return False
            
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ ERRO NO BUILD:")
        print(f"Stdout: {e.stdout}")
        print(f"Stderr: {e.stderr}")
        return False
    except Exception as e:
        print(f"❌ ERRO GERAL: {e}")
        return False

if __name__ == '__main__':
    success = build_jsp_executable()
    if success:
        print("\n🚀 PRONTO! Execute: dist/JSP_Sistema.exe")
    else:
        print("\n❌ Build falhou. Verifique os erros acima.")
        sys.exit(1)