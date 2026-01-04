"""
Adiciona coluna datasheet nas tabelas placa_solar e inversor_solar
"""
import os
from app.app import create_app
from app.extensoes import db

def adicionar_colunas_datasheet():
    """Adiciona colunas datasheet que estão faltando"""
    print("\n" + "=" * 80)
    print("ADICIONANDO COLUNAS DATASHEET")
    print("=" * 80)
    
    app = create_app()
    
    with app.app_context():
        try:
            # Verificar se usando PostgreSQL (Render) ou SQLite (local)
            engine = db.engine
            dialect = engine.dialect.name
            
            print(f"\n📊 Banco de dados: {dialect}")
            print(f"   URL: {engine.url}")
            
            # SQL para adicionar colunas
            sqls = []
            
            # Verificar se coluna existe em placa_solar
            try:
                result = db.session.execute(db.text("SELECT datasheet FROM placa_solar LIMIT 1"))
                print("\n✅ Coluna 'datasheet' já existe em placa_solar")
            except Exception:
                print("\n➕ Adicionando coluna 'datasheet' em placa_solar...")
                if dialect == 'postgresql':
                    sqls.append("ALTER TABLE placa_solar ADD COLUMN IF NOT EXISTS datasheet VARCHAR(500)")
                else:
                    sqls.append("ALTER TABLE placa_solar ADD COLUMN datasheet VARCHAR(500)")
            
            # Verificar se coluna existe em inversor_solar
            try:
                result = db.session.execute(db.text("SELECT datasheet FROM inversor_solar LIMIT 1"))
                print("✅ Coluna 'datasheet' já existe em inversor_solar")
            except Exception:
                print("➕ Adicionando coluna 'datasheet' em inversor_solar...")
                if dialect == 'postgresql':
                    sqls.append("ALTER TABLE inversor_solar ADD COLUMN IF NOT EXISTS datasheet VARCHAR(500)")
                else:
                    sqls.append("ALTER TABLE inversor_solar ADD COLUMN datasheet VARCHAR(500)")
            
            # Executar SQLs
            if sqls:
                print(f"\n🔧 Executando {len(sqls)} comando(s) SQL...")
                for sql in sqls:
                    print(f"   SQL: {sql}")
                    db.session.execute(db.text(sql))
                
                db.session.commit()
                print("\n✅ Colunas adicionadas com sucesso!")
            else:
                print("\n✅ Todas as colunas já existem! Nada a fazer.")
            
            # Verificar resultado
            print("\n📋 Verificando estrutura final...")
            
            # PlacaSolar
            if dialect == 'postgresql':
                result = db.session.execute(db.text(
                    "SELECT column_name, data_type FROM information_schema.columns "
                    "WHERE table_name = 'placa_solar' AND column_name = 'datasheet'"
                ))
                row = result.fetchone()
                if row:
                    print(f"   ✅ placa_solar.datasheet: {row[1]}")
                else:
                    print(f"   ❌ placa_solar.datasheet: NÃO ENCONTRADA")
                
                # InversorSolar
                result = db.session.execute(db.text(
                    "SELECT column_name, data_type FROM information_schema.columns "
                    "WHERE table_name = 'inversor_solar' AND column_name = 'datasheet'"
                ))
                row = result.fetchone()
                if row:
                    print(f"   ✅ inversor_solar.datasheet: {row[1]}")
                else:
                    print(f"   ❌ inversor_solar.datasheet: NÃO ENCONTRADA")
            else:
                # SQLite
                result = db.session.execute(db.text("PRAGMA table_info(placa_solar)"))
                colunas = [row[1] for row in result]
                if 'datasheet' in colunas:
                    print(f"   ✅ placa_solar.datasheet existe")
                else:
                    print(f"   ❌ placa_solar.datasheet NÃO existe")
                
                result = db.session.execute(db.text("PRAGMA table_info(inversor_solar)"))
                colunas = [row[1] for row in result]
                if 'datasheet' in colunas:
                    print(f"   ✅ inversor_solar.datasheet existe")
                else:
                    print(f"   ❌ inversor_solar.datasheet NÃO existe")
            
        except Exception as e:
            db.session.rollback()
            print(f"\n❌ ERRO: {str(e)}")
            import traceback
            traceback.print_exc()
        
        print("\n" + "=" * 80)
        print()


if __name__ == '__main__':
    adicionar_colunas_datasheet()
