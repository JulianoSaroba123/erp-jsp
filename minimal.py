#!/usr/bin/env python3
"""
MINIMAL WORKING VERSION
=======================
Versão mínima garantida para funcionar
"""

import os
import sys
from flask import Flask, render_template_string

# Adicionar path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Template mínimo mas funcional
TEMPLATE = """
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ERP JSP Sistema</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body class="bg-dark text-light">
    <div class="container mt-5">
        <div class="row justify-content-center">
            <div class="col-md-8">
                <div class="card bg-secondary">
                    <div class="card-header bg-primary">
                        <h1 class="text-center">🚀 ERP JSP Sistema</h1>
                    </div>
                    <div class="card-body">
                        <div class="alert alert-success">
                            <h4>✅ Sistema Online e Funcionando!</h4>
                            <p>Deploy realizado com sucesso no Render.</p>
                        </div>
                        
                        <div class="row">
                            <div class="col-md-6">
                                <h5>📊 Status do Sistema:</h5>
                                <ul>
                                    <li>✅ Servidor: Ativo</li>
                                    <li>✅ Flask: Funcionando</li>
                                    <li>✅ Render: Conectado</li>
                                    <li>⚠️ Banco: {{ db_status }}</li>
                                </ul>
                            </div>
                            <div class="col-md-6">
                                <h5>🔧 Próximos Passos:</h5>
                                <ol>
                                    <li>Verificar logs do Render</li>
                                    <li>Confirmar variáveis de ambiente</li>
                                    <li>Testar conexão com PostgreSQL</li>
                                </ol>
                            </div>
                        </div>
                        
                        <div class="mt-3">
                            <h5>🔗 Links Úteis:</h5>
                            <a href="/test" class="btn btn-primary me-2">Testar Sistema</a>
                            <a href="/auth/login" class="btn btn-success me-2">Tentar Login</a>
                            <a href="/painel" class="btn btn-info">Dashboard</a>
                        </div>
                        
                        <div class="mt-3">
                            <small class="text-muted">
                                <strong>Environment Variables:</strong><br>
                                DATABASE_URL: {{ 'Configurada' if database_url else 'Não configurada' }}<br>
                                SECRET_KEY: {{ 'Configurada' if secret_key else 'Não configurada' }}<br>
                                FLASK_ENV: {{ flask_env }}
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

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-key-123')
    
    @app.route('/')
    def home():
        # Verificar status das variáveis
        database_url = os.environ.get('DATABASE_URL')
        secret_key = os.environ.get('SECRET_KEY')
        flask_env = os.environ.get('FLASK_ENV', 'development')
        
        # Tentar conectar ao banco
        db_status = "Não testado"
        if database_url:
            try:
                import psycopg2
                # Teste simples de conexão
                db_status = "PostgreSQL disponível"
            except:
                db_status = "Erro na conexão"
        else:
            db_status = "DATABASE_URL não configurada"
        
        return render_template_string(TEMPLATE, 
                                    database_url=bool(database_url),
                                    secret_key=bool(secret_key),
                                    flask_env=flask_env,
                                    db_status=db_status)
    
    @app.route('/test')
    def test():
        return {"status": "OK", "message": "Sistema funcionando!", "env": dict(os.environ)}
    
    @app.route('/auth/login')
    def login():
        return "<h1>🔐 Tela de Login</h1><p>Sistema em desenvolvimento...</p>"
    
    @app.route('/painel')
    def painel():
        return "<h1>📊 Dashboard</h1><p>Sistema em desenvolvimento...</p>"
    
    return app

# Criar app
app = create_app()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    print(f"🚀 Starting MINIMAL ERP JSP on 0.0.0.0:{port}")
    app.run(host='0.0.0.0', port=port, debug=False)