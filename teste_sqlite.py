import sqlite3
conn = sqlite3.connect('test.db')
c = conn.cursor()
c.execute('CREATE TABLE test (id INTEGER PRIMARY KEY, name TEXT)')
conn.commit()
print('Tabela criada!')
c.execute("SELECT name FROM sqlite_master WHERE type='table'")
print('Tabelas:', c.fetchall())
conn.close()
