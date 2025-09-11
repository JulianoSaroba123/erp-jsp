from flask import Blueprint, render_template

# Registrar o blueprint do painel sob o prefixo /painel para evitar conflito com a raiz
painel_bp = Blueprint('painel', __name__, url_prefix='/painel')


@painel_bp.route('/')
def dashboard():
    return render_template('painel/painel.html')

