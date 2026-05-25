#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Launcher simples do ERP JSP - Garantido para funcionar
"""

import os
import sys
import time
import threading
import webbrowser
from subprocess import Popen, PIPE, DEVNULL
import tkinter as tk
from tkinter import messagebox

def show_message(title, message, type_msg="info"):
    """Mostra mensagem usando tkinter"""
    root = tk.Tk()
    root.withdraw()  # Oculta a janela principal
    
    if type_msg == "error":
        messagebox.showerror(title, message)
    elif type_msg == "warning":
        messagebox.showwarning(title, message)
    else:
        messagebox.showinfo(title, message)
    
    root.destroy()

def start_flask_server():
    """Inicia o servidor Flask"""
    try:
        # Verifica se estamos no diretório correto
        if not os.path.exists('app'):
            os.chdir(os.path.dirname(os.path.abspath(__file__)))
        
        if not os.path.exists('app'):
            show_message("Erro", "Pasta 'app' não encontrada. Verifique a instalação.", "error")
            return None
        
        # Comando para iniciar o Flask
        cmd = [sys.executable, '-c', '''
import sys, os
sys.path.insert(0, os.getcwd())
from app.app import create_app
app = create_app()
app.run(host="127.0.0.1", port=5001, debug=False, use_reloader=False)
''']
        
        # Inicia o processo Flask
        process = Popen(cmd, stdout=PIPE, stderr=PIPE, creationflags=0x08000000)  # CREATE_NO_WINDOW
        return process
        
    except Exception as e:
        show_message("Erro Flask", f"Erro ao iniciar servidor: {str(e)}", "error")
        return None

def wait_for_server(max_attempts=30):
    """Aguarda o servidor ficar disponível"""
    import urllib.request
    
    for i in range(max_attempts):
        try:
            urllib.request.urlopen('http://127.0.0.1:5001/', timeout=1)
            return True
        except:
            time.sleep(1)
    return False

def main():
    """Função principal do launcher"""
    show_message("ERP JSP", " Iniciando ERP JSP Sistema...\nPor favor aguarde...")
    
    # Inicia o servidor Flask
    flask_process = start_flask_server()
    
    if not flask_process:
        return
    
    # Aguarda o servidor ficar disponível
    if wait_for_server():
        # Abre o navegador
        webbrowser.open('http://127.0.0.1:5001/auth/login')
        show_message("ERP JSP", " Sistema iniciado com sucesso!\n\n Abrindo navegador...\n URL: http://127.0.0.1:5001")
    else:
        show_message("Erro", " Timeout: Servidor não respondeu em 30 segundos", "error")
        if flask_process:
            flask_process.terminate()
        return
    
    # Mantém o processo vivo
    try:
        show_message("ERP JSP", " Sistema rodando!\n\n⚠️ IMPORTANTE: Não feche esta janela!\n\n Para parar o sistema, feche o navegador e esta janela.")
    except KeyboardInterrupt:
        pass
    finally:
        if flask_process:
            flask_process.terminate()

if __name__ == "__main__":
    main()