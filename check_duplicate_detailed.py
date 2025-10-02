#!/usr/bin/env python3
"""
Script para verificar duplicação completa no arquivo
"""

file_path = r"aplicacao\ordem_servico\templates\ordem_servico\cadastro_new.html"

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Procurar pelo padrão da seção de pagamento
payment_pattern = r'<!-- 10\) Pagamento -->'
import re

matches = list(re.finditer(payment_pattern, content))
print(f"Encontradas {len(matches)} ocorrências do comentário '<!-- 10) Pagamento -->'")

for i, match in enumerate(matches, 1):
    start_pos = match.start()
    line_num = content[:start_pos].count('\n') + 1
    print(f"Ocorrência {i}: posição {start_pos}, linha {line_num}")

# Verificar se há duplicação de blocos inteiros
lines = content.split('\n')
print(f"\nTotal de linhas: {len(lines)}")

# Verificar se a segunda metade é igual à primeira
half = len(lines) // 2
first_half = lines[:half]
second_half = lines[half:]

if first_half == second_half:
    print("ENCONTRADA DUPLICAÇÃO COMPLETA DO ARQUIVO!")
    print("A segunda metade do arquivo é idêntica à primeira metade.")
else:
    print("Não há duplicação completa do arquivo.")
    
    # Verificar duplicação parcial procurando por seções específicas
    payment_section_start = None
    payment_section_count = 0
    
    for i, line in enumerate(lines):
        if "<!-- 10) Pagamento -->" in line:
            payment_section_start = i
            payment_section_count += 1
            print(f"Seção de pagamento encontrada na linha {i+1}")
            # Mostrar contexto
            for j in range(max(0, i-2), min(len(lines), i+20)):
                marker = ">>> " if j == i else "    "
                print(f"{marker}{j+1:3d}: {lines[j]}")