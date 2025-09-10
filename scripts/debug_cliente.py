"""Simple scripts to inspect Cliente entries for manual testing.
Usage: python scripts/debug_cliente.py list | delete_all
"""
import sys
import os
BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, BASE)

from aplicacao import create_app
from aplicacao.extensoes import db
from aplicacao.cliente.cliente_model import Cliente

app = create_app()

def listar():
    with app.app_context():
        for c in Cliente.query.all():
            print(c.id, c.nome, getattr(c, 'apelido', None))

def delete_all():
    with app.app_context():
        Cliente.query.delete()
        db.session.commit()
        print('Deleted all clientes')

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('Usage: python scripts/debug_cliente.py list|delete_all')
        sys.exit(1)
    cmd = sys.argv[1]
    if cmd == 'list':
        listar()
    elif cmd == 'delete_all':
        delete_all()
    else:
        print('Unknown command')
