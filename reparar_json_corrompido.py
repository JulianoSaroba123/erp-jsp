import sqlite3
import json

# Conectar ao banco de dados
conn = sqlite3.connect('database/database.db')
cursor = conn.cursor()

print("=== REPARAR DADOS JSON CORROMPIDOS ===")

# Buscar todas as ordens com dados JSON corrompidos
cursor.execute("""
    SELECT id, servicos_dados, produtos_dados, parcelas_json 
    FROM ordens_servico 
    WHERE servicos_dados LIKE '[{%' 
       OR produtos_dados LIKE '[{%'
       OR parcelas_json LIKE '[{%'
""")

orders_to_fix = cursor.fetchall()

print(f"Encontradas {len(orders_to_fix)} ordens com dados corrompidos")

for order_id, servicos_raw, produtos_raw, parcelas_raw in orders_to_fix:
    print(f"\n[ORDEM {order_id}]")
    
    # Verificar e corrigir servicos_dados
    if servicos_raw and servicos_raw.startswith('[{') and len(servicos_raw) < 10:
        print(f"  Corrigindo servicos_dados: '{servicos_raw}' -> '[]'")
        cursor.execute("UPDATE ordens_servico SET servicos_dados = '[]' WHERE id = ?", (order_id,))
    
    # Verificar e corrigir produtos_dados
    if produtos_raw and produtos_raw.startswith('[{') and len(produtos_raw) < 10:
        print(f"  Corrigindo produtos_dados: '{produtos_raw}' -> '[]'")
        cursor.execute("UPDATE ordens_servico SET produtos_dados = '[]' WHERE id = ?", (order_id,))
    
    # Verificar e corrigir parcelas_json
    if parcelas_raw and parcelas_raw.startswith('[{') and len(parcelas_raw) < 10:
        print(f"  Corrigindo parcelas_json: '{parcelas_raw}' -> '[]'")
        cursor.execute("UPDATE ordens_servico SET parcelas_json = '[]' WHERE id = ?", (order_id,))

# Salvar as mudanças
conn.commit()

print("\n=== VERIFICAR CORREÇÕES ===")

# Verificar se as correções funcionaram
cursor.execute("""
    SELECT id, servicos_dados, produtos_dados, parcelas_json 
    FROM ordens_servico 
    WHERE id IN (SELECT id FROM ordens_servico LIMIT 10)
""")

for row in cursor.fetchall():
    order_id, servicos, produtos, parcelas = row
    print(f"[ORDEM {order_id}]")
    
    # Tentar fazer parse dos JSONs
    try:
        s = json.loads(servicos) if servicos else []
        print(f"  Servicos: OK ({len(s)} itens)")
    except:
        print(f"  Servicos: ERRO - {servicos[:50]}...")
    
    try:
        p = json.loads(produtos) if produtos else []
        print(f"  Produtos: OK ({len(p)} itens)")
    except:
        print(f"  Produtos: ERRO - {produtos[:50]}...")
    
    try:
        pa = json.loads(parcelas) if parcelas else []
        print(f"  Parcelas: OK ({len(pa)} itens)")
    except:
        print(f"  Parcelas: ERRO - {parcelas[:50]}...")

conn.close()
print("\n=== REPARO CONCLUÍDO ===")