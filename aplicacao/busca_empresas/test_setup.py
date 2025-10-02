"""
Script auxiliar para testar a integração do módulo de busca de empresas
"""
from aplicacao import create_app
from aplicacao.extensoes import db

app = create_app()

with app.app_context():
    # Mostrar contagem de empresas salvas
    from aplicacao.busca_empresas.empresa_model import EmpresaEncontrada
    total = db.session.query(EmpresaEncontrada).count()
    print(f'Total de empresas encontradas no banco: {total}')

    # Fazer uma busca de exemplo via função utilitária
    from aplicacao.busca_empresas.busca_routes import buscar_empresas_api
    empresas = buscar_empresas_api('São Paulo', 'restaurante')
    print(f'Empresas encontradas via API (exemplo): {len(empresas)}')
