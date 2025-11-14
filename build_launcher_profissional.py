#!/usr/bin/env python3
"""
Script para gerar executável profissional do ERP JSP
"""

import PyInstaller.__main__
import os

def build_launcher():
    """Gera o executável profissional"""
    
    print("🔧 Gerando executável profissional do ERP JSP...")
    print("📦 Isso pode demorar alguns minutos...")
    
    args = [
        'launcher_profissional.py',
        '--onefile',
        '--windowed',
        '--name=ERP_JSP_Professional',
        '--add-data=app;app',
        '--add-data=database;database', 
        '--add-data=static;static',
        '--hidden-import=werkzeug',
        '--hidden-import=flask',
        '--hidden-import=jinja2',
        '--hidden-import=sqlalchemy',
        '--hidden-import=tkinter',
        '--hidden-import=tkinter.ttk',
        '--hidden-import=threading',
        '--hidden-import=webbrowser',
        '--hidden-import=subprocess',
        '--distpath=.',
        '--workpath=build_temp',
        '--clean'
    ]
    
    try:
        PyInstaller.__main__.run(args)
        print("\n✅ Executável criado com sucesso!")
        print("📁 Arquivo: ERP_JSP_Professional.exe")
        print("🎯 Para usar: Clique duplo no arquivo .exe")
        
    except Exception as e:
        print(f"\n❌ Erro ao gerar executável: {e}")
        return False
    
    return True

if __name__ == "__main__":
    build_launcher()