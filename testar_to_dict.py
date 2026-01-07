import os
os.environ['DATABASE_URL'] = 'postgresql://postgres:postgres@localhost/erp_jsp_local'

from app.app import app
from app.extensoes import db
from app.energia_solar.catalogo_model import PlacaSolar
import json

with app.app_context():
    placa = PlacaSolar.query.get(1)
    
    if placa:
        resultado = placa.to_dict()
        print('=== to_dict() RETORNA ===')
        print(json.dumps(resultado, indent=2, ensure_ascii=False))
        
        print('\n=== VERIFICAR CAMPOS CRÍTICOS ===')
        print(f"comprimento presente? {'comprimento' in resultado}")
        print(f"largura presente? {'largura' in resultado}")
        print(f"espessura presente? {'espessura' in resultado}")
        print(f"preco_custo presente? {'preco_custo' in resultado}")
        
        if 'comprimento' in resultado:
            print(f"\n✅ comprimento: {resultado['comprimento']}")
        if 'largura' in resultado:
            print(f"✅ largura: {resultado['largura']}")
        if 'espessura' in resultado:
            print(f"✅ espessura: {resultado['espessura']}")
        if 'preco_custo' in resultado:
            print(f"✅ preco_custo: {resultado['preco_custo']}")
    else:
        print('❌ Placa não encontrada!')
