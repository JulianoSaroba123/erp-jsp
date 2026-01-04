"""
Script simplificado para adicionar coluna datasheet
Uso: python adicionar_datasheet_render.py <DATABASE_URL>
"""
import sys
import psycopg

def adicionar_colunas(database_url):
    """Adiciona colunas datasheet via psycopg direto"""
    print("\n" + "=" * 80)
    print("ADICIONANDO COLUNAS DATASHEET NO RENDER")
    print("=" * 80)
    
    try:
        print(f"\n📡 Conectando ao banco...")
        conn = psycopg.connect(database_url)
        cur = conn.cursor()
        
        print("✅ Conectado!")
        
        # Verificar placa_solar
        print("\n🔍 Verificando placa_solar...")
        cur.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'placa_solar' AND column_name = 'datasheet'
        """)
        
        if cur.fetchone():
            print("   ✅ Coluna datasheet já existe em placa_solar")
        else:
            print("   ➕ Adicionando coluna datasheet em placa_solar...")
            cur.execute("ALTER TABLE placa_solar ADD COLUMN datasheet VARCHAR(500)")
            conn.commit()
            print("   ✅ Coluna adicionada!")
        
        # Verificar inversor_solar
        print("\n🔍 Verificando inversor_solar...")
        cur.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'inversor_solar' AND column_name = 'datasheet'
        """)
        
        if cur.fetchone():
            print("   ✅ Coluna datasheet já existe em inversor_solar")
        else:
            print("   ➕ Adicionando coluna datasheet em inversor_solar...")
            cur.execute("ALTER TABLE inversor_solar ADD COLUMN datasheet VARCHAR(500)")
            conn.commit()
            print("   ✅ Coluna adicionada!")
        
        # Verificar resultado
        print("\n📋 Verificando estrutura final...")
        cur.execute("""
            SELECT table_name, column_name, data_type, character_maximum_length
            FROM information_schema.columns
            WHERE table_name IN ('placa_solar', 'inversor_solar')
                AND column_name = 'datasheet'
            ORDER BY table_name
        """)
        
        for row in cur.fetchall():
            print(f"   ✅ {row[0]}.{row[1]}: {row[2]}({row[3]})")
        
        cur.close()
        conn.close()
        
        print("\n✅ CONCLUÍDO COM SUCESSO!")
        print("=" * 80 + "\n")
        
    except Exception as e:
        print(f"\n❌ ERRO: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("\n❌ Uso: python adicionar_datasheet_render.py <DATABASE_URL>")
        print("\nExemplo:")
        print('python adicionar_datasheet_render.py "postgresql://user:pass@host/db"')
        print("\nOu no Render Shell:")
        print('python adicionar_datasheet_render.py "$DATABASE_URL"')
        sys.exit(1)
    
    database_url = sys.argv[1]
    adicionar_colunas(database_url)
