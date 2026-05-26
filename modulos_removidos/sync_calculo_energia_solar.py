"""
Script para sincronizar tabela calculo_energia_solar com o modelo
"""
from app.app import app
from app.extensoes import db
from sqlalchemy import text

def sync_calculo_energia_solar():
    """Sincroniza tabela calculo_energia_solar com o modelo atual"""
    with app.app_context():
        try:
            print("🔍 Verificando estrutura da tabela calculo_energia_solar...")
            
            # Lista de colunas que devem existir (baseado no modelo)
            colunas_necessarias = {
                'numero_projeto': 'VARCHAR(50) UNIQUE',
                'vida_util_sistema': 'INTEGER DEFAULT 25',
            }
            
            # Verifica quais colunas existem
            result = db.session.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name='calculo_energia_solar'
            """))
            
            colunas_existentes = [row[0] for row in result.fetchall()]
            print(f"✅ Colunas existentes: {len(colunas_existentes)}")
            
            # Adiciona colunas faltantes
            alteracoes = 0
            for coluna, tipo in colunas_necessarias.items():
                if coluna not in colunas_existentes:
                    print(f"🔧 Adicionando coluna: {coluna}")
                    try:
                        db.session.execute(text(f"""
                            ALTER TABLE calculo_energia_solar 
                            ADD COLUMN {coluna} {tipo}
                        """))
                        alteracoes += 1
                    except Exception as e:
                        print(f"⚠️ Erro ao adicionar {coluna}: {e}")
                else:
                    print(f"✓ Coluna {coluna} já existe")
            
            if alteracoes > 0:
                db.session.commit()
                print(f"✅ {alteracoes} coluna(s) adicionada(s) com sucesso!")
            else:
                print("✅ Tabela já está sincronizada!")
                
        except Exception as e:
            print(f"❌ Erro ao sincronizar tabela: {e}")
            db.session.rollback()
            import traceback
            traceback.print_exc()

if __name__ == '__main__':
    sync_calculo_energia_solar()
