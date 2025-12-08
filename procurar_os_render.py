"""
Lista TODAS as tabelas e verifica onde estão as OS
"""
from sqlalchemy import create_engine, text, inspect
from sqlalchemy.orm import sessionmaker

RENDER_DB_URL = 'postgresql://erp_jsp_db_iw6v_user:roBPw29VFmZKdksaGXw1tv4mYULKQwnl@dpg-d4pf1s49c44c73bdsdrg-a.oregon-postgres.render.com/erp_jsp_db_iw6v'

print("🔌 Conectando ao Render...")
engine = create_engine(RENDER_DB_URL)
Session = sessionmaker(bind=engine)
session = Session()

print("=" * 80)
print("🔍 PROCURANDO AS ORDENS DE SERVIÇO")
print("=" * 80)

try:
    # 1. Lista todas as tabelas
    inspector = inspect(engine)
    all_tables = inspector.get_table_names()
    
    print(f"\n📊 TOTAL DE TABELAS: {len(all_tables)}\n")
    
    # Filtra tabelas relacionadas a OS
    os_tables = [t for t in all_tables if 'ordem' in t.lower() or 'servico' in t.lower()]
    
    print("📋 TABELAS RELACIONADAS A OS:")
    for table in os_tables:
        print(f"   - {table}")
    
    # 2. Verifica registros em cada tabela
    print("\n" + "=" * 80)
    print("📊 CONTAGEM DE REGISTROS EM CADA TABELA:")
    print("=" * 80)
    
    for table in os_tables:
        try:
            result = session.execute(text(f"SELECT COUNT(*) FROM {table}"))
            count = result.scalar()
            print(f"\n   {table}: {count} registros")
            
            if count > 0:
                # Mostra primeiros registros
                result = session.execute(text(f"SELECT * FROM {table} LIMIT 3"))
                print(f"      Primeiros registros:")
                for row in result:
                    print(f"      - {dict(row._mapping)}")
        
        except Exception as e:
            print(f"\n   {table}: ERRO - {e}")
    
    # 3. Verifica também a tabela de clientes
    print("\n" + "=" * 80)
    print("📊 VERIFICANDO CLIENTES:")
    print("=" * 80)
    
    try:
        result = session.execute(text("SELECT COUNT(*) FROM clientes"))
        count = result.scalar()
        print(f"   Total de clientes: {count}")
        
        if count > 0:
            result = session.execute(text("SELECT id, nome FROM clientes LIMIT 5"))
            print("   Primeiros clientes:")
            for row in result:
                print(f"   - ID {row[0]}: {row[1]}")
    
    except Exception as e:
        print(f"   ERRO: {e}")

finally:
    session.close()
    engine.dispose()

print("\n" + "=" * 80)
