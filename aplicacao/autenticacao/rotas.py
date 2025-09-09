

from flask import render_template
from . import bp_autenticacao

@bp_autenticacao.route('/login')
def login():
    return render_template('autenticacao/login.html')

@bp_autenticacao.route('/')
def index():
    return render_template('autenticacao/login.html')
