#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ERP JSP - Launcher Profissional
==============================

Launcher com interface gráfica para o sistema ERP JSP.
Inclui splash screen, barra de progresso e inicialização silenciosa.

Autor: JSP Soluções
Data: 2025
"""

import sys
import os
import time
import threading
import subprocess
import webbrowser
import configparser
from pathlib import Path

try:
    import tkinter as tk
    from tkinter import ttk, messagebox
    import tkinter.font as tkFont
except ImportError:
    # Fallback se tkinter não estiver disponível
    print("⚠️ Interface gráfica não disponível. Iniciando em modo texto...")
    sys.exit(1)

class ERPJSPLauncher:
    """Launcher profissional do ERP JSP com interface gráfica."""
    
    def __init__(self):
        self.root = None
        self.progress = None
        self.status_label = None
        self.server_process = None
        self.current_step = 0
        self.total_steps = 6
        
        # Carregar configurações
        self.config = self.load_config()
        
        # Verificar se está na pasta correta
        if not os.path.exists('app'):
            messagebox.showerror("Erro", "Pasta 'app' não encontrada!\nCertifique-se de que o launcher está na pasta correta.")
            sys.exit(1)
    
    def load_config(self):
        """Carrega configurações do arquivo launcher_config.ini."""
        config = configparser.ConfigParser()
        
        # Configurações padrão
        defaults = {
            'SISTEMA': {
                'nome': 'ERP JSP',
                'versao': '3.0',
                'autor': 'JSP Soluções',
                'porta': '5000',
                'host': '127.0.0.1'
            },
            'INTERFACE': {
                'cor_principal': '#1e3a8a',
                'cor_secundaria': '#3b82f6',
                'cor_texto': '#ffffff',
                'cor_fundo': '#1e3a8a',
                'largura_janela': '500',
                'altura_janela': '350'
            },
            'SERVIDOR': {
                'arquivo_inicio': 'run.py',
                'tempo_espera': '30',
                'auto_browser': 'true',
                'url_inicial': '/auth/login'
            }
        }
        
        # Tentar carregar do arquivo
        try:
            config.read('launcher_config.ini', encoding='utf-8')
        except:
            pass
        
        # Aplicar defaults para seções ausentes
        for section, options in defaults.items():
            if not config.has_section(section):
                config.add_section(section)
            for key, value in options.items():
                if not config.has_option(section, key):
                    config.set(section, key, value)
        
        return config
    
    def create_splash_screen(self):
        """Cria a tela de splash profissional."""
        self.root = tk.Tk()
        
        # Configurações da janela
        nome = self.config.get('SISTEMA', 'nome')
        versao = self.config.get('SISTEMA', 'versao')
        self.root.title(f"{nome} v{versao}")
        self.root.resizable(False, False)
        
        # Centralizar na tela
        window_width = self.config.getint('INTERFACE', 'largura_janela')
        window_height = self.config.getint('INTERFACE', 'altura_janela')
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        self.root.geometry(f"{window_width}x{window_height}+{x}+{y}")
        
        # Remover borda e ficar sempre no topo
        self.root.overrideredirect(True)
        self.root.attributes('-topmost', True)
        
        # Cores da configuração
        cor_principal = self.config.get('INTERFACE', 'cor_principal')
        cor_texto = self.config.get('INTERFACE', 'cor_texto')
        
        # Frame principal com gradiente simulado
        main_frame = tk.Frame(self.root, bg=cor_principal, bd=2, relief='raised')
        main_frame.pack(fill='both', expand=True, padx=2, pady=2)
        
        # Header com logo
        header_frame = tk.Frame(main_frame, bg=cor_principal, height=80)
        header_frame.pack(fill='x', pady=(20, 10))
        
        # Logo e título
        logo_font = tkFont.Font(family="Arial", size=24, weight="bold")
        title_font = tkFont.Font(family="Arial", size=16)
        subtitle_font = tkFont.Font(family="Arial", size=10)
        
        logo_label = tk.Label(header_frame, text=f" {nome}", font=logo_font, 
                             bg=cor_principal, fg=cor_texto)
        logo_label.pack(pady=(10, 5))
        
        title_label = tk.Label(header_frame, text="Sistema Integrado de Gestão", 
                              font=title_font, bg=cor_principal, fg='#e0e7ff')
        title_label.pack()
        
        autor = self.config.get('SISTEMA', 'autor')
        version_label = tk.Label(header_frame, text=f"Versão {versao} • {autor}", 
                                font=subtitle_font, bg=cor_principal, fg='#94a3b8')
        version_label.pack()
        
        # Área de progresso
        progress_frame = tk.Frame(main_frame, bg=cor_principal)
        progress_frame.pack(fill='x', padx=40, pady=20)
        
        # Label de status
        self.status_label = tk.Label(progress_frame, text="Inicializando sistema...", 
                                    font=("Arial", 11), bg=cor_principal, fg=cor_texto)
        self.status_label.pack(pady=(0, 15))
        
        # Barra de progresso com estilo moderno
        style = ttk.Style()
        style.theme_use('clam')
        cor_secundaria = self.config.get('INTERFACE', 'cor_secundaria')
        style.configure("Custom.Horizontal.TProgressbar", 
                       background=cor_secundaria,
                       troughcolor='#334155',
                       borderwidth=1,
                       lightcolor='#60a5fa',
                       darkcolor='#1d4ed8')
        
        self.progress = ttk.Progressbar(progress_frame, style="Custom.Horizontal.TProgressbar",
                                       mode='determinate', length=400)
        self.progress.pack(pady=(0, 10))
        
        # Percentual
        self.percent_label = tk.Label(progress_frame, text="0%", 
                                     font=("Arial", 10), bg=cor_principal, fg='#94a3b8')
        self.percent_label.pack()
        
        # Footer
        footer_frame = tk.Frame(main_frame, bg=cor_principal, height=50)
        footer_frame.pack(side='bottom', fill='x')
        
        footer_label = tk.Label(footer_frame, text="Aguarde enquanto o sistema está sendo carregado...", 
                               font=("Arial", 9), bg=cor_principal, fg='#94a3b8')
        footer_label.pack(pady=15)
        
        # Botão de cancelar (pequeno, no canto)
        cancel_btn = tk.Button(footer_frame, text="✕", command=self.cancel_startup,
                              font=("Arial", 8), bg='#ef4444', fg='white',
                              bd=0, padx=8, pady=2, cursor='hand2')
        cancel_btn.place(relx=0.95, rely=0.2, anchor='ne')
        
        self.root.update()
    
    def update_progress(self, step, message):
        """Atualiza a barra de progresso e mensagem."""
        self.current_step = step
        progress_percent = (step / self.total_steps) * 100
        
        self.progress['value'] = progress_percent
        self.status_label.config(text=message)
        self.percent_label.config(text=f"{int(progress_percent)}%")
        
        self.root.update()
        time.sleep(0.5)  # Pausa para visualização
    
    def cancel_startup(self):
        """Cancela a inicialização."""
        if messagebox.askyesno("Cancelar", "Deseja cancelar a inicialização do ERP JSP?"):
            if self.server_process:
                self.server_process.terminate()
            self.root.destroy()
            sys.exit(0)
    
    def check_python_modules(self):
        """Verifica se os módulos Python necessários estão disponíveis."""
        required_modules = ['flask', 'sqlalchemy', 'werkzeug']
        
        for module in required_modules:
            try:
                __import__(module)
            except ImportError:
                messagebox.showerror("Erro", 
                    f"Módulo Python '{module}' não encontrado!\n"
                    f"Execute: pip install {module}")
                return False
        return True
    
    def check_existing_server(self):
        """Verifica se já existe um servidor rodando."""
        try:
            import urllib.request
            host = self.config.get('SISTEMA', 'host')
            porta = self.config.get('SISTEMA', 'porta')
            
            response = urllib.request.urlopen(f'http://{host}:{porta}', timeout=2)
            return True  # Servidor já está rodando
        except:
            return False  # Servidor não está rodando
    
    def start_server(self):
        """Inicia o servidor Flask em background."""
        try:
            arquivo_inicio = self.config.get('SERVIDOR', 'arquivo_inicio')
            
            # Verificar se o arquivo existe
            if not os.path.exists(arquivo_inicio):
                raise Exception(f"Arquivo {arquivo_inicio} não encontrado!")
            
            # Iniciar servidor sem mostrar janela
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = subprocess.SW_HIDE
            
            self.server_process = subprocess.Popen(
                [sys.executable, arquivo_inicio],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                startupinfo=startupinfo,
                cwd=os.getcwd()
            )
            
            # Dar tempo para o processo iniciar
            time.sleep(3)
            
            # Verificar se o processo ainda está rodando
            if self.server_process.poll() is not None:
                stdout, stderr = self.server_process.communicate()
                error_msg = f"Servidor falhou ao iniciar (código: {self.server_process.returncode})\n"
                if stderr:
                    error_msg += f"Erro: {stderr.decode('utf-8', errors='ignore')[:300]}\n"
                raise Exception(error_msg)
            
            return True
            
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao iniciar servidor:\n{str(e)}")
            return False
    
    def wait_for_server(self):
        """Aguarda o servidor ficar disponível - versão simplificada."""
        import urllib.request
        import urllib.error
        
        host = self.config.get('SISTEMA', 'host')
        porta = self.config.get('SISTEMA', 'porta')
        
        try:
            # Tentar acessar o servidor
            response = urllib.request.urlopen(f'http://{host}:{porta}/', timeout=2)
            return True
        except urllib.error.HTTPError as e:
            # Se for qualquer erro HTTP, o servidor está rodando
            if e.code in [404, 302, 401, 500, 403]:
                return True
        except:
            pass
        
        return False
    
    def launch_browser(self):
        """Abre o navegador no sistema."""
        try:
            if self.config.getboolean('SERVIDOR', 'auto_browser'):
                host = self.config.get('SISTEMA', 'host')
                porta = self.config.get('SISTEMA', 'porta')
                url_inicial = self.config.get('SERVIDOR', 'url_inicial')
                webbrowser.open(f'http://{host}:{porta}{url_inicial}')
            return True
        except:
            return False
    
    def startup_sequence(self):
        """Sequência completa de inicialização."""
        try:
            arquivo_inicio = self.config.get('SERVIDOR', 'arquivo_inicio')
            
            # Passo 1: Verificar estrutura
            self.update_progress(1, "Verificando estrutura do sistema...")
            if not os.path.exists(arquivo_inicio):
                raise Exception(f"Arquivo {arquivo_inicio} não encontrado!")
            
            # Passo 2: Verificar módulos
            self.update_progress(2, "Verificando dependências Python...")
            if not self.check_python_modules():
                return False
            
            # Passo 3: Preparar ambiente
            self.update_progress(3, "Preparando ambiente de execução...")
            time.sleep(1)
            
            # Passo 4: Verificar se servidor já está rodando ou iniciar
            self.update_progress(4, "Verificando/iniciando servidor web...")
            if self.check_existing_server():
                self.update_progress(4, "Servidor já está ativo!")
                time.sleep(1)
            else:
                if not self.start_server():
                    return False
            
            # Passo 5: Aguardar servidor
            self.update_progress(5, "Aguardando servidor ficar disponível...")
            
            # Aguardar com timeout mais curto e feedback melhor
            servidor_ok = False
            max_tentativas = 15  # 15 segundos
            
            for tentativa in range(max_tentativas):
                if self.wait_for_server():
                    servidor_ok = True
                    break
                
                # Atualizar status a cada 3 tentativas
                if tentativa % 3 == 0:
                    tempo_restante = max_tentativas - tentativa
                    self.status_label.config(text=f"Aguardando servidor... ({tempo_restante}s)")
                    self.root.update()
                
                time.sleep(1)
            
            if not servidor_ok:
                # Tentar mais um pouco mas continuar mesmo assim
                self.status_label.config(text="⚠️ Servidor demorou para responder, tentando continuar...")
                self.root.update()
                time.sleep(2)
            
            # Passo 6: Abrir navegador
            self.update_progress(6, "Abrindo interface do sistema...")
            self.launch_browser()
            
            # Finalizar
            time.sleep(1)
            self.status_label.config(text="Sistema iniciado com sucesso!")
            time.sleep(2)
            
            return True
            
        except Exception as e:
            messagebox.showerror("Erro", f"Erro durante inicialização:\n{str(e)}")
            return False
    
    def run_startup_thread(self):
        """Executa a inicialização em thread separada."""
        def startup_worker():
            success = self.startup_sequence()
            if success:
                # Minimizar splash depois de sucesso
                self.root.after(2000, self.minimize_splash)
            else:
                self.root.after(1000, self.root.destroy)
        
        thread = threading.Thread(target=startup_worker, daemon=True)
        thread.start()
    
    def minimize_splash(self):
        """Minimiza a splash screen mas mantém processo ativo."""
        self.root.withdraw()  # Esconder janela
        
        # Criar ícone na bandeja (systemtray) simplificado
        self.create_tray_icon()
    
    def create_tray_icon(self):
        """Cria um ícone 'virtual' na bandeja (simplificado)."""
        # Para simplicidade, vamos apenas criar uma janela pequena minimizada
        tray_window = tk.Toplevel()
        
        nome = self.config.get('SISTEMA', 'nome')
        versao = self.config.get('SISTEMA', 'versao')
        host = self.config.get('SISTEMA', 'host')
        porta = self.config.get('SISTEMA', 'porta')
        
        tray_window.title(f"{nome} - Servidor Ativo")
        tray_window.geometry("300x100")
        tray_window.resizable(False, False)
        
        # Posicionar no canto inferior direito
        tray_window.geometry("+{}+{}".format(
            tray_window.winfo_screenwidth() - 320,
            tray_window.winfo_screenheight() - 150
        ))
        
        # Conteúdo
        tk.Label(tray_window, text=f" {nome} v{versao}", font=("Arial", 12, "bold")).pack(pady=5)
        tk.Label(tray_window, text=f"Servidor ativo em: http://{host}:{porta}").pack()
        
        btn_frame = tk.Frame(tray_window)
        btn_frame.pack(pady=10)
        
        tk.Button(btn_frame, text="Abrir Sistema", 
                 command=lambda: webbrowser.open(f'http://{host}:{porta}')).pack(side='left', padx=5)
        tk.Button(btn_frame, text="Encerrar", 
                 command=self.shutdown_system).pack(side='left', padx=5)
        
        # Minimizar automaticamente após 3 segundos
        tray_window.after(3000, lambda: tray_window.iconify())
    
    def shutdown_system(self):
        """Encerra o sistema completamente."""
        nome = self.config.get('SISTEMA', 'nome')
        if messagebox.askyesno("Encerrar", f"Deseja encerrar o {nome}?"):
            if self.server_process:
                self.server_process.terminate()
            self.root.quit()
            sys.exit(0)
    
    def run(self):
        """Executa o launcher."""
        try:
            self.create_splash_screen()
            self.run_startup_thread()
            self.root.mainloop()
        except KeyboardInterrupt:
            self.shutdown_system()
        except Exception as e:
            messagebox.showerror("Erro Fatal", f"Erro inesperado:\n{str(e)}")
            sys.exit(1)

if __name__ == "__main__":
    launcher = ERPJSPLauncher()
    launcher.run()