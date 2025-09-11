from flask import render_template, request, redirect, url_for, flash, session
from . import bp_autenticacao

# Modo dev: credenciais simples (texto puro) - substitua por DB/hash em produção
USUARIOS = {
    'admin': 'jsp1234'
}


@bp_autenticacao.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        usuario = request.form.get('usuario') or request.form.get('username')
        senha = request.form.get('senha') or request.form.get('password')

        if usuario in USUARIOS and USUARIOS[usuario] == senha:
            session['usuario'] = usuario
            flash('Login realizado com sucesso.', 'success')
            return redirect(url_for('painel.dashboard'))
        else:
            flash('Usuário ou senha inválidos.', 'danger')

    return render_template('autenticacao/login.html')


@bp_autenticacao.route('/logout')
def logout():
    session.pop('usuario', None)
    flash('Você saiu da sessão.', 'info')
    return redirect(url_for('autenticacao.login'))


@bp_autenticacao.route('/')
def index():
    return redirect(url_for('autenticacao.login'))
