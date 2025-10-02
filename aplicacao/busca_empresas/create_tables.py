"""
Cria tabelas faltantes no banco (útil para desenvolvimento rápido).
Uso: python aplicacao\busca_empresas\create_tables.py
"""
from aplicacao import create_app
from aplicacao.extensoes import db

app = create_app()

with app.app_context():
    # Cria todas as tabelas declaradas pelos modelos (não remove/alter)
    db.create_all()

    # Relatório simples
    from aplicacao.busca_empresas.empresa_model import EmpresaEncontrada
    try:
        total = db.session.query(EmpresaEncontrada).count()
    except Exception:
        total = 0

    print('Tabela empresas_encontradas criada/confirmada. Total de linhas:', total)
