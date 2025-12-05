"""Adiciona coluna logo_base64 na tabela configuracao"""
import sqlite3
import os

dbs = [
    'c:/ERP_JSP/erp.db',
    'c:/ERP_JSP/instance/erp.db'
]

for db_path in dbs:
    if not os.path.exists(db_path):
        print(f'{db_path}: Nao existe')
        continue
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.execute('PRAGMA table_info(configuracao)')
        cols = [row[1] for row in cursor.fetchall()]
        
        if not cols:
            print(f'{db_path}: Tabela configuracao nao existe')
            continue
        
        if 'logo_base64' not in cols:
            conn.execute('ALTER TABLE configuracao ADD COLUMN logo_base64 TEXT')
            conn.commit()
            print(f'{db_path}: Coluna logo_base64 adicionada!')
        else:
            print(f'{db_path}: Coluna logo_base64 ja existe')
        
        conn.close()
    except Exception as e:
        print(f'{db_path}: Erro - {e}')
