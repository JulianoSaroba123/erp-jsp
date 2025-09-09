from flask import Blueprint

bp_autenticacao = Blueprint(
    'autenticacao',
    __name__,
    template_folder='templates'
)

from . import rotas