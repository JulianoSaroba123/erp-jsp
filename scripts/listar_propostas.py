"""
Verificar propostas no banco local.
"""
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
os.environ['FLASK_SKIP_DOTENV'] = '1'

from app import create_app
from app.proposta.proposta_model import Proposta, ParcelaProposta

def listar_propostas():
    app = create_app()
    with app.app_context():
        propostas = Proposta.query.all()
        print(f"\n📋 PROPOSTAS NO BANCO:")
        print("="*80)
        
        if not propostas:
            print("❌ Nenhuma proposta encontrada!")
            return
        
        for p in propostas:
            parcelas = ParcelaProposta.query.filter_by(proposta_id=p.id, ativo=True).count()
            print(f"\n🆔 ID: {p.id}")
            print(f"📄 Código: {p.codigo}")
            print(f"💰 Valor: R$ {p.valor_total}")
            print(f"💳 Forma: {p.forma_pagamento}")
            if p.forma_pagamento == 'parcelado':
                print(f"📊 Parcelas: {p.numero_parcelas}")
                print(f"🏦 Entrada: {p.entrada_percentual}%")
                print(f"📅 Intervalo: {p.intervalo_parcelas} dias")
                print(f"💾 Parcelas no BD: {parcelas}")
            print("-"*80)

if __name__ == "__main__":
    listar_propostas()
