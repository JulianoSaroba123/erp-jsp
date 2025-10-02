#!/usr/bin/env python3
"""
Script para verificar duplicação no arquivo cadastro_new.html
"""

file_path = r"aplicacao\ordem_servico\templates\ordem_servico\cadastro_new.html"

with open(file_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

print(f"Total de linhas: {len(lines)}")

# Procurar por linhas que contêm "Condições de Pagamento"
pagamento_lines = []
for i, line in enumerate(lines, 1):
    if "Condições de Pagamento" in line:
        pagamento_lines.append((i, line.strip()))

print(f"Linhas com 'Condições de Pagamento': {len(pagamento_lines)}")
for line_num, content in pagamento_lines:
    print(f"Linha {line_num}: {content}")

# Verificar se há seções duplicadas - vamos olhar ao redor das linhas de pagamento
if len(pagamento_lines) > 1:
    print("\n=== ANÁLISE DE DUPLICAÇÃO ===")
    for line_num, content in pagamento_lines:
        print(f"\n--- Contexto da linha {line_num} ---")
        start = max(0, line_num - 10)
        end = min(len(lines), line_num + 10)
        for i in range(start, end):
            marker = ">>> " if i == line_num - 1 else "    "
            print(f"{marker}{i+1:3d}: {lines[i].rstrip()}")