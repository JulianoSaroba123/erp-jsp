from flask import Blueprint

financeiro_bp = Blueprint('financeiro', __name__, url_prefix='/financeiro', template_folder='templates')

from . import financeiro_routes  # noqa: E402,F401
from . import financeiro_model  # noqa: E402,F401
from . import lancamento_os_model  # noqa: E402,F401
from . import lancamento_os_service  # noqa: E402,F401

# Importar e registrar blueprint de formação de preço
from .formacao_preco import formacao_preco_bp  # noqa: E402,F401

# Facilitar importação dos modelos e serviços
from .financeiro_model import LancamentoFinanceiro  # noqa: E402,F401
from .lancamento_os_model import LancamentoFinanceiroOS  # noqa: E402,F401
from .lancamento_os_service import gerar_lancamentos_financeiro, remover_lancamentos_da_os, parse_schedule_custom  # noqa: E402,F401
