#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para encontrar exatamente onde está a chave extra
"""

import re

# Ler o arquivo
with open('app/proposta/templates/proposta/form.html', 'r', encoding='utf-8') as f:
    conteudo = f.read()

# Extrai apenas o JavaScript
script_match = re.search(r'<script>(.*?)</script>', conteudo, re.DOTALL)

if script_match:
    javascript = script_match.group(1)
    
    # Divide em linhas e analisa cada uma
    linhas = javascript.split('\n')
    nivel_chaves = 0
    
    print("🔍 Analisando nível de chaves linha por linha...")
    print("=" * 60)
    
    for i, linha in enumerate(linhas, 1):
        linha_stripped = linha.strip()
        
        # Conta chaves abertas e fechadas na linha
        abrir = linha.count('{')
        fechar = linha.count('}')
        
        nivel_chaves += abrir - fechar
        
        # Mostra linhas com chaves ou níveis problemáticos
        if abrir > 0 or fechar > 0 or nivel_chaves < 0:
            status = "❌" if nivel_chaves < 0 else "⚠️" if nivel_chaves > 10 else "✅"
            print(f"Linha {i:3d} | Nível: {nivel_chaves:2d} | {status} | {linha_stripped[:80]}")
            
            if nivel_chaves < 0:
                print(f"         ^^^^^^^^ PROBLEMA AQUI! Nível negativo: {nivel_chaves}")
                break
    
    print("=" * 60)
    print(f"🎯 Nível final de chaves: {nivel_chaves}")
    
    if nivel_chaves != 0:
        if nivel_chaves > 0:
            print(f"❌ Faltam {nivel_chaves} chaves de fechamento")
        else:
            print(f"❌ Há {abs(nivel_chaves)} chaves de fechamento extras")
    else:
        print("✅ Chaves estão balanceadas!")
        
else:
    print("❌ Nenhum script encontrado!")