import sqlite3
conn = sqlite3.connect('erp.db')
c = conn.cursor()
c.execute('PRAGMA table_info(clientes)')
cols = c.fetchall()
print('Total colunas:', len(cols))
for col in cols:
    print(col[1])
conn.close()
