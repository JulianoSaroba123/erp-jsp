"""
Script de migração direta para adicionar colunas financeiras na tabela projeto_solar.
Conecta diretamente ao banco sem passar pelo Flask.

Adiciona as colunas:
- concessionaria_id
- tarifa_kwh
- economia_mensal
- economia_anual
- impostos_percentual
"""

import os
import sys
from sqlalchemy import create_engine, text, inspect
from dotenv import load_dotenv

# Carrega variáveis de ambiente
load_dotenv()

def coluna_existe(inspector, tabela, coluna):
    """Verifica se uma coluna existe na tabela."""
    colunas = [col['name'] for col in inspector.get_columns(tabela)]
    return coluna in colunas


def garantir_colunas():
    """Garante que todas as colunas financeiras existam na tabela projeto_solar."""
    
    # Obtém a URL do banco
    database_url = os.getenv("DATABASE_URL")
    
    if not database_url:
        # Usa SQLite local se não houver DATABASE_URL
        basedir = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
        database_url = f'sqlite:///{os.path.join(basedir, "erp.db")}'
        print(f"⚠️  DATABASE_URL não encontrada. Usando SQLite local: erp.db")
    
    # Corrige URL do PostgreSQL se necessário
    if database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://", 1)
    
    print(f"🔧 Conectando ao banco: {database_url.split('@')[0]}@...")
    
    # Cria engine
    engine = create_engine(database_url)
    inspector = inspect(engine)
    
    # Verifica se a tabela existe
    if 'projeto_solar' not in inspector.get_table_names():
        print("❌ Tabela projeto_solar não existe!")
        return
    
    tabela = "projeto_solar"
    
    # Definição das colunas a serem criadas
    colunas = {
        "concessionaria_id": "INTEGER",
        "tarifa_kwh": "NUMERIC(10,4) DEFAULT 0",
        "economia_mensal": "NUMERIC(12,2) DEFAULT 0",
        "economia_anual": "NUMERIC(12,2) DEFAULT 0",
        "impostos_percentual": "NUMERIC(8,2) DEFAULT 0",
    }
    
    print(f"🔧 Banco de dados: {engine.url.get_backend_name()}")
    print("=" * 60)
    
    with engine.begin() as conn:
        for coluna, tipo in colunas.items():
            # Verifica se a coluna já existe
            existe = coluna_existe(inspector, tabela, coluna)
            
            # Adiciona a coluna se não existir
            if not existe:
                try:
                    conn.execute(text(f"ALTER TABLE {tabela} ADD COLUMN {coluna} {tipo}"))
                    print(f"✅ Coluna criada: {coluna} ({tipo})")
                except Exception as e:
                    print(f"❌ Erro ao criar coluna {coluna}: {e}")
            else:
                print(f"✓ Coluna já existe: {coluna}")
    
    print("=" * 60)
    print("✅ Migration financeira da tabela projeto_solar concluída.")
    print("=" * 60)


if __name__ == "__main__":
    print("=" * 60)
    print("🚀 Iniciando migração da tabela projeto_solar...")
    print("=" * 60)
    try:
        garantir_colunas()
    except KeyboardInterrupt:
        print("\n⚠️ Operação cancelada pelo usuário.")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Erro durante a migração: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
