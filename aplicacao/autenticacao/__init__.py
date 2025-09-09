bp_autenticacao = Blueprint('autenticacao', __name__, template_folder='templates')
from flask import Blueprint

bp_autenticacao = Blueprint('autenticacao', __name__, template_folder='templates')

from . import rotas

from flask import Blueprint

bp_autenticacao = Blueprint('autenticacao', __name__, template_folder='templates')

from . import rotas
from aplicacao import create_app
import os
app = create_app()