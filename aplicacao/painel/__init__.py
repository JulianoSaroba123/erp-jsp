from flask import Flask
from aplicacao.painel.rotas_painel import painel_bp

def init_app(app: Flask):
    app.register_blueprint(painel_bp)
