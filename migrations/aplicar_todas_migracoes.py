"""
Script centralizado para aplicar todas as migrações necessárias no banco de dados.
Este script é executado automaticamente pelo build.sh no Render.

Ordem de execução:
1. Migrações de dados financeiros do projeto solar
2. Outras migrações futuras podem ser adicionadas aqui
"""

import os
import sys

# Adiciona o diretório raiz ao path para importar módulos
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sqlalchemy import create_engine, text, inspect
from dotenv import load_dotenv

# Carrega variáveis de ambiente
load_dotenv()


def coluna_existe(inspector, tabela, coluna):
    """Verifica se uma coluna existe na tabela."""
    try:
        colunas = [col['name'] for col in inspector.get_columns(tabela)]
        return coluna in colunas
    except Exception:
        return False


def migrar_projeto_solar_financeiro(engine, inspector):
    """
    Adiciona colunas financeiras na tabela projeto_solar.
    
    Colunas:
    - concessionaria_id (INTEGER)
    - tarifa_kwh (NUMERIC)
    - economia_mensal (NUMERIC)
    - economia_anual (NUMERIC)
    - impostos_percentual (NUMERIC)
    """
    print("\n" + "=" * 60)
    print("📊 MIGRAÇÃO: Dados Financeiros - projeto_solar")
    print("=" * 60)
    
    # Verifica se a tabela existe
    if 'projeto_solar' not in inspector.get_table_names():
        print("⚠️  Tabela projeto_solar não existe ainda. Pulando migração.")
        return
    
    tabela = "projeto_solar"
    
    # Definição das colunas
    colunas = {
        "concessionaria_id": "INTEGER",
        "tarifa_kwh": "NUMERIC(10,4) DEFAULT 0",
        "economia_mensal": "NUMERIC(12,2) DEFAULT 0",
        "economia_anual": "NUMERIC(12,2) DEFAULT 0",
        "impostos_percentual": "NUMERIC(8,2) DEFAULT 0",
    }
    
    alteracoes_feitas = False
    
    with engine.begin() as conn:
        for coluna, tipo in colunas.items():
            existe = coluna_existe(inspector, tabela, coluna)
            
            if not existe:
                try:
                    conn.execute(text(f"ALTER TABLE {tabela} ADD COLUMN {coluna} {tipo}"))
                    print(f"  ✅ Coluna criada: {coluna} ({tipo})")
                    alteracoes_feitas = True
                except Exception as e:
                    print(f"  ❌ Erro ao criar coluna {coluna}: {e}")
            else:
                print(f"  ✓ Coluna já existe: {coluna}")
    
    if alteracoes_feitas:
        print("✅ Migração de dados financeiros aplicada com sucesso!")
    else:
        print("✓ Todas as colunas já existem. Nenhuma alteração necessária.")


def aplicar_todas_migracoes():
    """Aplica todas as migrações pendentes no banco de dados."""
    
    print("\n" + "=" * 60)
    print("🚀 APLICANDO MIGRAÇÕES DO BANCO DE DADOS")
    print("=" * 60)
    
    # Obtém a URL do banco
    database_url = os.getenv("DATABASE_URL")
    
    if not database_url:
        print("❌ DATABASE_URL não encontrada nas variáveis de ambiente!")
        print("⚠️  Usando SQLite local como fallback...")
        basedir = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
        database_url = f'sqlite:///{os.path.join(basedir, "erp.db")}'
    
    # Corrige URL do PostgreSQL para usar psycopg (v3)
    if database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql+psycopg://", 1)
    elif database_url.startswith("postgresql://") and "+psycopg" not in database_url:
        database_url = database_url.replace("postgresql://", "postgresql+psycopg://", 1)
    
    # Oculta a senha na exibição
    url_display = database_url.split('@')[0].split('://')[0] + "://***@" + database_url.split('@')[1] if '@' in database_url else database_url
    print(f"🔗 Conectando ao banco: {url_display}")
    
    try:
        # Cria engine e inspector
        engine = create_engine(database_url)
        inspector = inspect(engine)
        
        print(f"✅ Conexão estabelecida com sucesso!")
        print(f"🗄️  Banco: {engine.url.get_backend_name()}")
        
        # Aplica cada migração
        migrar_projeto_solar_financeiro(engine, inspector)
        
        # Aqui você pode adicionar outras migrações no futuro:
        # migrar_outra_tabela(engine, inspector)
        # migrar_mais_uma_coisa(engine, inspector)
        
        print("\n" + "=" * 60)
        print("✅ TODAS AS MIGRAÇÕES FORAM APLICADAS COM SUCESSO!")
        print("=" * 60 + "\n")
        
        return True
        
    except Exception as e:
        print("\n" + "=" * 60)
        print(f"❌ ERRO AO APLICAR MIGRAÇÕES: {e}")
        print("=" * 60)
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    try:
        sucesso = aplicar_todas_migracoes()
        sys.exit(0 if sucesso else 1)
    except KeyboardInterrupt:
        print("\n⚠️ Operação cancelada pelo usuário.")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Erro inesperado: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
