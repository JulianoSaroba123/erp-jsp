import sqlite3

conn = sqlite3.connect('erp.db')
cursor = conn.cursor()

print("📄 Adicionando campo datasheet...")

try:
    cursor.execute("ALTER TABLE placa_solar ADD COLUMN datasheet VARCHAR(500)")
    print("✅ Campo datasheet adicionado em placa_solar")
except Exception as e:
    print(f"⚠️ placa_solar: {e}")

try:
    cursor.execute("ALTER TABLE inversor_solar ADD COLUMN datasheet VARCHAR(500)")
    print("✅ Campo datasheet adicionado em inversor_solar")
except Exception as e:
    print(f"⚠️ inversor_solar: {e}")

conn.commit()
conn.close()
print("✅ Migração concluída!")
