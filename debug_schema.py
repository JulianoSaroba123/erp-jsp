import sqlite3

# Conectar ao banco de dados
conn = sqlite3.connect('database/database.db')
cursor = conn.cursor()

print("=== TABELAS NO BANCO ===")

# Listar todas as tabelas
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = cursor.fetchall()
for table in tables:
    print(f"Tabela: {table[0]}")

print("\n=== COLUNAS DA TABELA ORDEM DE SERVICO ===")

# Encontrar a tabela correta
for table in tables:
    table_name = table[0]
    if 'ordem' in table_name.lower():
        print(f"\nTabela '{table_name}':")
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = cursor.fetchall()
        for col in columns:
            print(f"  {col[1]} ({col[2]})")

conn.close()
print("\n=== FIM SCHEMA ===")