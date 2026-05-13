# -*- coding: utf-8 -*-
"""
Script para listar todas as tabelas no banco SQLite
"""

import sqlite3

db_path = r"C:\ERP_JSP\database\database.db"

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Listar todas as tabelas
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
tabelas = cursor.fetchall()

print(f"📋 Total de tabelas no banco: {len(tabelas)}\n")
if len(tabelas) == 0:
    print("❌ BANCO DE DADOS VAZIO!")
    print("\n💡 Você precisa criar as tabelas executando:")
    print("   python scripts/criar_tabelas.py")
else:
    print("Tabelas encontradas:")
    for tabela in tabelas:
        cursor.execute(f"SELECT COUNT(*) FROM {tabela[0]}")
        count = cursor.fetchone()[0]
        print(f"   ✓ {tabela[0]} ({count} registros)")

conn.close()
