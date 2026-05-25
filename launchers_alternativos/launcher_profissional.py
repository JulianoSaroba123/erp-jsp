#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ERP JSP Professional Launcher
Interface gráfica profissional para inicialização do sistema
"""

import tkinter as tk
from tkinter import ttk
import threading
import subprocess
import sys
import os
import webbrowser
import time
from tkinter import messagebox
import urllib.request

class ERPJSPLauncher:
    def __init__(self):
        self.root = tk.Tk()
        self.flask_process = None
        self.setup_window()
        self.setup_styles()
        self.create_widgets()
        
    def setup_window(self):
        """Configura a janela principal"""
        self.root.title("ERP JSP Professional")
        self.root.geometry("450x600")
        self.root.resizable(False, False)
        self.root.configure(bg='#0a0a0a')
        
        # Centralizar janela
        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth() // 2) - (450 // 2)
        y = (self.root.winfo_screenheight() // 2) - (600 // 2)
        self.root.geometry(f"450x600+{x}+{y}")
        
        # Ícone se existir
        try:
            if os.path.exists('app/static/img/favicon.ico'):
                self.root.iconbitmap('app/static/img/favicon.ico')
        except:
            pass
    
    def setup_styles(self):
        """Configura os estilos ttk"""
        style = ttk.Style()
        style.theme_use('clam')
        
        # Estilo para progressbar
        style.configure("Custom.Horizontal.TProgressbar",
                       background='#00aaff',
                       troughcolor='#2a2a2a',
                       borderwidth=0,
                       lightcolor='#00aaff',
                       darkcolor='#00aaff')
    
    def create_widgets(self):
        """Cria todos os widgets da interface"""
        
        # Frame principal
        main_frame = tk.Frame(self.root, bg='#0a0a0a')
        main_frame.pack(fill='both', expand=True, padx=20, pady=20)
        
        # Logo/Título
        title_frame = tk.Frame(main_frame, bg='#0a0a0a')
        title_frame.pack(fill='x', pady=(0, 20))
        
        # Logo JSP
        logo_label = tk.Label(title_frame, 
                             text="JSP",
                             font=('Arial', 36, 'bold'),
                             fg='#00aaff',
                             bg='#0a0a0a')
        logo_label.pack()
        
        subtitle_label = tk.Label(title_frame,
                                 text="Automação Industrial & Solar",
                                 font=('Arial', 12),
                                 fg='#cccccc',
                                 bg='#0a0a0a')
        subtitle_label.pack()
        
        # Linha decorativa
        line_frame = tk.Frame(main_frame, bg='#00aaff', height=2)
        line_frame.pack(fill='x', pady=20)
        
        # Título do sistema
        system_label = tk.Label(main_frame,
                               text="ERP Sistema Professional v3.0",
                               font=('Arial', 18, 'bold'),
                               fg='#ffffff',
                               bg='#0a0a0a')
        system_label.pack(pady=(0, 10))
        
        # Status
        self.status_var = tk.StringVar()
        self.status_var.set("Pronto para inicializar...")
        
        self.status_label = tk.Label(main_frame,
                                    textvariable=self.status_var,
                                    font=('Arial', 11),
                                    fg='#00aaff',
                                    bg='#0a0a0a')
        self.status_label.pack(pady=10)
        
        # Progress bar
        self.progress = ttk.Progressbar(main_frame, 
                                       style="Custom.Horizontal.TProgressbar",
                                       mode='determinate',
                                       length=300)
        self.progress.pack(pady=20)
        
        # Botão iniciar
        button_frame = tk.Frame(main_frame, bg='#0a0a0a')
        button_frame.pack(fill='x', pady=20)
        
        self.start_button = tk.Button(button_frame,
                                     text=" INICIAR SISTEMA",
                                     font=('Arial', 14, 'bold'),
                                     bg='#00aaff',
                                     fg='#ffffff',
                                     activebackground='#0088cc',
                                     activeforeground='#ffffff',
                                     border=0,
                                     pady=12,
                                     command=self.start_system)
        self.start_button.pack(fill='x')
        
        # Informações
        info_frame = tk.Frame(main_frame, bg='#1a1a1a', relief='ridge', bd=1)
        info_frame.pack(fill='x', pady=20)
        
        info_title = tk.Label(info_frame,
                             text=" Informações do Sistema",
                             font=('Arial', 12, 'bold'),
                             fg='#00aaff',
                             bg='#1a1a1a')
        info_title.pack(pady=(10, 5))
        
        info_items = [
            " URL: http://127.0.0.1:5001",
            "👤 Login: admin",
            "🔒 Senha: (configurável)",
            " Responsivo e moderno",
            " Interface futurística"
        ]
        
        for item in info_items:
            info_label = tk.Label(info_frame,
                                 text=item,
                                 font=('Arial', 9),
                                 fg='#cccccc',
                                 bg='#1a1a1a')
            info_label.pack(anchor='w', padx=15, pady=1)
        
        # Espaço final
        tk.Label(info_frame, text="", bg='#1a1a1a').pack(pady=5)
        
        # Botões inferiores
        bottom_frame = tk.Frame(main_frame, bg='#0a0a0a')
        bottom_frame.pack(fill='x', side='bottom')
        
        self.stop_button = tk.Button(bottom_frame,
                                    text="⏹ Parar Sistema",
                                    font=('Arial', 10),
                                    bg='#cc4400',
                                    fg='#ffffff',
                                    activebackground='#aa3300',
                                    border=0,
                                    pady=8,
                                    command=self.stop_system,
                                    state='disabled')
        self.stop_button.pack(side='left', fill='x', expand=True, padx=(0, 5))
        
        exit_button = tk.Button(bottom_frame,
                               text=" Sair",
                               font=('Arial', 10),
                               bg='#666666',
                               fg='#ffffff',
                               activebackground='#555555',
                               border=0,
                               pady=8,
                               command=self.exit_app)
        exit_button.pack(side='right', fill='x', expand=True, padx=(5, 0))
    
    def update_status(self, message):
        """Atualiza o status na interface"""
        self.status_var.set(message)
        self.root.update()
    
    def update_progress(self, value):
        """Atualiza a barra de progresso"""
        self.progress['value'] = value
        self.root.update()
    
    def start_system(self):
        """Inicia o sistema em thread separada"""
        self.start_button.config(state='disabled')
        thread = threading.Thread(target=self._start_system_thread)
        thread.daemon = True
        thread.start()
    
    def _start_system_thread(self):
        """Thread para inicializar o sistema"""
        try:
            # Verificações iniciais
            self.update_status("🔍 Verificando arquivos...")
            self.update_progress(10)
            time.sleep(0.5)
            
            if not os.path.exists('app'):
                raise Exception("Pasta 'app' não encontrada")
            
            if not os.path.exists('run.py'):
                raise Exception("Arquivo 'run.py' não encontrado")
            
            self.update_status(" Arquivos verificados")
            self.update_progress(30)
            time.sleep(0.5)
            
            # Iniciar Flask
            self.update_status(" Iniciando servidor Flask...")
            self.update_progress(50)
            
            # Verificar se estamos no executável ou script
            if hasattr(sys, 'frozen'):
                # Executável - usar Python do sistema
                import shutil
                python_cmd = shutil.which('python') or shutil.which('python3') or sys.executable
            else:
                # Script
                python_cmd = sys.executable
            
            # Verificar se o comando Python funciona
            try:
                result = subprocess.run([python_cmd, '--version'], 
                                      capture_output=True, timeout=5)
                if result.returncode != 0:
                    raise Exception(f"Python não funciona: {result.stderr.decode()}")
            except:
                raise Exception("Python não encontrado ou não funciona")
            
            # Comando para iniciar Flask com mais opções
            flask_cmd = [
                python_cmd, '-c', 
                '''
import sys, os
sys.path.insert(0, os.getcwd())
try:
    from app.app import create_app
    app = create_app()
    print(" Flask app criado com sucesso")
    app.run(host="0.0.0.0", port=5001, debug=False, use_reloader=False, threaded=True)
except Exception as e:
    print(f" Erro Flask: {e}")
    import traceback
    traceback.print_exc()
'''
            ]
            
            self.flask_process = subprocess.Popen(
                flask_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0,
                cwd=os.getcwd()
            )
            
            self.update_progress(70)
            time.sleep(1)
            
            # Aguardar servidor ficar disponível
            self.update_status(" Aguardando servidor...")
            self.update_progress(80)
            
            for i in range(45):  # 45 tentativas (45 segundos)
                try:
                    # Tentar várias URLs
                    urls_to_try = [
                        'http://127.0.0.1:5001/',
                        'http://127.0.0.1:5001/auth/login',
                        'http://localhost:5001/'
                    ]
                    
                    for url in urls_to_try:
                        try:
                            urllib.request.urlopen(url, timeout=2)
                            self.update_status(f" Servidor online! ({url})")
                            break
                        except:
                            continue
                    else:
                        # Se nenhuma URL funcionou, continue tentando
                        raise Exception("Tentando novamente...")
                    
                    # Se chegou aqui, alguma URL funcionou
                    break
                    
                except:
                    time.sleep(1)
                    progress = 80 + (i * 15 // 45)  # Progresso de 80% a 95%
                    self.update_progress(progress)
                    if i % 5 == 0:  # Atualizar status a cada 5 segundos
                        self.update_status(f" Aguardando servidor... ({i+1}/45s)")
            else:
                raise Exception("Servidor não respondeu em 45 segundos. Verifique se o Python está funcionando.")
            
            self.update_status(" Abrindo navegador...")
            self.update_progress(95)
            
            # Abrir navegador
            webbrowser.open('http://127.0.0.1:5001/auth/login')
            
            self.update_progress(100)
            self.update_status(" Sistema iniciado com sucesso!")
            
            # Habilitar botão parar
            self.stop_button.config(state='normal')
            
            # Minimizar janela após 3 segundos
            self.root.after(3000, self.minimize_window)
            
        except Exception as e:
            self.update_status(f" Erro: {str(e)}")
            self.update_progress(0)
            self.start_button.config(state='normal')
            
            # Mostrar logs do Flask se disponível
            error_details = str(e)
            if self.flask_process:
                try:
                    stdout, stderr = self.flask_process.communicate(timeout=2)
                    if stdout:
                        error_details += f"\n\nLogs Flask:\n{stdout.decode()}"
                    if stderr:
                        error_details += f"\n\nErros Flask:\n{stderr.decode()}"
                except:
                    pass
            
            # Criar janela de erro detalhada
            error_window = tk.Toplevel(self.root)
            error_window.title("Detalhes do Erro")
            error_window.geometry("600x400")
            error_window.configure(bg='#1a1a1a')
            
            # Texto do erro
            error_text = tk.Text(error_window, bg='#2a2a2a', fg='#ffffff', wrap='word')
            error_text.pack(fill='both', expand=True, padx=10, pady=10)
            error_text.insert('1.0', error_details)
            error_text.config(state='disabled')
            
            # Botão fechar
            tk.Button(error_window, text="Fechar", command=error_window.destroy,
                     bg='#cc4400', fg='#ffffff').pack(pady=5)
    
    def minimize_window(self):
        """Minimiza a janela"""
        self.root.iconify()
        self.update_status(" Sistema rodando... (janela minimizada)")
    
    def stop_system(self):
        """Para o sistema Flask"""
        if self.flask_process:
            try:
                self.flask_process.terminate()
                self.flask_process = None
                self.update_status("⏹ Sistema parado")
                self.update_progress(0)
                self.start_button.config(state='normal')
                self.stop_button.config(state='disabled')
            except Exception as e:
                messagebox.showerror("Erro", f"Erro ao parar sistema:\n{str(e)}")
    
    def exit_app(self):
        """Sai da aplicação"""
        if self.flask_process:
            self.stop_system()
        self.root.quit()
        self.root.destroy()
    
    def run(self):
        """Executa a aplicação"""
        try:
            self.root.protocol("WM_DELETE_WINDOW", self.exit_app)
            self.root.mainloop()
        except KeyboardInterrupt:
            self.exit_app()

if __name__ == "__main__":
    launcher = ERPJSPLauncher()
    launcher.run()