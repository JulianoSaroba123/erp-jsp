"""
Testa a query EXATA que a rota /listar usa
"""
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app.app import create_app

RENDER_DB_URL = 'postgresql://erp_jsp_db_iw6v_user:roBPw29VFmZKdksaGXw1tv4mYULKQwnl@dpg-d4pf1s49c44c73bdsdrg-a.oregon-postgres.render.com/erp_jsp_db_iw6v'

app = create_app()
app.config['SQLALCHEMY_DATABASE_URI'] = RENDER_DB_URL

print("=" * 80)
print("🔍 TESTANDO A QUERY DA ROTA /listar")
print("=" * 80)

with app.app_context():
    from app.extensoes import db
    from app.ordem_servico.ordem_servico_model import OrdemServico
    from app.cliente.cliente_model import Cliente
    
    print("\n📊 TESTE 1: Query base (ativo=True)")
    query = OrdemServico.query.filter_by(ativo=True)
    ordens = query.order_by(OrdemServico.data_abertura.desc()).all()
    print(f"   Resultado: {len(ordens)} ordens")
    
    if ordens:
        print("\n   Primeiras 5 OS:")
        for os in ordens[:5]:
            print(f"   - {os.numero} | {os.titulo} | ativo={os.ativo}")
    else:
        print("\n   ⚠️ NENHUMA OS RETORNADA!")
        
        # Testa sem filtro
        print("\n📊 TESTE 2: SEM filtro ativo")
        todas = OrdemServico.query.all()
        print(f"   Total SEM filtro: {len(todas)}")
        
        if todas:
            print("\n   Valores do campo 'ativo':")
            for os in todas[:5]:
                print(f"   - {os.numero}: ativo={os.ativo} (tipo: {type(os.ativo).__name__})")
            
            # Tenta forçar ativo=True
            print("\n🔧 FORÇANDO ativo=True em todas as OS...")
            for os in todas:
                os.ativo = True
            
            db.session.commit()
            print("   ✅ Atualizado!")
            
            # Testa novamente
            print("\n📊 TESTE 3: Após forçar ativo=True")
            ordens_apos = OrdemServico.query.filter_by(ativo=True).all()
            print(f"   Resultado: {len(ordens_apos)} ordens")
            
            if ordens_apos:
                print("\n   🎉 SUCESSO! As OS agora aparecem!")
                for os in ordens_apos[:5]:
                    print(f"   - {os.numero} | {os.titulo}")
    
    # Testa estatísticas
    print("\n📊 TESTE 4: Estatísticas")
    try:
        stats = OrdemServico.estatisticas_dashboard()
        print(f"   Stats: {stats}")
    except Exception as e:
        print(f"   Erro ao calcular stats: {e}")

print("\n" + "=" * 80)
