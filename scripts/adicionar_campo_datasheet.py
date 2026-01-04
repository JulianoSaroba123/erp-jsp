"""
Script para adicionar campo datasheet nas tabelas placa_solar e inversor_solar
"""
import sqlite3

conn = sqlite3.connect('erp.db')
cursor = conn.cursor()

print("📄 Adicionando campo datasheet...")

try:
    # Adicionar campo datasheet na tabela placa_solar
    cursor.execute("ALTER TABLE placa_solar ADD COLUMN datasheet VARCHAR(500)")
    print("✅ Campo datasheet adicionado em placa_solar")
except Exception as e:
    print(f"⚠️ Campo datasheet já existe em placa_solar ou erro: {e}")

try:
    # Adicionar campo datasheet na tabela inversor_solar
    cursor.execute("ALTER TABLE inversor_solar ADD COLUMN datasheet VARCHAR(500)")
    print("✅ Campo datasheet adicionado em inversor_solar")
except Exception as e:
    print(f"⚠️ Campo datasheet já existe em inversor_solar ou erro: {e}")

conn.commit()
conn.close()

print("\n✅ Migração concluída!")
