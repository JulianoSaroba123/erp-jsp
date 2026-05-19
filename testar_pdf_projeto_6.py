from app import create_app
from app.energia_solar.catalogo_model import ProjetoSolar, PlacaSolar, InversorSolar, KitSolar
from app.cliente.cliente_model import Cliente
from app.configuracao.configuracao_utils import get_config
from app.energia_solar.energia_solar_routes import calcular_balanco_energetico
from flask import render_template

app = create_app()

print("=" * 60)
print("TESTE DE GERAÇÃO DE PDF - PROJETO 6")
print("=" * 60)

with app.app_context():
    projeto = ProjetoSolar.query.get(6)
    
    if not projeto:
        print("❌ Projeto 6 não encontrado")
        exit(1)
    
    print(f"✅ Projeto encontrado: {projeto.nome_cliente}")
    print(f"   Potência: {projeto.potencia_kwp} kWp")
    print(f"   kit_id: {projeto.kit_id}")
    print(f"   placa_id: {projeto.placa_id}")
    print(f"   inversor_id: {projeto.inversor_id}")
    
    # Carregar cliente
    cliente = None
    if projeto.cliente_id:
        cliente = Cliente.query.get(projeto.cliente_id)
        print(f"✅ Cliente: {cliente.nome if cliente else 'N/A'}")
    
    # Carregar kit
    kit = None
    if projeto.kit_id:
        kit = KitSolar.query.get(projeto.kit_id)
        if kit:
            print(f"✅ Kit: {kit.descricao}")
            print(f"   outras_informacoes: {repr(kit.outras_informacoes)}")
            print(f"   tipo: {type(kit.outras_informacoes)}")
        else:
            print("⚠️ Kit não encontrado no banco")
    else:
        print("⚠️ Projeto sem kit_id")
    
    # Carregar placa
    placa = None
    if projeto.placa_id:
        placa = PlacaSolar.query.get(projeto.placa_id)
        print(f"✅ Placa: {placa.modelo if placa else 'N/A'}")
    else:
        print("⚠️ Projeto sem placa_id")
    
    # Carregar inversor
    inversor = None
    if projeto.inversor_id:
        inversor = InversorSolar.query.get(projeto.inversor_id)
        print(f"✅ Inversor: {inversor.modelo if inversor else 'N/A'}")
    
    # Config
    config = get_config()
    
    # Balanço
    balanco = calcular_balanco_energetico(projeto)
    
    print("\n🖨️ Testando renderização do template...")
    try:
        html = render_template('energia_solar/pdf_proposta_solar_v2.html',
                             projeto=projeto,
                             cliente=cliente,
                             logo_url=config.logo_base64 if config else None,
                             config=config,
                             balanco=balanco,
                             placa=placa,
                             inversor=inversor,
                             kit=kit)
        
        print(f"✅ Template renderizado com sucesso! ({len(html)} caracteres)")
        
    except Exception as e:
        print(f"❌ Erro ao renderizar template: {e}")
        import traceback
        traceback.print_exc()

print("=" * 60)
