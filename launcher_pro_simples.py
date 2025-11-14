#!/usr/bin/env python3
"""
🚀 ERP JSP Professional Launcher - Versão Simplificada
Interface gráfica profissional para iniciar o ERP JSP
"""

import os
import sys
import time
import subprocess
import webbrowser
import threading
try:
    import tkinter as tk
    from tkinter import ttk, messagebox
    TKINTER_AVAILABLE = True
except ImportError:
    TKINTER_AVAILABLE = False

def show_console_loading():
    """Tela de carregamento no console"""
    print("\n" + "="*60)
    print("██████╗░░█████╗░░██████╗░  ░░░░░██╗░██████╗░██████╗░")
    print("██╔════╝░██╔══██╗██╔════╝░  ░░░░░██║██╔════╝██╔══██╗")
    print("█████╗░░██║░░██║██║░░██╗░  ░░░░░██║╚█████╗░██████╔╝")
    print("██╔══╝░░██║░░██║██║░░╚██╗██╗░░██║░░╚═══██╗██╔═══╝░")
    print("███████╗╚█████╔╝╚██████╔╝╚█████╔╝░██████╔╝██║░░░░░")
    print("╚══════╝░╚════╝░░╚═════╝░░╚════╝░░╚═════╝░╚═╝░░░░░")
    print("\n⚡ JSP Automação Industrial & Solar ⚡")
    print("🚀 ERP Sistema Professional v3.0")
    print("="*60)
    
def start_system():
    """Inicia o sistema ERP"""
    try:
        show_console_loading()
        
        print("\n🔍 Verificando sistema...")
        if not os.path.exists('app'):
            print("❌ ERRO: Pasta 'app' não encontrada!")
            return False
            
        if not os.path.exists('run.py'):
            print("❌ ERRO: Arquivo 'run.py' não encontrado!")
            return False
            
        print("✅ Arquivos verificados")
        
        print("🚀 Iniciando servidor Flask...")
        print("⏳ Por favor aguarde...")
        
        # Iniciar Flask em processo separado
        flask_process = subprocess.Popen(
            [sys.executable, 'run.py'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            creationflags=0x08000000 if os.name == 'nt' else 0  # CREATE_NO_WINDOW
        )
        
        print("✅ Processo iniciado")
        
        # Aguardar servidor (com animação)
        print("🌐 Aguardando servidor... ", end="", flush=True)
        for i in range(15):
            print(".", end="", flush=True)
            time.sleep(1)
            
        print("\n🎯 Abrindo navegador...")
        webbrowser.open('http://127.0.0.1:5001/auth/login')
        
        print("✅ Sistema iniciado com sucesso!")
        print("🔗 URL: http://127.0.0.1:5001")
        print("\n" + "="*60)
        print("⚠️  IMPORTANTE:")
        print("   • Sistema rodando em segundo plano")
        print("   • Mantenha esta janela aberta")
        print("   • Para parar: feche esta janela")
        print("="*60)
        
        return flask_process
        
    except Exception as e:
        print(f"❌ Erro: {e}")
        return False

def main_console():
    """Launcher modo console"""
    try:
        flask_process = start_system()
        if flask_process:
            print("\n👁️  Monitorando sistema... (Ctrl+C para parar)")
            while True:
                if flask_process.poll() is not None:
                    print("⚠️ Processo Flask encerrado")
                    break
                time.sleep(5)
    except KeyboardInterrupt:
        print("\n🛑 Parando sistema...")
        if 'flask_process' in locals() and flask_process:
            flask_process.terminate()
        print("✅ Sistema parado")
    except Exception as e:
        print(f"❌ Erro: {e}")
    finally:
        input("\n📋 Pressione Enter para sair...")

def main_gui():
    """Launcher modo gráfico"""
    class ERPLauncher:
        def __init__(self):
            self.root = tk.Tk()
            self.flask_process = None
            self.setup_ui()
            
        def setup_ui(self):
            # Configurar janela
            self.root.title("ERP JSP Professional Launcher")
            self.root.geometry("500x350")
            self.root.configure(bg="#1a1a1a")
            self.root.resizable(False, False)
            
            # Centralizar
            self.root.update_idletasks()
            x = (self.root.winfo_screenwidth() // 2) - (500 // 2)
            y = (self.root.winfo_screenheight() // 2) - (350 // 2)
            self.root.geometry(f"500x350+{x}+{y}")
            
            # Header
            header = tk.Frame(self.root, bg="#1a1a1a")
            header.pack(fill=tk.X, pady=20)
            
            title = tk.Label(
                header,
                text="⚡ JSP",
                font=("Arial", 28, "bold"),
                fg="#3b82f6",
                bg="#1a1a1a"
            )
            title.pack()
            
            subtitle = tk.Label(
                header,
                text="Automação Industrial & Solar",
                font=("Arial", 11),
                fg="#94a3b8",
                bg="#1a1a1a"
            )
            subtitle.pack()
            
            # Status
            status_frame = tk.Frame(self.root, bg="#2d3748", relief=tk.RAISED, bd=1)
            status_frame.pack(fill=tk.X, padx=20, pady=10)
            
            self.status_label = tk.Label(
                status_frame,
                text="🔄 Pronto para iniciar",
                font=("Arial", 10, "bold"),
                fg="white",
                bg="#2d3748"
            )
            self.status_label.pack(pady=10)
            
            # Progress
            self.progress = ttk.Progressbar(
                self.root,
                length=460,
                mode='indeterminate'
            )
            self.progress.pack(pady=10)
            
            # Info
            info_frame = tk.Frame(self.root, bg="#2d3748", relief=tk.RAISED, bd=1)
            info_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
            
            self.info_text = tk.Text(
                info_frame,
                height=8,
                font=("Consolas", 9),
                bg="#1a1a1a",
                fg="white",
                relief=tk.FLAT
            )
            self.info_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
            
            # Buttons
            btn_frame = tk.Frame(self.root, bg="#1a1a1a")
            btn_frame.pack(fill=tk.X, padx=20, pady=10)
            
            self.btn_start = tk.Button(
                btn_frame,
                text="🚀 Iniciar Sistema",
                font=("Arial", 11, "bold"),
                bg="#10b981",
                fg="white",
                relief=tk.FLAT,
                padx=20,
                command=self.start_system
            )
            self.btn_start.pack(side=tk.LEFT)
            
            self.btn_stop = tk.Button(
                btn_frame,
                text="🛑 Parar",
                font=("Arial", 11),
                bg="#f59e0b",
                fg="white",
                relief=tk.FLAT,
                padx=20,
                command=self.stop_system,
                state=tk.DISABLED
            )
            self.btn_stop.pack(side=tk.LEFT, padx=(10, 0))
            
            btn_exit = tk.Button(
                btn_frame,
                text="❌ Sair",
                font=("Arial", 11),
                bg="#ef4444",
                fg="white",
                relief=tk.FLAT,
                padx=20,
                command=self.root.quit
            )
            btn_exit.pack(side=tk.RIGHT)
            
            # Log inicial
            self.log("🚀 ERP JSP Professional Launcher v3.0")
            self.log("⚡ JSP Automação Industrial & Solar")
            self.log("📅 " + time.strftime("%d/%m/%Y %H:%M:%S"))
            self.log("-" * 50)
            
        def log(self, message):
            """Adiciona mensagem ao log"""
            timestamp = time.strftime("%H:%M:%S")
            self.info_text.insert(tk.END, f"[{timestamp}] {message}\n")
            self.info_text.see(tk.END)
            self.root.update()
            
        def update_status(self, message):
            """Atualiza status"""
            self.status_label.config(text=message)
            self.root.update()
            
        def start_system(self):
            """Inicia o sistema"""
            def processo():
                try:
                    self.update_status("🔍 Verificando arquivos...")
                    self.progress.start()
                    
                    if not os.path.exists('app'):
                        raise Exception("Pasta 'app' não encontrada")
                    self.log("✅ Pasta 'app' encontrada")
                    
                    if not os.path.exists('run.py'):
                        raise Exception("Arquivo 'run.py' não encontrado")
                    self.log("✅ Arquivo 'run.py' encontrado")
                    
                    self.update_status("🚀 Iniciando servidor...")
                    self.log("🚀 Iniciando Flask...")
                    
                    # Iniciar Flask
                    self.flask_process = subprocess.Popen(
                        [sys.executable, 'run.py'],
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        creationflags=0x08000000 if os.name == 'nt' else 0
                    )
                    
                    self.log("✅ Processo Flask iniciado")
                    self.update_status("⏳ Aguardando servidor...")
                    
                    # Aguardar
                    time.sleep(8)
                    
                    self.update_status("🌐 Abrindo navegador...")
                    self.log("🎯 Abrindo http://127.0.0.1:5001")
                    webbrowser.open('http://127.0.0.1:5001/auth/login')
                    
                    self.update_status("✅ Sistema rodando!")
                    self.log("🎉 Sistema iniciado com sucesso!")
                    
                    # Atualizar botões
                    self.btn_start.config(state=tk.DISABLED)
                    self.btn_stop.config(state=tk.NORMAL)
                    self.progress.stop()
                    
                except Exception as e:
                    self.log(f"❌ Erro: {e}")
                    self.update_status("❌ Falha na inicialização")
                    self.progress.stop()
                    messagebox.showerror("Erro", f"Falha: {e}")
                    
            threading.Thread(target=processo, daemon=True).start()
            
        def stop_system(self):
            """Para o sistema"""
            if self.flask_process:
                self.log("🛑 Parando servidor...")
                self.flask_process.terminate()
                self.flask_process = None
                
            self.update_status("🛑 Sistema parado")
            self.btn_start.config(state=tk.NORMAL)
            self.btn_stop.config(state=tk.DISABLED)
            self.log("✅ Sistema parado")
            
        def run(self):
            """Executa o launcher"""
            self.root.mainloop()
    
    # Executar GUI
    launcher = ERPLauncher()
    launcher.run()

if __name__ == "__main__":
    # Verificar localização
    if not os.path.exists('app') or not os.path.exists('run.py'):
        print("❌ ERRO: Este arquivo deve estar na pasta raiz do ERP JSP!")
        print("   Certifique-se de que 'app/' e 'run.py' existem.")
        input("\nPressione Enter para sair...")
        sys.exit(1)
    
    # Escolher modo
    if TKINTER_AVAILABLE:
        try:
            main_gui()
        except:
            print("⚠️ Interface gráfica falhou, usando console...")
            main_console()
    else:
        print("⚠️ Tkinter não disponível, usando console...")
        main_console()