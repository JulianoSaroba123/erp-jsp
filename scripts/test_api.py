# Run this script from the project root so Python's import system can find
# the local `aplicacao` package (i.e. run: `python scripts/test_api.py`).
from aplicacao import create_app
import json
import uuid

app = create_app()

def run():
    with app.test_client() as c:
        print('GET /clientes/api/')
        r = c.get('/clientes/api/')
        print(r.status_code)
        try:
            print(json.dumps(r.get_json(), ensure_ascii=False, indent=2))
        except Exception:
            print(r.data[:200])

        print('\nGET /clientes/api/buscar?nome=JSP')
        r = c.get('/clientes/api/buscar?nome=JSP')
        print(r.status_code)
        print(json.dumps(r.get_json(), ensure_ascii=False, indent=2))

        print('\nPOST /clientes/api/ (criar novo)')
        unique_email = f"api+{uuid.uuid4().hex[:8]}@test.local"
        # generate a pseudo-unique 11-digit cpf_cnpj for test runs
        unique_cpf = str(uuid.uuid4().int % 10**11).zfill(11)
        payload = {'nome': 'API Cliente Test', 'apelido': 'API Test', 'cpf_cnpj': unique_cpf, 'email': unique_email}
        r = c.post('/clientes/api/', json=payload)
        print(r.status_code, r.get_data(as_text=True))

        print('\nGET /clientes/api/ (após POST)')
        r = c.get('/clientes/api/')
        print(r.status_code)
        data = r.get_json() or []
        print(f'Total clientes: {len(data)}')

if __name__ == '__main__':
    run()
