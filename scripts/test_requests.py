import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from aplicacao import create_app

app = create_app()
with app.test_client() as c:
    for path in ['/', '/painel', '/clientes/']:
        resp = c.get(path)
        print(path, resp.status_code)
        if resp.status_code == 200:
            print(resp.data[:200].decode(errors='ignore'))
