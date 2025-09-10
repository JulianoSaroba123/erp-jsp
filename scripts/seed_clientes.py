"""Seed script to insert example clients for manual testing.
Usage: python scripts/seed_clientes.py
"""
import sys
import os
BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, BASE)

from aplicacao import create_app
from aplicacao.extensoes import db
from aplicacao.cliente.cliente_model import Cliente

app = create_app()

def seed():
    with app.app_context():
        samples = [
            {'nome': 'Ricardo Cury', 'apelido': 'Cury', 'cpf_cnpj': '12345678900', 'email': 'ricardo@example.com'},
            {'nome': 'Lavanderia Clean', 'apelido': 'Clean', 'cpf_cnpj': '98765432100', 'email': 'contato@clean.com'},
            {'nome': 'Usina Solar JSP', 'apelido': 'JSP Solar', 'cpf_cnpj': '11223344556', 'email': 'vendas@jspsolar.com'},
        ]

        created = []
        for s in samples:
            # avoid duplicates by cpf_cnpj
            existing = Cliente.query.filter_by(cpf_cnpj=''.join(filter(str.isdigit, s['cpf_cnpj']))).first()
            if existing:
                created.append(existing)
                continue

            c = Cliente()
            c.codigo = None
            c.nome = s['nome']
            c.apelido = s['apelido']
            c.cpf_cnpj = ''.join(filter(str.isdigit, s['cpf_cnpj']))
            c.email = s.get('email')
            c.telefone = s.get('telefone')
            c.pais = 'Brasil'
            c.ativo = True
            # minimal required fields
            db.session.add(c)
            db.session.flush()
            # generate codigo if not present
            if not c.codigo:
                c.codigo = f"CLI{c.id:05d}"
            created.append(c)

        db.session.commit()
        for c in created:
            print(f'ID: {c.id} | Nome: {c.nome} | Apelido: {c.apelido} | Documento: {c.cpf_cnpj}')

if __name__ == '__main__':
    seed()
