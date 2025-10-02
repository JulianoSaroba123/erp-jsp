# Módulo de serviços do ERP JSP
from .servico_model import Servico
from .servico_routes import servico_bp

__all__ = ['Servico', 'servico_bp']

def init_app(app):
    """Inicializa o módulo servico com a aplicação Flask"""
    try:
        app.register_blueprint(servico_bp, url_prefix='/servicos')
    except Exception:
        pass