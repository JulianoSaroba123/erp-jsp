import sqlite3

conn = sqlite3.connect('erp.db')
cursor = conn.cursor()

# Ver estrutura
cursor.execute("PRAGMA table_info(projeto_solar)")
colunas = cursor.fetchall()

print("📋 Colunas da tabela projeto_solar:")
for col in colunas:
    print(f"   {col[1]} - {col[2]}")

# Ver dados do projeto 1
cursor.execute("SELECT id, componentes_extras FROM projeto_solar WHERE id = 1")
projeto = cursor.fetchone()

if projeto:
    print(f"\n📊 Projeto ID {projeto[0]}:")
    print(f"   componentes_extras: {projeto[1][:200] if projeto[1] else 'NULL'}...")

conn.close()
