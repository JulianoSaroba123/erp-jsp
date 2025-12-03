#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Build simples do executável JSP Sistema
"""

import os
import subprocess
import sys
import shutil

def clean_build():
    """Limpa diretórios de build"""
    dirs_to_clean = ['build', 'dist', '__pycache__']
    for dir_name in dirs_to_clean:
        if os.path.exists(dir_name):
            try:
                shutil.rmtree(dir_name)
                print(f" {dir_name}/ limpo")
            except:
                pass

def build_exe():
    """Build do executável"""
    print("🏢 JSP SISTEMA - BUILD SIMPLES")
    print("=" * 50)
    
    # Limpar build anterior
    clean_build()
    
    # Comando PyInstaller simples
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--onefile",
        "--windowed", 
        "--clean",
        "--name=JSP_Sistema",
        "--add-data", "app;app",
        "--add-data", "static;static", 
        "--add-data", "database;database",
        "jsp_launcher.py"
    ]
    
    print("🔨 Executando PyInstaller...")
    print(f"Comando: {' '.join(cmd)}")
    
    try:
        # Executar com timeout menor
        result = subprocess.run(cmd, check=True, timeout=300)
        
        # Verificar se executável foi criado
        exe_path = "dist/JSP_Sistema.exe"
        if os.path.exists(exe_path):
            size = os.path.getsize(exe_path) / (1024*1024)  # MB
            print(f"\n SUCESSO!")
            print(f" Executável: {exe_path}")
            print(f"📏 Tamanho: {size:.1f} MB")
            return True
        else:
            print("\n Executável não encontrado")
            return False
            
    except subprocess.TimeoutExpired:
        print("\n Timeout - build cancelado")
        return False
    except subprocess.CalledProcessError as e:
        print(f"\n Erro no build: {e}")
        return False
    except Exception as e:
        print(f"\n Erro: {e}")
        return False

if __name__ == "__main__":
    if build_exe():
        print("\n Build concluído com sucesso!")
        print(" Para testar: dist/JSP_Sistema.exe")
    else:
        print("\n💥 Build falhou!")