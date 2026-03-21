#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script para forçar deploy no Render
"""

import subprocess
import sys

print("\n" + "="*60)
print("🚀 FORÇANDO DEPLOY NO RENDER")
print("="*60 + "\n")

print("📋 Opções:")
print("   1. Fazer um commit vazio para trigger deploy")
print("   2. Abrir dashboard do Render no navegador")
print("   3. Verificar status do último deploy")
print("\nEscolha: ", end="")

try:
    opcao = input().strip()
    
    if opcao == "1":
        print("\n🔧 Criando commit vazio...")
        subprocess.run(["git", "commit", "--allow-empty", "-m", "chore: Trigger Render deploy"], check=True)
        print("✅ Commit criado!")
        
        print("\n📤 Fazendo push...")
        subprocess.run(["git", "push", "origin", "main"], check=True)
        print("✅ Push realizado!")
        
        print("\n⏳ Deploy iniciado no Render!")
        print("   Aguarde 2-5 minutos e recarregue a página")
        print("   Monitore em: https://dashboard.render.com/")
        
    elif opcao == "2":
        import webbrowser
        webbrowser.open("https://dashboard.render.com/")
        print("✅ Dashboard aberto no navegador!")
        
    elif opcao == "3":
        print("\n📊 Para verificar status:")
        print("   1. Acesse: https://dashboard.render.com/")
        print("   2. Clique no seu serviço 'erp-jsp'")
        print("   3. Veja a aba 'Events' para status do deploy")
        
    else:
        print("❌ Opção inválida!")
        
except KeyboardInterrupt:
    print("\n\n❌ Cancelado pelo usuário")
    sys.exit(0)

print("\n" + "="*60 + "\n")
