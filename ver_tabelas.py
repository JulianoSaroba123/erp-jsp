import sqlite3
conn = sqlite3.connect('erp.db')
c = conn.cursor()
c.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = c.fetchall()
print(f"Total de tabelas: {len(tables)}")
for t in tables:
    print(f"  - {t[0]}")
conn.close()
