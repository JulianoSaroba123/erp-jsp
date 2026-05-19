"""
Script para testar geração de PDF do projeto 5 localmente
"""
from app import create_app
from app.energia_solar.catalogo_model import ProjetoSolar, PlacaSolar, InversorSolar

app = create_app()

with app.app_context():
    print("=" * 60)
    print("TESTE DE GERAÇÃO DE PDF - PROJETO 5")
    print("=" * 60)
    
    # Buscar projeto
    projeto = ProjetoSolar.query.get(5)
    
    if not projeto:
        print("❌ ERRO: Projeto 5 não encontrado!")
        print("\nProjetos disponíveis:")
        projetos = ProjetoSolar.query.all()
        for p in projetos:
            print(f"  - ID {p.id}: {p.nome_cliente} ({p.potencia_kwp}kWp)")
    else:
        print(f"\n✅ Projeto encontrado: {projeto.nome_cliente}")
        print(f"   Potência: {projeto.potencia_kwp} kWp")
        print(f"   Valor: R$ {projeto.valor_venda or 0}")
        
        # Verificar campos necessários
        print("\n📊 Campos do Projeto:")
        print(f"   - placa_id: {projeto.placa_id}")
        print(f"   - inversor_id: {projeto.inversor_id}")
        print(f"   - custo_equipamentos: R$ {projeto.custo_equipamentos or 0}")
        print(f"   - custo_instalacao: R$ {projeto.custo_instalacao or 0}")
        print(f"   - custo_projeto: R$ {projeto.custo_projeto or 0}")
        print(f"   - consumo_kwh_mes: {projeto.consumo_kwh_mes or 0}")
        print(f"   - geracao_estimada_mes: {projeto.geracao_estimada_mes or 0}")
        print(f"   - tarifa_kwh: R$ {projeto.tarifa_kwh or 0}")
        
        # Verificar placa
        if projeto.placa_id:
            placa = PlacaSolar.query.get(projeto.placa_id)
            if placa:
                print(f"\n✅ Placa encontrada: {placa.fabricante} {placa.modelo} ({placa.potencia}W)")
            else:
                print(f"\n❌ Placa ID {projeto.placa_id} não encontrada no banco!")
        else:
            print("\n⚠️ Projeto sem placa associada")
        
        # Verificar inversor
        if projeto.inversor_id:
            inversor = InversorSolar.query.get(projeto.inversor_id)
            if inversor:
                print(f"✅ Inversor encontrado: {inversor.fabricante} {inversor.modelo} ({inversor.potencia_nominal}kW)")
            else:
                print(f"❌ Inversor ID {projeto.inversor_id} não encontrado no banco!")
        else:
            print("⚠️ Projeto sem inversor associado")
        
        # Testar geração do balanço energético
        print("\n🔄 Testando cálculo do balanço energético...")
        try:
            from app.energia_solar.energia_solar_routes import calcular_balanco_energetico
            balanco = calcular_balanco_energetico(projeto)
            print("✅ Balanço calculado com sucesso:")
            print(f"   - Consumo mensal: {balanco['consumo_mensal']} kWh")
            print(f"   - Geração mensal: {balanco['geracao_mensal']} kWh")
            print(f"   - Economia mensal: R$ {balanco['economia_mensal']}")
        except Exception as e:
            print(f"❌ Erro ao calcular balanço: {e}")
        
        # Testar renderização do template
        print("\n🖨️ Testando renderização do template...")
        try:
            from flask import render_template
            from app.configuracao.configuracao_utils import get_config
            from app.cliente.cliente_model import Cliente
            
            cliente = None
            if projeto.cliente_id:
                cliente = Cliente.query.get(projeto.cliente_id)
            
            placa = None
            if projeto.placa_id:
                placa = PlacaSolar.query.get(projeto.placa_id)
            
            inversor = None
            if projeto.inversor_id:
                inversor = InversorSolar.query.get(projeto.inversor_id)
            
            config = get_config()
            
            html = render_template('energia_solar/pdf_proposta_solar_v2.html',
                                 projeto=projeto,
                                 cliente=cliente,
                                 logo_url=config.logo_base64 if config else None,
                                 config=config,
                                 balanco=balanco,
                                 placa=placa,
                                 inversor=inversor)
            
            print(f"✅ Template renderizado com sucesso! ({len(html)} caracteres)")
            
        except Exception as e:
            print(f"❌ Erro ao renderizar template: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "=" * 60)
