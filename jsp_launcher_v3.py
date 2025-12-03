#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
 JSP Sistema Launcher Simplificado - Versão v3
===============================================

Launcher que funciona tanto como script quanto executável.
Flask integrado diretamente para resolver problemas de subprocess.

Autor: JSP Soluções
Data: 2025
"""

import os
import sys
import time
import threading
import webbrowser
import socket
from pathlib import Path

# Configurações
SERVER_HOST = '127.0.0.1'
SERVER_PORT = 5001
LOGIN_URL = f'http://{SERVER_HOST}:{SERVER_PORT}/auth/login'

class JSPLauncherSimple:
    def __init__(self):
        self.flask_app = None
        self.flask_thread = None
        
    def setup_paths(self):
        """Configura paths para PyInstaller ou script"""
        if getattr(sys, 'frozen', False):
            # Executando como .exe
            base_dir = sys._MEIPASS
            print(f" Modo executável - Base: {base_dir}")
        else:
            # Executando como script
            base_dir = os.path.dirname(os.path.abspath(__file__))
            print(f" Modo script - Base: {base_dir}")
        
        # Configurar sys.path
        if base_dir not in sys.path:
            sys.path.insert(0, base_dir)
        
        # Configurar diretório de trabalho
        os.chdir(base_dir)
        return base_dir
    
    def wait_for_server(self, timeout=30):
        """Aguarda servidor estar pronto"""
        print(" Aguardando Flask iniciar...")
        
        for i in range(timeout):
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.settimeout(1)
                    if s.connect_ex((SERVER_HOST, SERVER_PORT)) == 0:
                        print(" Flask pronto!")
                        return True
            except:
                pass
            
            if i % 5 == 0 and i > 0:
                print(f" Ainda aguardando... ({i}/{timeout}s)")
            time.sleep(1)
        
        return False
    
    def start_flask_integrated(self):
        """Inicia Flask integrado na aplicação"""
        try:
            print(" Iniciando Flask integrado...")
            
            # Importar Flask
            from app.app import create_app
            print(" App importado com sucesso")
            
            # Criar aplicação
            self.flask_app = create_app()
            print(" App criado com sucesso")
            
            # Função para executar Flask
            def run_flask():
                try:
                    # Configurar logging
                    import logging
                    log = logging.getLogger('werkzeug')
                    log.setLevel(logging.ERROR)
                    
                    # Executar Flask
                    self.flask_app.run(
                        host=SERVER_HOST,
                        port=SERVER_PORT,
                        debug=False,
                        use_reloader=False,
                        threaded=True
                    )
                except Exception as e:
                    print(f" Erro Flask: {e}")
            
            # Iniciar thread
            self.flask_thread = threading.Thread(target=run_flask, daemon=True)
            self.flask_thread.start()
            
            print(" Flask thread iniciada")
            return True
            
        except Exception as e:
            print(f" Erro ao iniciar Flask: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def show_message_simple(self, title, message):
        """Mostra mensagem simples"""
        try:
            import tkinter as tk
            from tkinter import messagebox
            
            root = tk.Tk()
            root.withdraw()
            messagebox.showinfo(title, message)
            root.destroy()
        except:
            print(f"\n{title}\n{message}\n")
    
    def open_browser(self):
        """Abre navegador"""
        try:
            print(f" Abrindo: {LOGIN_URL}")
            webbrowser.open(LOGIN_URL)
            return True
        except Exception as e:
            print(f" Erro browser: {e}")
            return False
    
    def run(self):
        """Executa o launcher"""
        print("=" * 50)
        print("🏢 JSP SISTEMA v3.0 - INICIANDO")
        print("=" * 50)
        
        try:
            # Configurar paths
            base_dir = self.setup_paths()
            print(f" Diretório: {base_dir}")
            
            # Verificar arquivos essenciais
            app_dir = os.path.join(base_dir, 'app')
            if not os.path.exists(app_dir):
                self.show_message_simple("Erro JSP", "Pasta 'app' não encontrada!\nVerifique a instalação.")
                return
            
            print("📂 Estrutura de arquivos verificada")
            
            # Iniciar Flask
            if not self.start_flask_integrated():
                self.show_message_simple("Erro JSP", "Falha ao iniciar sistema Flask.\nContate o suporte técnico.")
                return
            
            # Aguardar Flask estar pronto
            if not self.wait_for_server(30):
                self.show_message_simple("Timeout JSP", "Sistema não iniciou dentro do tempo esperado.\nTente novamente.")
                return
            
            # Abrir navegador
            self.open_browser()
            
            # Mostrar mensagem de sucesso
            self.show_message_simple("JSP Sistema", f"Sistema iniciado com sucesso!\n\nAcesso: {LOGIN_URL}\n\nO navegador foi aberto automaticamente.")
            
            print(" JSP Sistema rodando!")
            print(" Mantenha esta janela aberta...")
            
            # Manter aplicação viva
            try:
                while True:
                    time.sleep(2)
                    # Verificar se thread ainda está ativa
                    if self.flask_thread and not self.flask_thread.is_alive():
                        print(" Flask thread parou")
                        break
            except KeyboardInterrupt:
                print("\n🛑 Encerrando...")
            
        except Exception as e:
            print(f" Erro geral: {e}")
            self.show_message_simple("Erro JSP", f"Erro inesperado:\n{str(e)}")

def main():
    """Função principal"""
    launcher = JSPLauncherSimple()
    launcher.run()

if __name__ == '__main__':
    main()