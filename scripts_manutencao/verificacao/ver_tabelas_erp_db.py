import sqlite3

conn = sqlite3.connect('database/erp.db')
cursor = conn.cursor()

# Lista todas as tabelas
tables = cursor.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()

print("📋 TABELAS NO BANCO erp.db:")
for table in tables:
    print(f"   - {table[0]}")
    
    # Conta registros
    count = cursor.execute(f"SELECT COUNT(*) FROM {table[0]}").fetchone()[0]
    print(f"      Registros: {count}")

conn.close()
