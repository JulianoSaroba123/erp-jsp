import os
from flask import Flask

def create_app():
    app = Flask(__name__)
    app.secret_key = os.environ.get("SECRET_KEY", "dev")
    from .autenticacao import bp_autenticacao
    app.register_blueprint(bp_autenticacao)
    return app
    
