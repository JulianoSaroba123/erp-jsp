import sqlite3
from datetime import datetime

# Conectar ao banco
conn = sqlite3.connect('database/database.db')
cursor = conn.cursor()

print("=== ADICIONAR COLUNA DATA_CONCLUSAO ===")

try:
    # Adicionar a coluna data_conclusao
    cursor.execute("ALTER TABLE ordens_servico ADD COLUMN data_conclusao DATE")
    print("✅ Coluna data_conclusao adicionada com sucesso!")
    
    # Verificar se foi criada
    cursor.execute("PRAGMA table_info(ordens_servico)")
    columns = cursor.fetchall()
    
    for col in columns:
        if 'conclusao' in col[1].lower():
            print(f"📋 Coluna encontrada: {col[1]} ({col[2]})")
    
    # Salvar mudanças
    conn.commit()
    print("💾 Mudanças salvas no banco!")
    
except sqlite3.OperationalError as e:
    if "duplicate column name" in str(e):
        print("⚠️ Coluna data_conclusao já existe!")
    else:
        print(f"❌ Erro: {e}")

conn.close()
print("🏁 Finalizado!")