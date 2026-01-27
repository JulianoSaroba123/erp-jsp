"""
Script para adicionar a coluna incluir_imagens_relatorio na tabela ordem_servico
se ela não existir.
"""
import os
import sys

# Adiciona o diretório raiz ao path para importar módulos
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Define variável de ambiente antes de importar
os.environ['FLASK_SKIP_DOTENV'] = '1'

from app import create_app
from app.extensoes import db
from sqlalchemy import text, inspect

def adicionar_coluna_incluir_imagens():
    """Adiciona a coluna incluir_imagens_relatorio se ela não existir."""
    app = create_app()
    with app.app_context():
        try:
            # Verifica se a coluna já existe
            inspector = inspect(db.engine)
            colunas = [col['name'] for col in inspector.get_columns('ordem_servico')]
            
            print(f"📋 Colunas existentes na tabela ordem_servico:")
            for col in colunas:
                print(f"  - {col}")
            
            if 'incluir_imagens_relatorio' in colunas:
                print(f"\n✅ A coluna 'incluir_imagens_relatorio' já existe!")
                
                # Verificar quantos registros têm a opção ativada
                result = db.session.execute(text("""
                    SELECT COUNT(*) as total,
                           SUM(CASE WHEN incluir_imagens_relatorio = TRUE THEN 1 ELSE 0 END) as com_imagens
                    FROM ordem_servico
                    WHERE ativo = TRUE
                """)).fetchone()
                
                print(f"📊 Estatísticas:")
                print(f"   Total de OS ativas: {result.total}")
                print(f"   OS com imagens ativadas: {result.com_imagens}")
                
            else:
                print(f"\n⚠️ A coluna 'incluir_imagens_relatorio' NÃO existe!")
                print(f"➕ Adicionando coluna...")
                
                # PostgreSQL
                if 'postgresql' in str(db.engine.url):
                    db.session.execute(text("""
                        ALTER TABLE ordem_servico 
                        ADD COLUMN IF NOT EXISTS incluir_imagens_relatorio BOOLEAN DEFAULT FALSE
                    """))
                # SQLite
                else:
                    db.session.execute(text("""
                        ALTER TABLE ordem_servico 
                        ADD COLUMN incluir_imagens_relatorio BOOLEAN DEFAULT 0
                    """))
                
                db.session.commit()
                print(f"✅ Coluna 'incluir_imagens_relatorio' adicionada com sucesso!")
                
                # Ativar por padrão para todas as OS existentes
                print(f"\n🔧 Ativando inclusão de imagens para todas as OS existentes...")
                db.session.execute(text("""
                    UPDATE ordem_servico 
                    SET incluir_imagens_relatorio = TRUE
                    WHERE ativo = TRUE
                """))
                db.session.commit()
                print(f"✅ Todas as OS ativas agora têm imagens ativadas!")
            
        except Exception as e:
            print(f"❌ Erro: {e}")
            import traceback
            traceback.print_exc()
            db.session.rollback()

if __name__ == '__main__':
    print("="*80)
    print("SCRIPT: Adicionar coluna incluir_imagens_relatorio")
    print("="*80)
    adicionar_coluna_incluir_imagens()
    print("="*80)
    print("✅ Script concluído!")
    print("="*80)
