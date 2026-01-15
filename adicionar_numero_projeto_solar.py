"""
Script para adicionar coluna numero_projeto na tabela calculo_energia_solar
"""
from app.app import app
from app.extensoes import db
from sqlalchemy import text

def adicionar_coluna_numero_projeto():
    """Adiciona coluna numero_projeto se não existir"""
    with app.app_context():
        try:
            # Verifica se a coluna já existe
            result = db.session.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name='calculo_energia_solar' 
                AND column_name='numero_projeto'
            """))
            
            if result.fetchone():
                print("✅ Coluna numero_projeto já existe!")
                return
            
            # Adiciona a coluna
            print("🔧 Adicionando coluna numero_projeto...")
            db.session.execute(text("""
                ALTER TABLE calculo_energia_solar 
                ADD COLUMN numero_projeto VARCHAR(50) UNIQUE
            """))
            db.session.commit()
            print("✅ Coluna numero_projeto adicionada com sucesso!")
            
        except Exception as e:
            print(f"❌ Erro ao adicionar coluna: {e}")
            db.session.rollback()
            import traceback
            traceback.print_exc()

if __name__ == '__main__':
    adicionar_coluna_numero_projeto()
