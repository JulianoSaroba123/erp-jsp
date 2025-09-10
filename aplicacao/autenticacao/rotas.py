from flask import render_template, request
from . import bp_autenticacao

@bp_autenticacao.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # Processar login
        pass
    return render_template('autenticacao/login.html')

@bp_autenticacao.route('/')
def index():
    return render_template('autenticacao/login.html')
