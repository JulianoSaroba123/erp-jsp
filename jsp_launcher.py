#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🚀 JSP Sistema - Launcher Executável
====================================

Script principal que:
1. Inicia o servidor Flask em background
2. Aguarda o servidor estar pronto
3. Abre o navegador na URL de login
4. Mantém o servidor rodando

Autor: JSP Soluções
Data: 2025
"""

import os
import sys
import time
import threading
import webbrowser
import subprocess
import socket
from pathlib import Path

# Configurações
SERVER_HOST = '127.0.0.1'
SERVER_PORT = 5001
LOGIN_URL = f'http://{SERVER_HOST}:{SERVER_PORT}/auth/login'
MAX_WAIT_TIME = 30  # segundos

class JSPLauncher:
    def __init__(self):
        self.server_process = None
        self.server_ready = False
        
    def check_port_available(self, host, port):
        """Verifica se a porta está disponível"""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(1)
                result = s.connect_ex((host, port))
                return result != 0  # True se porta está livre
        except:
            return True
    
    def wait_for_server(self, max_wait=30):
        """Aguarda o servidor estar pronto"""
        print("⏳ Aguardando servidor Flask iniciar...")
        
        for i in range(max_wait):
            try:
                import urllib.request
                urllib.request.urlopen(f'http://{SERVER_HOST}:{SERVER_PORT}', timeout=1)
                print("✅ Servidor Flask está pronto!")
                return True
            except:
                if i < 3:
                    print(f"🔄 Aguardando... ({i+1}/3)")
                time.sleep(1)
        
        print("❌ Timeout: Servidor não respondeu")
        return False
    
    def start_flask_server(self):
        """Inicia o servidor Flask"""
        try:
            # Determinar o script principal
            if os.path.exists('run.py'):
                script = 'run.py'
            elif os.path.exists('app.py'):
                script = 'app.py'
            else:
                raise FileNotFoundError("Não foi possível encontrar run.py ou app.py")
            
            print(f"🚀 Iniciando servidor Flask ({script})...")
            
            # Configurar variáveis de ambiente
            env = os.environ.copy()
            env['FLASK_ENV'] = 'production'
            env['PYTHONPATH'] = os.getcwd()
            
            # Iniciar servidor em processo separado
            if getattr(sys, 'frozen', False):
                # Se estiver executando como .exe
                # Usar o Python bundleado
                python_exe = sys.executable
            else:
                # Se estiver executando como script
                python_exe = sys.executable
            
            # Comando para iniciar o servidor
            cmd = [python_exe, script]
            
            # Iniciar processo sem janela de console
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = subprocess.SW_HIDE
            
            self.server_process = subprocess.Popen(
                cmd,
                env=env,
                cwd=os.getcwd(),
                startupinfo=startupinfo,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            
            return True
            
        except Exception as e:
            print(f"❌ Erro ao iniciar servidor: {e}")
            return False
    
    def open_browser(self):
        """Abre o navegador na URL de login"""
        try:
            print(f"🌐 Abrindo navegador em: {LOGIN_URL}")
            webbrowser.open(LOGIN_URL)
            return True
        except Exception as e:
            print(f"❌ Erro ao abrir navegador: {e}")
            return False
    
    def cleanup(self):
        """Limpa recursos ao fechar"""
        if self.server_process:
            try:
                self.server_process.terminate()
                print("🛑 Servidor Flask encerrado")
            except:
                pass
    
    def run(self):
        """Executa o launcher principal"""
        print("=" * 50)
        print("🏢 JSP SISTEMA - INICIANDO...")
        print("=" * 50)
        
        try:
            # Verificar se porta está livre
            if not self.check_port_available(SERVER_HOST, SERVER_PORT):
                print(f"⚠️  Porta {SERVER_PORT} já está em uso")
                print(f"🌐 Tentando abrir navegador diretamente...")
                self.open_browser()
                return
            
            # Iniciar servidor Flask
            if not self.start_flask_server():
                input("❌ Falha ao iniciar servidor. Pressione Enter para sair...")
                return
            
            # Aguardar servidor estar pronto
            if not self.wait_for_server(MAX_WAIT_TIME):
                print("❌ Servidor não iniciou corretamente")
                input("Pressione Enter para sair...")
                return
            
            # Abrir navegador
            if not self.open_browser():
                print("❌ Falha ao abrir navegador")
            
            print("✅ JSP Sistema iniciado com sucesso!")
            print(f"🌐 Acesse: {LOGIN_URL}")
            print("🔄 Pressione Ctrl+C ou feche esta janela para parar")
            
            # Manter rodando até interrupção
            try:
                while True:
                    time.sleep(1)
                    # Verificar se processo ainda existe
                    if self.server_process and self.server_process.poll() is not None:
                        print("❌ Servidor Flask parou inesperadamente")
                        break
            except KeyboardInterrupt:
                print("\n🛑 Encerrando JSP Sistema...")
            
        except Exception as e:
            print(f"❌ Erro geral: {e}")
            input("Pressione Enter para sair...")
        finally:
            self.cleanup()

def main():
    """Função principal"""
    # Configurar diretório de trabalho
    if getattr(sys, 'frozen', False):
        # Se executando como .exe
        app_dir = os.path.dirname(sys.executable)
    else:
        # Se executando como script
        app_dir = os.path.dirname(os.path.abspath(__file__))
    
    os.chdir(app_dir)
    
    # Executar launcher
    launcher = JSPLauncher()
    launcher.run()

if __name__ == '__main__':
    main()