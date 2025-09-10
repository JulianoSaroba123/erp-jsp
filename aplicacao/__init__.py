import os
from flask import Flask
from aplicacao.extensoes import db

def create_app():
    # Configurar o caminho central para templates
    template_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'templates')
    app = Flask(__name__, template_folder=template_path, static_folder=os.path.join(os.path.abspath(os.path.dirname(__file__)), '..', 'static'), static_url_path='/static')

    app.secret_key = os.environ.get("SECRET_KEY", "dev")

    # Configurações do banco de dados (SQLite local por padrão) usando caminho absoluto
    from pathlib import Path
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    db_path = os.path.join(base_dir, 'database', 'database.db')
    app.config.setdefault('SQLALCHEMY_DATABASE_URI', f"sqlite:///{Path(db_path).as_posix()}")
    app.config.setdefault('SQLALCHEMY_TRACK_MODIFICATIONS', False)

    # Inicializa extensões
    db.init_app(app)

    # Torna current_app disponível nos templates quando necessário
    app.jinja_env.globals['current_app'] = app

    # Filtro global para evitar exibir a string literal 'None' ou valores None
    def _tidy(value):
        try:
            if value is None:
                return ''
            if isinstance(value, str) and value.strip().lower() == 'none':
                return ''
            return value
        except Exception:
            return ''

    app.jinja_env.filters['tidy'] = _tidy

    from .autenticacao import bp_autenticacao
    app.register_blueprint(bp_autenticacao)

    from aplicacao.painel import init_app as painel_init
    painel_init(app)

    # Registrar o módulo cliente através do init_app
    from aplicacao.cliente import init_app as cliente_init
    cliente_init(app)

    # Injetar totais usados pelos KPIs no template base
    try:
        from aplicacao.cliente.cliente_model import Cliente
        from aplicacao.extensoes import db as _db

        @app.context_processor
        def inject_kpis():
            try:
                # total de clientes (apenas contar linhas na tabela)
                total_clientes = _db.session.query(Cliente).count()
            except Exception:
                total_clientes = 0

            # placeholders para outros KPIs (pode ser substituído por lógica real)
            total_produtos = 0
            total_os_emitidas = 0
            faturamento_total = 'R$ 0,00'

            return {
                'total_clientes': total_clientes,
                'total_produtos': total_produtos,
                'total_os_emitidas': total_os_emitidas,
                'faturamento_total': faturamento_total
            }
    except Exception:
        # Se importar modelos falhar (por ex durante setup), não interrompe a criação do app
        pass

    return app

