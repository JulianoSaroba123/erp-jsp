#!/usr/bin/env python3
"""
Script para adicionar a coluna anexos_dados à tabela ordens_servico
"""

import sqlite3
import os

# Caminho para o banco de dados
db_path = "database/database.db"

if not os.path.exists(db_path):
    print(f"❌ Banco de dados não encontrado em: {db_path}")
    exit(1)

try:
    # Conectar ao banco
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Verificar se a coluna já existe
    cursor.execute("PRAGMA table_info(ordens_servico)")
    columns = [col[1] for col in cursor.fetchall()]
    
    if 'anexos_dados' in columns:
        print("✅ Coluna 'anexos_dados' já existe na tabela")
    else:
        # Adicionar a coluna
        cursor.execute("ALTER TABLE ordens_servico ADD COLUMN anexos_dados TEXT")
        conn.commit()
        print("✅ Coluna 'anexos_dados' adicionada com sucesso!")
    
    # Verificar novamente
    cursor.execute("PRAGMA table_info(ordens_servico)")
    columns = [col[1] for col in cursor.fetchall()]
    print(f"📋 Colunas atuais na tabela: {', '.join(columns)}")
    
    conn.close()
    print("🎉 Migração concluída com sucesso!")
    
except Exception as e:
    print(f"❌ Erro ao executar migração: {str(e)}")
    if 'conn' in locals():
        conn.close()