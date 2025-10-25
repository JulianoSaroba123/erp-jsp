"""Pacote do módulo de prospecção de clientes.

Este pacote contém a lógica de dados, rotas e templates
responsáveis por pesquisar e armazenar potenciais clientes
(prospects) com base em filtros como CNAE, cidade, estado e CNPJ.

Para utilizar em uma aplicação Flask, registre o Blueprint
``prospeccao_bp`` definido em ``prospeccao_routes.py``:

    from prospeccao.prospeccao_routes import prospeccao_bp
    app.register_blueprint(prospeccao_bp)

"""

from .prospeccao_model import Prospect, buscar_empresas
from .prospeccao_routes import prospeccao_bp  # noqa: F401