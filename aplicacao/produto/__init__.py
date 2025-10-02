# Módulo de produtos

def init_app(app):
    """Inicializa o módulo produto com a aplicação Flask"""
    try:
        from .produto_routes import produto_bp
        app.register_blueprint(produto_bp, url_prefix='/produtos')
    except ImportError:
        pass