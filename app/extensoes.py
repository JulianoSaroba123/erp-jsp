# -*- coding: utf-8 -*-
"""
ERP JSP v3.0 - Extensões do Sistema
====================================

Inicializa e configura todas as extensões Flask.
Centraliza a configuração de SQLAlchemy, Migrate, etc.

Autor: JSP Soluções
Data: 2025
"""

from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager

# Inicialização das extensões
# Serão configuradas no create_app()
db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()

def init_extensions(app):
    """
    Inicializa todas as extensões com a aplicação Flask.
    
    Args:
        app: Instância da aplicação Flask
    """
    # Banco de dados
    db.init_app(app)
    
    # Migrações
    migrate.init_app(app, db)
    
    # Flask-Login
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Por favor, faça login para acessar esta página.'
    login_manager.login_message_category = 'info'
    
    # User loader para Flask-Login
    @login_manager.user_loader
    def load_user(user_id):
        try:
            from app.auth.usuario_model import Usuario
            return Usuario.query.get(int(user_id))
        except Exception as e:
            print(f"⚠️ Erro no load_user: {e}")
            return None
    
    # Cria diretório do banco se necessário (para SQLite)
    import os
    db_path = app.config.get('SQLALCHEMY_DATABASE_URI')
    if db_path and db_path.startswith('sqlite:///'):
        db_file = db_path.replace('sqlite:///', '')
        db_dir = os.path.dirname(db_file)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)