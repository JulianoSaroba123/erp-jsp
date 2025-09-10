from flask import Blueprint, render_template
# from aplicacao.clientes.modelos import Cliente
# from aplicacao.produtos.modelos import Produto
# from aplicacao.ordem_servico.modelos import OrdemServico

painel_bp = Blueprint('painel', __name__)

@painel_bp.route('/')
def dashboard():
    return render_template('painel/painel.html')

