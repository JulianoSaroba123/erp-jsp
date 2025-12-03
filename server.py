#!/usr/bin/env python3
"""
ERP JSP - Servidor Minimalista para Render
==========================================
"""

import os
from flask import Flask, render_template_string, request, redirect, session, flash

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'jsp-secret-2025')

# Template de Login Simples
LOGIN_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>ERP JSP - Login</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body class="bg-light d-flex align-items-center min-vh-100">
    <div class="container">
        <div class="row justify-content-center">
            <div class="col-md-6">
                <div class="card">
                    <div class="card-header text-center">
                        <h3> ERP JSP Sistema</h3>
                    </div>
                    <div class="card-body">
                        {% if error %}<div class="alert alert-danger">{{ error }}</div>{% endif %}
                        <form method="POST">
                            <div class="mb-3">
                                <label>Email:</label>
                                <input type="email" name="email" class="form-control" 
                                       value="admin@jsp.com" required>
                            </div>
                            <div class="mb-3">
                                <label>Senha:</label>
                                <input type="password" name="senha" class="form-control" 
                                       value="admin123" required>
                            </div>
                            <button type="submit" class="btn btn-primary w-100">Entrar</button>
                        </form>
                    </div>
                </div>
            </div>
        </div>
    </div>
</body>
</html>
"""

# Template do Dashboard
DASHBOARD_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>ERP JSP - Dashboard</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body>
    <nav class="navbar navbar-dark bg-dark">
        <div class="container-fluid">
            <span class="navbar-brand"> ERP JSP - Dashboard</span>
            <a href="/logout" class="btn btn-outline-light">Sair</a>
        </div>
    </nav>
    <div class="container mt-4">
        <div class="alert alert-success">
            <h4> Sistema ERP JSP Funcionando!</h4>
            <p>Deploy realizado com sucesso no Render!</p>
            <p><strong>Usuário:</strong> {{ usuario }}</p>
        </div>
        
        <div class="row">
            <div class="col-md-3">
                <div class="card bg-primary text-white">
                    <div class="card-body text-center">
                        <h5>Clientes</h5>
                        <h3>25</h3>
                    </div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="card bg-success text-white">
                    <div class="card-body text-center">
                        <h5>Propostas</h5>
                        <h3>12</h3>
                    </div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="card bg-warning text-white">
                    <div class="card-body text-center">
                        <h5>Produtos</h5>
                        <h3>89</h3>
                    </div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="card bg-info text-white">
                    <div class="card-body text-center">
                        <h5>Receita</h5>
                        <h3>R$ 15.800</h3>
                    </div>
                </div>
            </div>
        </div>
    </div>
</body>
</html>
"""

@app.route('/')
def home():
    return redirect('/login')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email', '')
        senha = request.form.get('senha', '')
        
        if email == 'admin@jsp.com' and senha == 'admin123':
            session['user'] = 'Admin JSP'
            return redirect('/dashboard')
        else:
            return render_template_string(LOGIN_HTML, error='Login inválido!')
    
    return render_template_string(LOGIN_HTML)

@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect('/login')
    
    return render_template_string(DASHBOARD_HTML, usuario=session['user'])

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')

@app.route('/health')
def health():
    return {'status': 'ok', 'service': 'ERP JSP', 'version': '3.0'}

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    print(f" ERP JSP rodando na porta {port}")
    app.run(host='0.0.0.0', port=port, debug=False)