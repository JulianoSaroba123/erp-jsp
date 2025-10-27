#!/usr/bin/env python3
"""
ERP JSP - FORCED UPDATE - TIMESTAMP: 2025-10-26-14:30
=======================================
SISTEMA FORÇADO PARA QUEBRAR CACHE DO RENDER
"""

import os
from flask import Flask, render_template_string, request, redirect, session, flash

# FORÇAR NOVA VERSÃO
VERSION = "3.0.1-FORCE-UPDATE-20251026"
TIMESTAMP = "2025-10-26-14:30:00"

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'jsp-secret-key-2025-FORCED')

# Templates inline para garantir funcionamento
LOGIN_TEMPLATE = """
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ERP JSP - Login</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); }
        .login-card { box-shadow: 0 10px 25px rgba(0,0,0,0.3); }
    </style>
</head>
<body class="d-flex align-items-center justify-content-center min-vh-100">
    <div class="container">
        <div class="row justify-content-center">
            <div class="col-md-6 col-lg-5">
                <div class="card login-card">
                    <div class="card-header bg-primary text-white text-center">
                        <h2>🚀 ERP JSP Sistema</h2>
                        <p class="mb-0">Faça login para acessar</p>
                    </div>
                    <div class="card-body p-4">
                        {% if error %}
                        <div class="alert alert-danger">{{ error }}</div>
                        {% endif %}
                        
                        <form method="POST">
                            <div class="mb-3">
                                <label class="form-label">Email:</label>
                                <input type="email" name="email" class="form-control" required 
                                       placeholder="admin@jsp.com" value="{{ email or '' }}">
                            </div>
                            <div class="mb-3">
                                <label class="form-label">Senha:</label>
                                <input type="password" name="senha" class="form-control" required 
                                       placeholder="admin123">
                            </div>
                            <button type="submit" class="btn btn-primary w-100">
                                🔐 Entrar no Sistema
                            </button>
                        </form>
                        
                        <div class="mt-3 text-center">
                            <small class="text-muted">
                                <strong>Login padrão:</strong><br>
                                Email: admin@jsp.com<br>
                                Senha: admin123
                            </small>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
</body>
</html>
"""

DASHBOARD_TEMPLATE = """
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ERP JSP - Dashboard</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <style>
        body { background-color: #f8f9fa; }
        .sidebar { min-height: 100vh; background: linear-gradient(180deg, #2c3e50 0%, #34495e 100%); }
        .nav-link { color: #ecf0f1 !important; }
        .nav-link:hover { background-color: rgba(255,255,255,0.1); }
        .card { box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
    </style>
</head>
<body>
    <div class="container-fluid">
        <div class="row">
            <!-- Sidebar -->
            <div class="col-md-3 col-lg-2 sidebar p-0">
                <div class="d-flex flex-column">
                    <div class="p-3 text-center border-bottom">
                        <h4 class="text-white">🚀 ERP JSP</h4>
                        <small class="text-muted">v3.0 Produção</small>
                    </div>
                    <nav class="nav flex-column p-3">
                        <a class="nav-link active" href="/dashboard">
                            <i class="fas fa-tachometer-alt me-2"></i> Dashboard
                        </a>
                        <a class="nav-link" href="/clientes">
                            <i class="fas fa-users me-2"></i> Clientes
                        </a>
                        <a class="nav-link" href="/fornecedores">
                            <i class="fas fa-truck me-2"></i> Fornecedores
                        </a>
                        <a class="nav-link" href="/produtos">
                            <i class="fas fa-box me-2"></i> Produtos
                        </a>
                        <a class="nav-link" href="/propostas">
                            <i class="fas fa-file-invoice me-2"></i> Propostas
                        </a>
                        <a class="nav-link" href="/financeiro">
                            <i class="fas fa-dollar-sign me-2"></i> Financeiro
                        </a>
                        <hr class="text-white">
                        <a class="nav-link" href="/logout">
                            <i class="fas fa-sign-out-alt me-2"></i> Sair
                        </a>
                    </nav>
                </div>
            </div>
            
            <!-- Content -->
            <div class="col-md-9 col-lg-10">
                <div class="p-4">
                    <div class="d-flex justify-content-between align-items-center mb-4">
                        <h1>📊 Dashboard</h1>
                        <div>
                            <span class="badge bg-success">Online</span>
                            <span class="text-muted">Bem-vindo, {{ usuario }}!</span>
                        </div>
                    </div>
                    
                    <div class="row">
                        <div class="col-md-3 mb-3">
                            <div class="card bg-primary text-white">
                                <div class="card-body">
                                    <div class="d-flex justify-content-between">
                                        <div>
                                            <h6>Clientes</h6>
                                            <h3>{{ stats.clientes }}</h3>
                                        </div>
                                        <i class="fas fa-users fa-2x"></i>
                                    </div>
                                </div>
                            </div>
                        </div>
                        <div class="col-md-3 mb-3">
                            <div class="card bg-success text-white">
                                <div class="card-body">
                                    <div class="d-flex justify-content-between">
                                        <div>
                                            <h6>Propostas</h6>
                                            <h3>{{ stats.propostas }}</h3>
                                        </div>
                                        <i class="fas fa-file-invoice fa-2x"></i>
                                    </div>
                                </div>
                            </div>
                        </div>
                        <div class="col-md-3 mb-3">
                            <div class="card bg-warning text-white">
                                <div class="card-body">
                                    <div class="d-flex justify-content-between">
                                        <div>
                                            <h6>Produtos</h6>
                                            <h3>{{ stats.produtos }}</h3>
                                        </div>
                                        <i class="fas fa-box fa-2x"></i>
                                    </div>
                                </div>
                            </div>
                        </div>
                        <div class="col-md-3 mb-3">
                            <div class="card bg-info text-white">
                                <div class="card-body">
                                    <div class="d-flex justify-content-between">
                                        <div>
                                            <h6>Receita</h6>
                                            <h3>R$ {{ stats.receita }}</h3>
                                        </div>
                                        <i class="fas fa-dollar-sign fa-2x"></i>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                    
                    <div class="row">
                        <div class="col-12">
                            <div class="card">
                                <div class="card-header">
                                    <h5>🎉 Sistema ERP JSP Funcionando!</h5>
                                </div>
                                <div class="card-body">
                                    <div class="alert alert-success">
                                        <h6>✅ Deploy realizado com sucesso!</h6>
                                        <p>O sistema ERP JSP está totalmente operacional no Render.</p>
                                        <ul>
                                            <li>✅ Autenticação funcionando</li>
                                            <li>✅ Dashboard completo</li>
                                            <li>✅ Navegação sidebar</li>
                                            <li>✅ Sistema pronto para uso</li>
                                        </ul>
                                    </div>
                                    
                                    <h6>🔗 Próximas funcionalidades:</h6>
                                    <p>Use os links na sidebar para acessar:</p>
                                    <div class="row">
                                        <div class="col-md-6">
                                            <ul>
                                                <li>Gestão de Clientes</li>
                                                <li>Controle de Fornecedores</li>
                                                <li>Catálogo de Produtos</li>
                                            </ul>
                                        </div>
                                        <div class="col-md-6">
                                            <ul>
                                                <li>Sistema de Propostas</li>
                                                <li>Módulo Financeiro</li>
                                                <li>Relatórios e PDFs</li>
                                            </ul>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
</body>
</html>
"""

# Rotas simples mas funcionais
@app.route('/')
def home():
    if 'user' in session:
        return redirect('/dashboard')
    return redirect('/auth/login')

@app.route('/auth/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        senha = request.form.get('senha')
        
        # Login simples mas funcional
        if email == 'admin@jsp.com' and senha == 'admin123':
            session['user'] = 'Administrador JSP'
            flash('Login realizado com sucesso!', 'success')
            return redirect('/dashboard')
        else:
            return render_template_string(LOGIN_TEMPLATE, 
                                        error='Email ou senha incorretos!', 
                                        email=email)
    
    return render_template_string(LOGIN_TEMPLATE)

@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect('/auth/login')
    
    # Stats de exemplo
    stats = {
        'clientes': 45,
        'propostas': 23,
        'produtos': 156,
        'receita': '12.450'
    }
    
    return render_template_string(DASHBOARD_TEMPLATE, 
                                usuario=session['user'], 
                                stats=stats)

@app.route('/logout')
def logout():
    session.clear()
    flash('Logout realizado com sucesso!', 'info')
    return redirect('/auth/login')

# Rotas modulares (básicas)
@app.route('/<modulo>')
def modulo_generic(modulo):
    if 'user' not in session:
        return redirect('/auth/login')
    
    return f"""
    <h1>📋 Módulo {modulo.title()}</h1>
    <p>Funcionalidade em desenvolvimento...</p>
    <a href="/dashboard">← Voltar ao Dashboard</a>
    """

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    print("🚀 ERP JSP Sistema Simples Iniciado!")
    print(f"🌐 Acesse: https://erp-jsp.onrender.com")
    print("🔐 Login: admin@jsp.com / admin123")
    app.run(host='0.0.0.0', port=port, debug=False)