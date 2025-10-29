import os
from dotenv import load_dotenv
from datetime import timedelta

# Carrega variáveis do arquivo .env (para ambiente local)
load_dotenv()

class Config:
    """Configuração base do aplicativo"""
    
    # Banco de dados PostgreSQL (Render)
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL")
    if SQLALCHEMY_DATABASE_URI and SQLALCHEMY_DATABASE_URI.startswith("postgres://"):
        # Render às vezes fornece URL antiga; corrige para SQLAlchemy
        SQLALCHEMY_DATABASE_URI = SQLALCHEMY_DATABASE_URI.replace("postgres://", "postgresql://", 1)
    elif not SQLALCHEMY_DATABASE_URI:
        # Fallback para SQLite local se não houver DATABASE_URL
        basedir = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
        SQLALCHEMY_DATABASE_URI = f'sqlite:///{os.path.join(basedir, "erp.db")}'
    
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = os.getenv("SECRET_KEY", "jsp_chave_secreta")
    
    # Configurações gerais
    DEBUG = False
    TESTING = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
        'pool_timeout': 20,
        'max_overflow': 0
    }
    
    # Configurações de sessão
    PERMANENT_SESSION_LIFETIME = timedelta(hours=2)
    SESSION_COOKIE_SECURE = False  # True em produção com HTTPS
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'

class DevelopmentConfig(Config):
    """Configuração para desenvolvimento"""
    DEBUG = True
    SQLALCHEMY_ECHO = False  # True para ver SQL queries
    
    # Desabilitar cache de templates para desenvolvimento
    TEMPLATES_AUTO_RELOAD = True
    SEND_FILE_MAX_AGE_DEFAULT = 0
    
    # Configurações específicas do Jinja2 para desenvolvimento
    JINJA2_AUTO_RELOAD = True
    
    # Flask server configuration for URL building
    SERVER_NAME = None  # Allow any host
    APPLICATION_ROOT = '/'
    PREFERRED_URL_SCHEME = 'http'

class ProductionConfig(Config):
    """Configuração para produção"""
    DEBUG = False
    SESSION_COOKIE_SECURE = True
    WTF_CSRF_ENABLED = True
    
    # Configurações específicas de produção
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        'pool_recycle': 3600,
        'pool_timeout': 30,
        'max_overflow': 20,
        'pool_size': 10
    }

class TestingConfig(Config):
    """Configuração para testes"""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False

# Mapeamento de configurações
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}