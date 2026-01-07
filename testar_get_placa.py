import requests
import json

# Fazer requisição para obter dados da placa
url = 'http://127.0.0.1:5001/energia-solar/placas/editar/1'

try:
    response = requests.get(url)
    print(f"Status Code: {response.status_code}")
    print("\n=== JSON RETORNADO PELA API ===")
    data = response.json()
    print(json.dumps(data, indent=2, ensure_ascii=False))
    
    print("\n=== CAMPOS ESPECÍFICOS ===")
    print(f"Comprimento: {data.get('comprimento')}")
    print(f"Largura: {data.get('largura')}")
    print(f"Espessura: {data.get('espessura')}")
    print(f"Preço Custo: {data.get('preco_custo')}")
    
except Exception as e:
    print(f"❌ Erro: {e}")
