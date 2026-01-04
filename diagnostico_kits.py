"""
Diagnóstico de Kits no Wizard
"""
from app.app import create_app
from app.energia_solar.catalogo_model import KitSolar

app = create_app()
app.app_context().push()

print('=' * 70)
print('🔍 DIAGNÓSTICO DE KITS NO WIZARD')
print('=' * 70)

# 1. Verificar kits no banco
kits = KitSolar.query.filter_by(ativo=True).order_by(KitSolar.fabricante).all()
print(f'\n📦 Total de kits ativos: {len(kits)}')
print('-' * 70)

if kits:
    for i, kit in enumerate(kits, 1):
        print(f'\nKit {i}:')
        print(f'  ID: {kit.id}')
        print(f'  Fabricante: {kit.fabricante}')
        print(f'  Descrição: {kit.descricao}')
        print(f'  Potência: {kit.potencia_kwp} kWp')
        print(f'  Preço: R$ {kit.preco:.2f}')
        print(f'  Placa: {kit.placa.fabricante} {kit.placa.modelo} ({kit.qtd_placas}x)')
        print(f'  Inversor: {kit.inversor.fabricante} {kit.inversor.modelo} ({kit.qtd_inversores}x)')
        
        # Simular HTML que seria gerado
        print(f'\n  HTML que será renderizado:')
        print(f'  <option value="{kit.id}"')
        print(f'          data-potencia="{kit.potencia_kwp}"')
        print(f'          data-preco="{kit.preco}">')
        print(f'    {kit.fabricante} - {kit.potencia_kwp}kWp - R$ {kit.preco:.2f}')
        print(f'  </option>')
else:
    print('\n⚠️  NENHUM KIT ATIVO ENCONTRADO!')
    print('   Cadastre kits em: /energia-solar/kits')

print('\n' + '=' * 70)
print('✅ Diagnóstico concluído!')
print('=' * 70)
