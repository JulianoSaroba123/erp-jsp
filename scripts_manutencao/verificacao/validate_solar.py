from app import create_app
from app.extensoes import db
from app.energia_solar.energia_solar_model import CalculoEnergiaSolar
from app.energia_solar.proposta_word_service import montar_contexto_proposta

app = create_app()
with app.app_context():
    # 1. Test Instantiation and Model Attributes
    try:
        projeto = CalculoEnergiaSolar()
        attributes = ['iluminacao_publica', 'demais_custos', 'reajuste_anual_energia']
        found_attrs = {attr: hasattr(projeto, attr) for attr in attributes}
        print(f"Model attributes: {found_attrs}")
        
        # 2. Get a real project if exists, otherwise use the temporary one
        projeto_real = CalculoEnergiaSolar.query.first()
        test_project = projeto_real if projeto_real else projeto
        
        if projeto_real:
            print(f"Using real project ID: {projeto_real.id}")
        else:
            print("Using dummy project for testing context.")
            # Set minimum required attributes for montar_contexto_proposta to not fail
            # These are based on common energy project requirements
            test_project.valor_venda = 0
            test_project.geracao_mensal = 0
            test_project.tarifa_energia = 0
            test_project.reajuste_anual_energia = 10.0
            
        # 3. Call montar_contexto_proposta
        try:
            contexto = montar_contexto_proposta(test_project)
            reajuste = contexto.get('reajuste_anual')
            acrescimo = contexto.get('acrescimo_anual_percentual')
            print(f"Context values - reajuste_anual: {reajuste}, acrescimo_anual_percentual: {acrescimo}")
        except Exception as e:
            print(f"Error in montar_contexto_proposta: {e}")
            import traceback
            traceback.print_exc()

    except Exception as e:
        print(f"General error: {e}")
