
from flask import render_template, request, redirect, url_for, flash, session
from . import bp_autenticacao

@bp_autenticacao.route('/login', methods=['GET', 'POST'])
def login():
    return render_template('autenticacao/login.html')
