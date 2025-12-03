#!/usr/bin/env python3
"""
Build script para criar executável profissional do ERP JSP
"""

import PyInstaller.__main__
import os
import sys

def build_professional_launcher():
    """Constrói o launcher profissional"""
    
    print(" Construindo ERP JSP Professional Launcher...")
    print(" Incluindo dependências e recursos...")
    
    args = [
        'launcher_professional.py',
        '--onefile',
        '--windowed',
        '--name=ERP_JSP_Professional',
        '--icon=app/static/img/favicon.ico',
        '--add-data=app;app',
        '--add-data=database;database',
        '--add-data=run.py;.',
        '--add-data=static;static',
        '--hidden-import=tkinter',
        '--hidden-import=tkinter.ttk',
        '--hidden-import=webbrowser',
        '--hidden-import=threading',
        '--hidden-import=urllib.request',
        '--hidden-import=subprocess',
        '--hidden-import=pathlib',
        '--distpath=.',
        '--workpath=build_temp',
        '--specpath=build_temp',
        '--clean',
        '--noconfirm'
    ]
    
    try:
        PyInstaller.__main__.run(args)
        print(" Build concluído com sucesso!")
        print(" Arquivo criado: ERP_JSP_Professional.exe")
        print(" Execute o arquivo para iniciar o sistema!")
        
    except Exception as e:
        print(f" Erro durante o build: {e}")
        return False
        
    return True

if __name__ == "__main__":
    success = build_professional_launcher()
    if success:
        input("\n Pressione Enter para continuar...")
    else:
        input("\n Pressione Enter para sair...")