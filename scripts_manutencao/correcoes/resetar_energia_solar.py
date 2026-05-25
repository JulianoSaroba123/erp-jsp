"""
Script para RESETAR tabelas de Energia Solar
ATENÇÃO: Apaga todos os dados!
"""
import sys
import os

# Adiciona o diretório raiz ao PYTHONPATH
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app.app import create_app
from app.extensoes import db

def resetar_tabelas():
    """Apaga e recria as tabelas"""
    app = create_app()
    
    with app.app_context():
        try:
            print("🗑️  RESETANDO tabelas de Energia Solar...")
            
            # Drop tabelas antigas
            db.session.execute(db.text("DROP TABLE IF EXISTS calculo_energia_solar"))
            db.session.execute(db.text("DROP TABLE IF EXISTS placa_solar"))
            db.session.execute(db.text("DROP TABLE IF EXISTS inversor_solar"))
            db.session.commit()
            print("✅ Tabelas antigas removidas")
            
            # Agora executa o script de criação
            print("\n🔨 Criando tabelas novas...")
            import criar_tabelas_energia_solar_completo
            criar_tabelas_energia_solar_completo.criar_tabelas()
            
        except Exception as e:
            print(f"❌ Erro: {e}")
            import traceback
            traceback.print_exc()

if __name__ == '__main__':
    confirm = input("⚠️  ATENÇÃO: Isso vai APAGAR TODOS os dados de Energia Solar! Confirma? (sim/não): ")
    if confirm.lower() == 'sim':
        resetar_tabelas()
    else:
        print("❌ Cancelado!")
