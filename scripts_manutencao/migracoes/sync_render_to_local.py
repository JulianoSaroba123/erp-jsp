"""
Script para sincronizar dados do Render (PostgreSQL) para Local (SQLite)
Uso: python sync_render_to_local.py
"""

import os
import sys
import psycopg2
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker
import sqlite3
from datetime import datetime

# Adiciona o diretório do app ao path
sys.path.insert(0, os.path.dirname(__file__))

from app.config import DATABASE_URL

def get_postgres_url():
    """Pega a URL do PostgreSQL do ambiente ou .env"""
    # Verifica se está em produção (Render)
    postgres_url = os.getenv('DATABASE_URL')
    
    if not postgres_url:
        print("❌ Variável DATABASE_URL não encontrada!")
        print("Configure no .env ou variável de ambiente")
        return None
    
    # Render usa postgresql://, mas SQLAlchemy precisa de postgresql+psycopg2://
    if postgres_url.startswith('postgres://'):
        postgres_url = postgres_url.replace('postgres://', 'postgresql+psycopg2://', 1)
    elif postgres_url.startswith('postgresql://'):
        postgres_url = postgres_url.replace('postgresql://', 'postgresql+psycopg2://', 1)
    
    return postgres_url

def backup_local_db():
    """Faz backup do banco local antes de sobrescrever"""
    local_db = 'database/database.db'
    if os.path.exists(local_db):
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_path = f'database/backup_before_sync_{timestamp}.db'
        
        import shutil
        shutil.copy2(local_db, backup_path)
        print(f"✅ Backup do banco local criado: {backup_path}")
        return backup_path
    return None

def sync_databases():
    """Sincroniza dados do PostgreSQL (Render) para SQLite (Local)"""
    
    print("\n" + "="*60)
    print("🔄 SINCRONIZAÇÃO RENDER → LOCAL")
    print("="*60 + "\n")
    
    # 1. Pega URL do PostgreSQL
    postgres_url = get_postgres_url()
    if not postgres_url:
        return
    
    print(f"📡 PostgreSQL: {postgres_url.split('@')[1] if '@' in postgres_url else 'configurado'}")
    print(f"💾 SQLite Local: database/database.db\n")
    
    # 2. Backup do banco local
    backup_path = backup_local_db()
    
    # 3. Conecta aos dois bancos
    try:
        print("🔌 Conectando ao PostgreSQL (Render)...")
        pg_engine = create_engine(postgres_url)
        pg_inspector = inspect(pg_engine)
        
        print("🔌 Conectando ao SQLite (Local)...")
        sqlite_url = 'sqlite:///database/database.db'
        sqlite_engine = create_engine(sqlite_url)
        sqlite_inspector = inspect(sqlite_engine)
        
    except Exception as e:
        print(f"❌ Erro ao conectar: {e}")
        return
    
    # 4. Lista tabelas do PostgreSQL
    tabelas_pg = pg_inspector.get_table_names()
    print(f"\n📊 Tabelas encontradas no Render: {len(tabelas_pg)}")
    
    if not tabelas_pg:
        print("⚠️ Nenhuma tabela encontrada no PostgreSQL!")
        return
    
    # 5. Copia dados tabela por tabela
    pg_conn = pg_engine.raw_connection()
    sqlite_conn = sqlite3.connect('database/database.db')
    
    total_registros = 0
    tabelas_copiadas = 0
    
    for tabela in sorted(tabelas_pg):
        try:
            # Pega dados do PostgreSQL
            pg_cursor = pg_conn.cursor()
            pg_cursor.execute(f'SELECT * FROM "{tabela}"')
            rows = pg_cursor.fetchall()
            
            if not rows:
                print(f"  ⏭️  {tabela}: 0 registros (pulando)")
                continue
            
            # Pega estrutura das colunas
            colunas = [desc[0] for desc in pg_cursor.description]
            
            # Limpa tabela local
            sqlite_cursor = sqlite_conn.cursor()
            sqlite_cursor.execute(f'DELETE FROM "{tabela}"')
            
            # Insere dados
            placeholders = ','.join(['?' for _ in colunas])
            insert_sql = f'INSERT INTO "{tabela}" ({",".join(colunas)}) VALUES ({placeholders})'
            
            for row in rows:
                # Converte tipos incompatíveis (UUID, etc)
                row_converted = []
                for val in row:
                    if val is None:
                        row_converted.append(None)
                    elif isinstance(val, (list, dict)):
                        # Converte arrays/json para string
                        import json
                        row_converted.append(json.dumps(val))
                    else:
                        row_converted.append(str(val) if not isinstance(val, (int, float, bool)) else val)
                
                sqlite_cursor.execute(insert_sql, row_converted)
            
            sqlite_conn.commit()
            
            print(f"  ✅ {tabela}: {len(rows)} registros")
            total_registros += len(rows)
            tabelas_copiadas += 1
            
        except Exception as e:
            print(f"  ❌ {tabela}: ERRO - {e}")
            continue
    
    pg_conn.close()
    sqlite_conn.close()
    
    print("\n" + "="*60)
    print(f"✅ Sincronização concluída!")
    print(f"📊 {tabelas_copiadas}/{len(tabelas_pg)} tabelas copiadas")
    print(f"📝 {total_registros} registros totais")
    if backup_path:
        print(f"💾 Backup anterior: {backup_path}")
    print("="*60 + "\n")

if __name__ == '__main__':
    try:
        sync_databases()
    except KeyboardInterrupt:
        print("\n❌ Sincronização cancelada pelo usuário")
    except Exception as e:
        print(f"\n❌ Erro fatal: {e}")
        import traceback
        traceback.print_exc()
