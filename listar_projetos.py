"""
Listar todos os projetos solares no banco
"""
from app import create_app
from app.energia_solar.energia_solar_model import CalculoEnergiaSolar

app = create_app()

with app.app_context():
    projetos = CalculoEnergiaSolar.query.order_by(CalculoEnergiaSolar.id).all()
    
    if not projetos:
        print('❌ NENHUM PROJETO NO BANCO!')
        exit(1)
    
    print('=' * 60)
    print(f'📊 PROJETOS NO BANCO ({len(projetos)} encontrados):')
    print('=' * 60)
    
    for p in projetos:
        print(f'\n🔹 PROJETO ID: {p.id}')
        print(f'   Cliente: {p.nome_cliente}')
        print(f'   Potência: {p.potencia_kwp} kWp')
        
        # Kit
        if p.kit:
            print(f'   ✅ KIT: {p.kit.nome} - R$ {p.kit.valor_venda or 0:.2f}')
        else:
            print(f'   ❌ SEM KIT')
        
        # Placa
        if p.placa and p.qtd_placas:
            print(f'   ✅ PLACAS: {p.qtd_placas}x {p.placa.modelo} - R$ {(p.placa.valor_venda or 0) * p.qtd_placas:.2f}')
        else:
            print(f'   ❌ SEM PLACAS')
        
        # Inversor
        if p.inversor and p.qtd_inversores:
            print(f'   ✅ INVERSORES: {p.qtd_inversores}x {p.inversor.modelo} - R$ {(p.inversor.valor_venda or 0) * p.qtd_inversores:.2f}')
        else:
            print(f'   ❌ SEM INVERSORES')
    
    print('\n' + '=' * 60)
    print('🎯 USE O ID CORRETO NO NAVEGADOR!')
    print('=' * 60)
