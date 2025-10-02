from aplicacao import create_app
from aplicacao.ordem_servico.ordem_servico_model import OrdemServico
from aplicacao.extensoes import db

app = create_app()

@app.route('/test-ordens')
def test_ordens():
    try:
        # Testar a query que está na rota
        ordens = OrdemServico.query.order_by(OrdemServico.data_emissao.desc()).all()
        return f"Sucesso! Encontradas {len(ordens)} ordens de serviço."
    except Exception as e:
        return f"Erro: {str(e)}"

if __name__ == '__main__':
    print("Testando rota de ordens...")
    with app.test_client() as client:
        response = client.get('/test-ordens')
        print(response.get_data(as_text=True))