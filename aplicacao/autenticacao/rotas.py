
from flask import render_template, request, redirect, url_for, flash, session
from . import bp_autenticacao

@bp_autenticacao.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        usuario = request.form['username']
        senha = request.form['password']
        # ⚠️ Simulação de login fixo
        if usuario == 'admin' and senha == '1234':
            session['usuario'] = usuario
            return redirect(url_for('painel.dashboard'))
        flash('Usuário ou senha inválidos.')
    return render_template('autenticacao/login.html')
