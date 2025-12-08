"""
Verifica o campo 'ativo' das OS no Render
"""
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app.app import create_app

RENDER_DB_URL = 'postgresql://erp_jsp_db_iw6v_user:roBPw29VFmZKdksaGXw1tv4mYULKQwnl@dpg-d4pf1s49c44c73bdsdrg-a.oregon-postgres.render.com/erp_jsp_db_iw6v'

app = create_app()
app.config['SQLALCHEMY_DATABASE_URI'] = RENDER_DB_URL

with app.app_context():
    from app.extensoes import db
    from app.ordem_servico.ordem_servico_model import OrdemServico
    
    print("=" * 80)
    print("🔍 VERIFICAÇÃO DO CAMPO 'ATIVO' NAS OS")
    print("=" * 80)
    
    # Busca TODAS as OS (sem filtro)
    todas_os = OrdemServico.query.all()
    print(f"\n📊 Total de OS no banco (SEM filtro): {len(todas_os)}")
    
    # Busca apenas ativas
    os_ativas = OrdemServico.query.filter_by(ativo=True).all()
    print(f"✅ Total de OS ATIVAS (ativo=True): {len(os_ativas)}")
    
    # Mostra status de cada OS
    print("\n📋 STATUS DE CADA OS:")
    for os in todas_os:
        ativo_str = "✅ ATIVO" if os.ativo else "❌ INATIVO"
        print(f"   {os.numero} | {os.titulo[:30]:<30} | {ativo_str}")
    
    # Se houver OS inativas, ativa todas
    if len(todas_os) > len(os_ativas):
        print(f"\n⚠️ Encontradas {len(todas_os) - len(os_ativas)} OS INATIVAS!")
        print("🔧 Ativando todas as OS...")
        
        for os in todas_os:
            if not os.ativo:
                os.ativo = True
                print(f"   ✅ Ativada: {os.numero}")
        
        db.session.commit()
        print("\n✅ Todas as OS foram ativadas com sucesso!")
        
        # Verifica novamente
        os_ativas_agora = OrdemServico.query.filter_by(ativo=True).all()
        print(f"\n📊 Total de OS ATIVAS agora: {len(os_ativas_agora)}")
    
    print("\n" + "=" * 80)
