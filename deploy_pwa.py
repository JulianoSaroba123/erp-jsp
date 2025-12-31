#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de Deploy Automático - ERP JSP PWA
==========================================

Facilita o processo de deploy incrementando a versão do PWA automaticamente.

Uso:
    python deploy_pwa.py [patch|minor|major]
    
    patch: v1.0.0 → v1.0.1 (correções/pequenas mudanças)
    minor: v1.0.0 → v1.1.0 (novas funcionalidades)
    major: v1.0.0 → v2.0.0 (mudanças grandes/breaking)

Sem parâmetro, faz patch (incremento padrão)
"""

import os
import re
import sys
import subprocess
from datetime import datetime

# Cores para terminal
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    END = '\033[0m'
    BOLD = '\033[1m'

def print_header(text):
    """Imprime cabeçalho."""
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*60}{Colors.END}")
    print(f"{Colors.HEADER}{Colors.BOLD}{text}{Colors.END}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'='*60}{Colors.END}\n")

def print_success(text):
    """Imprime mensagem de sucesso."""
    print(f"{Colors.GREEN}✅ {text}{Colors.END}")

def print_info(text):
    """Imprime mensagem informativa."""
    print(f"{Colors.CYAN}ℹ️  {text}{Colors.END}")

def print_warning(text):
    """Imprime aviso."""
    print(f"{Colors.YELLOW}⚠️  {text}{Colors.END}")

def print_error(text):
    """Imprime erro."""
    print(f"{Colors.RED}❌ {text}{Colors.END}")

def get_current_version():
    """Obtém a versão atual do service worker."""
    sw_path = os.path.join('app', 'static', 'service-worker.js')
    
    if not os.path.exists(sw_path):
        print_error(f"Service worker não encontrado: {sw_path}")
        return None
    
    with open(sw_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Procura por: const CACHE_NAME = 'erp-jsp-v1.0.0';
    match = re.search(r"const CACHE_NAME = 'erp-jsp-v(\d+)\.(\d+)\.(\d+)'", content)
    
    if match:
        major, minor, patch = match.groups()
        return (int(major), int(minor), int(patch))
    
    print_warning("Versão não encontrada no service worker. Usando v1.0.0")
    return (1, 0, 0)

def increment_version(current, bump_type='patch'):
    """Incrementa a versão."""
    major, minor, patch = current
    
    if bump_type == 'major':
        return (major + 1, 0, 0)
    elif bump_type == 'minor':
        return (major, minor + 1, 0)
    else:  # patch
        return (major, minor, patch + 1)

def update_service_worker(new_version):
    """Atualiza a versão no service worker."""
    sw_path = os.path.join('app', 'static', 'service-worker.js')
    
    with open(sw_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Substitui a versão
    new_version_str = f"{new_version[0]}.{new_version[1]}.{new_version[2]}"
    new_content = re.sub(
        r"const CACHE_NAME = 'erp-jsp-v\d+\.\d+\.\d+'",
        f"const CACHE_NAME = 'erp-jsp-v{new_version_str}'",
        content
    )
    
    with open(sw_path, 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    return new_version_str

def update_manifest(new_version):
    """Atualiza a versão no manifest.json (opcional)."""
    manifest_path = os.path.join('app', 'static', 'manifest.json')
    
    if not os.path.exists(manifest_path):
        return
    
    try:
        import json
        
        with open(manifest_path, 'r', encoding='utf-8') as f:
            manifest = json.load(f)
        
        # Adiciona versão ao nome (opcional)
        manifest['version'] = f"{new_version[0]}.{new_version[1]}.{new_version[2]}"
        
        with open(manifest_path, 'w', encoding='utf-8') as f:
            json.dump(manifest, f, indent=2, ensure_ascii=False)
        
        print_success(f"manifest.json atualizado")
    except Exception as e:
        print_warning(f"Não foi possível atualizar manifest.json: {e}")

def git_status():
    """Verifica status do git."""
    try:
        result = subprocess.run(
            ['git', 'status', '--porcelain'],
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError:
        print_error("Erro ao verificar status do git")
        return None

def git_commit_and_push(version_str, message=None):
    """Faz commit e push para o repositório."""
    try:
        # Add all changes
        print_info("Adicionando alterações ao git...")
        subprocess.run(['git', 'add', '.'], check=True)
        
        # Commit
        if not message:
            message = f"chore: Atualização PWA para versão {version_str}"
        
        commit_message = f"{message}\n\n- Versão do cache atualizada: v{version_str}\n- Data: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}"
        
        print_info("Fazendo commit...")
        subprocess.run(['git', 'commit', '-m', commit_message], check=True)
        
        # Push
        print_info("Enviando para o repositório...")
        subprocess.run(['git', 'push'], check=True)
        
        print_success("Commit e push realizados com sucesso!")
        return True
        
    except subprocess.CalledProcessError as e:
        print_error(f"Erro no git: {e}")
        return False

def main():
    """Função principal."""
    print_header("🚀 Deploy Automático - ERP JSP PWA")
    
    # Determina tipo de incremento
    bump_type = 'patch'
    if len(sys.argv) > 1:
        bump_type = sys.argv[1].lower()
        if bump_type not in ['patch', 'minor', 'major']:
            print_error(f"Tipo inválido: {bump_type}")
            print_info("Use: patch, minor ou major")
            sys.exit(1)
    
    # Obtém versão atual
    print_info("Obtendo versão atual...")
    current_version = get_current_version()
    
    if not current_version:
        sys.exit(1)
    
    current_str = f"{current_version[0]}.{current_version[1]}.{current_version[2]}"
    print_success(f"Versão atual: v{current_str}")
    
    # Incrementa versão
    new_version = increment_version(current_version, bump_type)
    new_version_str = f"{new_version[0]}.{new_version[1]}.{new_version[2]}"
    
    print_info(f"Incremento: {bump_type.upper()}")
    print_success(f"Nova versão: v{new_version_str}")
    
    # Confirma
    print(f"\n{Colors.YELLOW}Deseja continuar? (s/n): {Colors.END}", end='')
    resposta = input().strip().lower()
    
    if resposta != 's' and resposta != 'sim':
        print_warning("Deploy cancelado pelo usuário")
        sys.exit(0)
    
    # Atualiza arquivos
    print_info("\nAtualizando arquivos...")
    update_service_worker(new_version)
    print_success("service-worker.js atualizado")
    
    update_manifest(new_version)
    
    # Verifica git
    print_info("\nVerificando repositório git...")
    status = git_status()
    
    if status is None:
        print_error("Repositório git não configurado")
        sys.exit(1)
    
    if status:
        print_success(f"Alterações detectadas:\n{status}\n")
    else:
        print_warning("Nenhuma alteração detectada além da versão")
    
    # Pergunta pela mensagem de commit
    print(f"{Colors.CYAN}Mensagem de commit (Enter para usar padrão): {Colors.END}", end='')
    custom_message = input().strip()
    
    # Commit e push
    if git_commit_and_push(new_version_str, custom_message if custom_message else None):
        print_header("✅ DEPLOY CONCLUÍDO COM SUCESSO!")
        print_success(f"Versão v{new_version_str} enviada para o repositório")
        print_info("O Render detectará as mudanças e fará deploy automático")
        print_info("Aguarde 5-10 minutos para o deploy completar")
        print_info("\nOs usuários receberão notificação de atualização disponível")
    else:
        print_error("Falha no deploy")
        sys.exit(1)
    
    # Instruções finais
    print(f"\n{Colors.BOLD}📋 Próximos passos:{Colors.END}")
    print("1. Aguarde o deploy no Render completar")
    print("2. Acesse: https://dashboard.render.com")
    print("3. Verifique o status do deploy")
    print("4. Teste o app atualizado")
    print("\n💡 Usuários com app instalado verão:")
    print("   'Nova versão disponível! Deseja atualizar?'")

if __name__ == '__main__':
    main()
