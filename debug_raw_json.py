import sqlite3
import json

# Conectar ao banco de dados
conn = sqlite3.connect('database/database.db')
cursor = conn.cursor()

print("=== DADOS RAW ORDEM 9 ===")

# Buscar os dados raw da ordem 9
cursor.execute("""
    SELECT servicos_dados, parcelas_json 
    FROM ordens_servico 
    WHERE id = 9
""")

row = cursor.fetchone()
if row:
    servicos_raw, parcelas_raw = row
    
    print(f"[RAW SERVICOS] Tipo: {type(servicos_raw)}")
    print(f"[RAW SERVICOS] Conteúdo: {repr(servicos_raw)}")
    print(f"[RAW SERVICOS] Primeiros 100 chars: {str(servicos_raw)[:100]}")
    
    print(f"\n[RAW PARCELAS] Tipo: {type(parcelas_raw)}")
    print(f"[RAW PARCELAS] Conteúdo: {repr(parcelas_raw)}")
    print(f"[RAW PARCELAS] Primeiros 100 chars: {str(parcelas_raw)[:100]}")
    
    # Tentar identificar o problema
    if servicos_raw:
        print(f"\n[ANALISE SERVICOS]")
        print(f"  Primeiro char: '{servicos_raw[0]}' (ord: {ord(servicos_raw[0])})")
        print(f"  Segundo char: '{servicos_raw[1]}' (ord: {ord(servicos_raw[1])})")
        print(f"  Terceiro char: '{servicos_raw[2]}' (ord: {ord(servicos_raw[2])})")
    
    if parcelas_raw:
        print(f"\n[ANALISE PARCELAS]")
        print(f"  Primeiro char: '{parcelas_raw[0]}' (ord: {ord(parcelas_raw[0])})")
        print(f"  Segundo char: '{parcelas_raw[1]}' (ord: {ord(parcelas_raw[1])})")
        print(f"  Terceiro char: '{parcelas_raw[2]}' (ord: {ord(parcelas_raw[2])})")

else:
    print("Ordem 9 não encontrada!")

conn.close()
print("\n=== FIM ANALISE RAW ===")