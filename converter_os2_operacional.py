from app.app import app
from app.extensoes import db
from app.ordem_servico.ordem_servico_model import OrdemServico

with app.app_context():
    os = OrdemServico.query.get(2)
    if os:
        print(f"\n=== ANTES DA ALTERAÇÃO ===")
        print(f"OS #{os.id} - {os.numero}")
        print(f"  tipo_os: '{os.tipo_os}'")
        print(f"  eh_operacional: {os.eh_operacional}")
        print(f"  eh_comercial: {os.eh_comercial}")
        
        # Alterar para operacional
        os.tipo_os = 'operacional'
        db.session.commit()
        
        print(f"\n=== DEPOIS DA ALTERAÇÃO ===")
        print(f"OS #{os.id} - {os.numero}")
        print(f"  tipo_os: '{os.tipo_os}'")
        print(f"  eh_operacional: {os.eh_operacional}")
        print(f"  eh_comercial: {os.eh_comercial}")
        print("\n✅ OS #2 convertida para OPERACIONAL com sucesso!")
    else:
        print("❌ OS #2 não encontrada!")
