from .cliente_routes import cliente_bp
from .cliente_api import cliente_api_bp


def init_app(app):
    app.register_blueprint(cliente_bp)
    app.register_blueprint(cliente_api_bp)
    return app