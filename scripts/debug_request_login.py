import traceback
import os
import sys

# Ensure project root is on sys.path so 'aplicacao' package can be imported
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

try:
    from aplicacao import create_app
    app = create_app()
    with app.test_client() as c:
        # Test produtos listing
        resp = c.get('/produtos')
        print('PRODUTOS LIST STATUS:', resp.status_code)
        if resp.status_code != 200:
            print('Error:', resp.get_data(as_text=True)[:500])
        
        # Test produtos cadastro
        resp = c.get('/produtos/cadastrar')
        print('PRODUTOS CADASTRO STATUS:', resp.status_code)
        if resp.status_code != 200:
            print('Error:', resp.get_data(as_text=True)[:500])
        
        # Test fornecedor search endpoint
        resp = c.get('/produtos/fornecedor_buscar?q=test')
        print('FORNECEDOR SEARCH STATUS:', resp.status_code)
        print('FORNECEDOR SEARCH RESPONSE:', resp.get_data(as_text=True))
        
except Exception as e:
    print('EXCEPTION during app import/initialization:')
    traceback.print_exc()
