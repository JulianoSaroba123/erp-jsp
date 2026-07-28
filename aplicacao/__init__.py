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
    database_url = os.environ.get('DATABASE_URL')
    if database_url:
        app.config['SQLALCHEMY_DATABASE_URI'] = database_url
    else:
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

    from aplicacao.financeiro import financeiro_bp
    app.register_blueprint(financeiro_bp)

    from aplicacao.ordem_servico.ordem_servico_routes import bp as ordens_bp
    app.register_blueprint(ordens_bp)

    # Registrar o módulo cliente através do init_app
    from aplicacao.cliente import init_app as cliente_init
    cliente_init(app)

    # Injetar totais usados pelos KPIs no template base
    try:
        from aplicacao.cliente.cliente_model import Cliente
        from aplicacao.extensoes import db as _db
        from aplicacao.financeiro.indicadores_service import periodo_mes_atual, resumir_financeiro_periodo

        @app.context_processor
        def inject_kpis():
            try:
                # total de clientes (apenas contar linhas na tabela)
                total_clientes = _db.session.query(Cliente).count()
            except Exception:
                total_clientes = 0

            try:
                inicio_mes, fim_mes = periodo_mes_atual()
                resumo_financeiro = resumir_financeiro_periodo(inicio_mes, fim_mes)
            except Exception:
                resumo_financeiro = None

            total_produtos = 0
            total_os_emitidas = 0
            faturamento_total = 'R$ 0,00'

            return {
                'total_clientes': total_clientes,
                'total_produtos': total_produtos,
                'total_os_emitidas': total_os_emitidas,
                'faturamento_total': faturamento_total,
                'resumo_financeiro_painel': resumo_financeiro,
                'receitas_realizadas_painel': resumo_financeiro.receitas_realizadas if resumo_financeiro else 0,
                'despesas_pagas_painel': resumo_financeiro.despesas_realizadas if resumo_financeiro else 0,
                'saldo_realizado_painel': resumo_financeiro.resultado_realizado if resumo_financeiro else 0,
                'saldo_projetado_painel': resumo_financeiro.saldo_projetado if resumo_financeiro else 0,
                'contas_a_receber_pendentes_painel': resumo_financeiro.contas_a_receber_pendentes if resumo_financeiro else 0,
                'contas_a_pagar_pendentes_painel': resumo_financeiro.contas_a_pagar_pendentes if resumo_financeiro else 0,
                'inconsistencias_financeiras_painel_qtd': resumo_financeiro.lancamentos_pagos_sem_data_qtd if resumo_financeiro else 0,
            }
    except Exception:
        # Se importar modelos falhar (por ex durante setup), não interrompe a criação do app
        pass

    return app

