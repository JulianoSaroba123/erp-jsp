"""
🔨 Build Script para JSP Sistema
================================

Script para criar executável .exe usando PyInstaller
Gera um executável standalone com ícone personalizado

Uso:
    python build_jsp_exe.py

Resultado:
    dist/JSP_Sistema.exe
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def create_icon():
    """Cria um ícone básico se não existir"""
    icon_path = "jsp_icon.ico"
    
    if not os.path.exists(icon_path):
        print("📦 Criando ícone padrão...")
        # Usar um ícone do Windows padrão como fallback
        system_icon = r"C:\Windows\System32\imageres.dll,1"
        return None  # PyInstaller usará ícone padrão
    
    return icon_path

def clean_build_dirs():
    """Remove diretórios de build anteriores"""
    dirs_to_clean = ['build', 'dist', '__pycache__']
    
    for dir_name in dirs_to_clean:
        if os.path.exists(dir_name):
            print(f"🧹 Limpando {dir_name}/")
            shutil.rmtree(dir_name)

def get_hidden_imports():
    """Retorna lista de imports que PyInstaller pode não detectar"""
    return [
        'flask',
        'werkzeug',
        'jinja2',
        'sqlalchemy',
        'wtforms',
        'email_validator',
        'webbrowser',
        'threading',
        'subprocess'
    ]

def get_data_files():
    """Retorna lista de arquivos de dados a incluir"""
    data_files = []
    
    # Incluir templates e static
    if os.path.exists('app'):
        data_files.append(('app', 'app'))
    
    # Incluir arquivos de configuração
    config_files = ['.env.example', 'requirements.txt']
    for file in config_files:
        if os.path.exists(file):
            data_files.append((file, '.'))
    
    return data_files

def build_executable():
    """Constrói o executável usando PyInstaller"""
    print("🚀 INICIANDO BUILD DO EXECUTÁVEL JSP SISTEMA")
    print("=" * 50)
    
    # Verificar se PyInstaller está instalado
    try:
        import PyInstaller
        print("✅ PyInstaller encontrado")
    except ImportError:
        print("❌ PyInstaller não encontrado. Instalando...")
        subprocess.run([sys.executable, '-m', 'pip', 'install', 'pyinstaller'])
    
    # Limpar builds anteriores
    clean_build_dirs()
    
    # Configurações do build
    script_name = 'jsp_launcher.py'
    exe_name = 'JSP_Sistema'
    icon_path = create_icon()
    
    # Construir comando PyInstaller
    cmd = [
        sys.executable, '-m', 'PyInstaller',
        '--onefile',                    # Arquivo único
        '--windowed',                   # Sem console (GUI)
        '--clean',                      # Limpar cache
        f'--name={exe_name}',          # Nome do executável
        '--add-data', 'app;app',       # Incluir pasta app
    ]
    
    # Adicionar ícone se disponível
    if icon_path:
        cmd.extend(['--icon', icon_path])
    
    # Adicionar imports ocultos
    hidden_imports = get_hidden_imports()
    for imp in hidden_imports:
        cmd.extend(['--hidden-import', imp])
    
    # Adicionar script principal
    cmd.append(script_name)
    
    print("🔨 Construindo executável...")
    print(f"📋 Comando: {' '.join(cmd)}")
    
    try:
        # Executar PyInstaller
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Build concluído com sucesso!")
            
            # Verificar se executável foi criado
            exe_path = f"dist/{exe_name}.exe"
            if os.path.exists(exe_path):
                size = os.path.getsize(exe_path) / (1024 * 1024)  # MB
                print(f"📦 Executável criado: {exe_path}")
                print(f"📏 Tamanho: {size:.1f} MB")
                
                # Criar atalho na área de trabalho
                create_desktop_shortcut(exe_path, exe_name)
                
                return True
            else:
                print("❌ Executável não foi criado")
                return False
        else:
            print("❌ Erro no build:")
            print(result.stderr)
            return False
            
    except Exception as e:
        print(f"❌ Erro durante build: {e}")
        return False

def create_desktop_shortcut(exe_path, exe_name):
    """Cria atalho na área de trabalho"""
    try:
        import winshell
        from win32com.client import Dispatch
        
        desktop = winshell.desktop()
        shortcut_path = os.path.join(desktop, f"{exe_name}.lnk")
        
        shell = Dispatch('WScript.Shell')
        shortcut = shell.CreateShortCut(shortcut_path)
        shortcut.Targetpath = os.path.abspath(exe_path)
        shortcut.WorkingDirectory = os.path.dirname(os.path.abspath(exe_path))
        shortcut.IconLocation = os.path.abspath(exe_path)
        shortcut.save()
        
        print(f"🔗 Atalho criado na área de trabalho: {exe_name}.lnk")
        
    except ImportError:
        print("⚠️  Para criar atalho, instale: pip install pywin32 winshell")
    except Exception as e:
        print(f"⚠️  Erro ao criar atalho: {e}")

def install_dependencies():
    """Instala dependências necessárias para o build"""
    dependencies = [
        'pyinstaller',
        'pywin32',
        'winshell'
    ]
    
    print("📦 Verificando dependências de build...")
    
    for dep in dependencies:
        try:
            __import__(dep.replace('-', '_'))
            print(f"✅ {dep} já instalado")
        except ImportError:
            print(f"📥 Instalando {dep}...")
            subprocess.run([sys.executable, '-m', 'pip', 'install', dep])

def main():
    """Função principal"""
    print("🏢 JSP SISTEMA - GERADOR DE EXECUTÁVEL")
    print("=" * 50)
    
    # Verificar se estamos no diretório correto
    if not os.path.exists('jsp_launcher.py'):
        print("❌ jsp_launcher.py não encontrado!")
        print("Execute este script no diretório raiz do projeto")
        return
    
    # Instalar dependências
    install_dependencies()
    
    # Construir executável
    if build_executable():
        print("\n🎉 SUCESSO! Executável criado com sucesso!")
        print("📍 Localização: dist/JSP_Sistema.exe")
        print("🖱️  Procure pelo atalho na área de trabalho")
        print("\n💡 Para usar:")
        print("   1. Clique duas vezes no JSP_Sistema.exe")
        print("   2. Aguarde o servidor iniciar")
        print("   3. O navegador abrirá automaticamente")
    else:
        print("\n❌ Falha no build. Verifique os erros acima.")

if __name__ == '__main__':
    main()