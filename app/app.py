# -*- coding: utf-8 -*-
"""
ERP JSP v3.0 - Aplicação Principal
===================================

Factory da aplicação Flask com padrão modular.
Registra todos os blueprints e configura extensões.

Autor: JSP Soluções
Data: 2025
"""

import os
from flask import Flask, render_template, request
from datetime import datetime
from app.config import config
from app.extensoes import init_extensions

def create_app(config_name=None):
    """
    Factory da aplicação Flask.

    Cria e configura a aplicação usando o padrão Application Factory.
    Registra blueprints, extensões e handlers de erro.

    Args:
        config_name (str): Nome da configuração ('development', 'production', 'testing')
    Returns:
        Flask: Instância configurada da aplicação
    """
    # Cria a aplicação Flask
    # Define o caminho da pasta static na raiz do projeto
    static_folder = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static')
    app = Flask(__name__, static_folder=static_folder)

    # Ensure logs directory exists early so middleware/handlers can write
    try:
        logs_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'logs')
        os.makedirs(logs_dir, exist_ok=True)
    except Exception:
        pass

    # Determina o ambiente de configuração
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'development')

    # Aplica a configuração - usa diretamente a classe Config
    app.config.from_object("app.config.Config")
    
    # Configurações específicas do Jinja2 para desenvolvimento
    if app.config.get('DEBUG'):
        app.jinja_env.auto_reload = True
        app.config['TEMPLATES_AUTO_RELOAD'] = True

    # Inicializa extensões
    init_extensions(app)

    # WSGI middleware to log unhandled exceptions (captures before Flask handlers)
    class ExceptionLoggerMiddleware:
        def __init__(self, app):
            self.app = app

        def __call__(self, environ, start_response):
            try:
                return self.app(environ, start_response)
            except Exception:
                try:
                    import traceback
                    log_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'logs', 'error.log')
                    with open(log_file, 'a', encoding='utf-8') as f:
                        f.write('\n\n===== UNHANDLED EXCEPTION %s UTC =====\n' % datetime.utcnow().isoformat())
                        # environ contains PATH_INFO and REQUEST_METHOD
                        try:
                            f.write('Path: %s Method: %s\n' % (environ.get('PATH_INFO'), environ.get('REQUEST_METHOD')))
                        except Exception:
                            pass
                        traceback.print_exc(file=f)
                except Exception:
                    pass
                # Re-raise so Flask can handle it (and return 500)
                raise

    # Registra blueprints
    register_blueprints(app)
    
    # Registra rotas auxiliares
    register_auxiliary_routes(app)

    # Registra handlers de erro
    register_error_handlers(app)

    # Configura context processors
    register_context_processors(app)

    # Cria as tabelas do banco de dados se não existirem (necessário para Render/Gunicorn)
    with app.app_context():
        try:
            from app.extensoes import db
            db.create_all()
            print("[OK] Tabelas do banco de dados verificadas/criadas!")
            
            # Cria usuário admin padrão se não existir nenhum usuário
            from app.auth.usuario_model import Usuario
            if Usuario.query.count() == 0:
                admin = Usuario(
                    nome='Administrador',
                    email='admin@jsp.com',
                    usuario='admin',
                    tipo_usuario='admin',
                    ativo=True,
                    email_confirmado=True
                )
                admin.set_password('admin123')
                db.session.add(admin)
                db.session.commit()
                print("[OK] Usuario admin padrao criado! (admin / admin123)")
        except Exception as e:
            print(f" ⚠ Aviso na criação de tabelas: {e}")
        
        # Popula banco com dados iniciais se estiver vazio
        try:
            popular_banco_se_vazio()
        except Exception as e:
            print(f" ⚠ Aviso ao popular banco: {e}")

    return app

def popular_banco_se_vazio():
    """Popula o banco com dados do erp.db se estiver vazio"""
    from app.ordem_servico.ordem_servico_model import OrdemServico
    from app.cliente.cliente_model import Cliente
    import os
    import sqlite3
    from datetime import datetime
    
    try:
        total_os = OrdemServico.query.count()
        
        if total_os > 0:
            print(f"✅ Banco já tem {total_os} OS")
            return
        
        print("📊 Banco de OS vazio - verificando erp.db...")
        
        if not os.path.exists('erp.db'):
            print("⚠️ erp.db não encontrado - pulando importação")
            return
        
        print("🔄 Importando dados do erp.db...")
        
        conn = sqlite3.connect('erp.db')
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Cria mapeamento de clientes (CPF/CNPJ)
        clientes_local = cursor.execute("SELECT id, nome, cpf_cnpj FROM clientes").fetchall()
        clientes_render = Cliente.query.all()
        
        mapa_clientes = {}
        for cli_local in clientes_local:
            for cli_render in clientes_render:
                if cli_render.cpf_cnpj and cli_local['cpf_cnpj'] and cli_render.cpf_cnpj == cli_local['cpf_cnpj']:
                    mapa_clientes[cli_local['id']] = cli_render.id
                    print(f"   Mapeado: {cli_local['nome']} (local {cli_local['id']} → render {cli_render.id})")
                    break
        
        # Importa OS
        ordens = cursor.execute("SELECT * FROM ordem_servico WHERE ativo = 1 ORDER BY id").fetchall()
        importadas = 0
        
        for row in ordens:
            cliente_id_render = mapa_clientes.get(row['cliente_id'])
            if not cliente_id_render:
                print(f"   ⚠️ Cliente local {row['cliente_id']} não encontrado no Render - pulando OS {row['numero']}")
                continue
            
            nova_os = OrdemServico(
                numero=row['numero'],
                cliente_id=cliente_id_render,
                titulo=row['titulo'] or 'OS sem título',
                descricao=row['descricao'],
                status=row['status'] or 'aberta',
                prioridade=row['prioridade'] or 'normal',
                data_abertura=row['data_abertura'] if row['data_abertura'] else datetime.now().date(),
                data_previsao=row['data_previsao'] if row['data_previsao'] else None,
                data_conclusao=row['data_conclusao'] if row['data_conclusao'] else None,
                valor_mao_obra=row['valor_mao_obra'] or 0,
                valor_produtos=row['valor_produtos'] or 0,
                valor_total=row['valor_total'] or 0,
                forma_pagamento=row['forma_pagamento'] or 'a_vista',
                num_parcelas=row['num_parcelas'] or 1,
                valor_entrada=row['valor_entrada'] or 0,
                observacoes=row['observacoes'],
                ativo=True
            )
            
            db.session.add(nova_os)
            importadas += 1
        
        db.session.commit()
        conn.close()
        
        print(f"✅ Auto-importação concluída: {importadas} OS importadas!")
        
    except Exception as e:
        print(f"❌ Erro na auto-importação: {e}")
        import traceback
        traceback.print_exc()

def register_blueprints(app):
    """
    Registra todos os blueprints da aplicação.

    Args:
        app (Flask): Instância da aplicação Flask
    """
    # Blueprint de autenticação
    from app.auth.auth_routes import auth_bp
    app.register_blueprint(auth_bp)
    
    # Blueprint do painel principal
    from app.painel.painel_routes import painel_bp
    app.register_blueprint(painel_bp)

    # Blueprint de clientes
    from app.cliente.cliente_routes import cliente_bp
    app.register_blueprint(cliente_bp, url_prefix='/cliente')

    # Blueprint de fornecedores
    from app.fornecedor.fornecedor_routes import fornecedor_bp
    app.register_blueprint(fornecedor_bp, url_prefix='/fornecedor')

    # Blueprint de produtos
    from app.produto.produto_routes import produto_bp
    app.register_blueprint(produto_bp, url_prefix='/produto')

    # Blueprint de ordens de serviço
    from app.ordem_servico.ordem_servico_routes import ordem_servico_bp
    app.register_blueprint(ordem_servico_bp, url_prefix='/ordem_servico')

    # Blueprint de serviços
    from app.servico.servico_routes import servico_bp
    app.register_blueprint(servico_bp, url_prefix='/servico')

    # Blueprint financeiro
    from app.financeiro.financeiro_routes import bp_financeiro
    app.register_blueprint(bp_financeiro, url_prefix='/financeiro')

    # Blueprint de configuração do sistema
    from app.configuracao.configuracao_routes import bp_config
    app.register_blueprint(bp_config, url_prefix='/configuracao')

    # Blueprint de precificação
    from app.precificacao.precificacao_routes import precificacao_bp
    from app.precificacao.precificacao_model import ConfigPrecificacao  # Importar modelo para SQLAlchemy
    app.register_blueprint(precificacao_bp, url_prefix='/precificacao')

    # Blueprint de prospecção
    from app.prospeccao.prospeccao_routes import prospeccao_bp
    app.register_blueprint(prospeccao_bp, url_prefix='/prospeccao')

    # Blueprint de propostas
    from app.proposta.proposta_routes import proposta_bp
    app.register_blueprint(proposta_bp, url_prefix='/propostas')


def register_auxiliary_routes(app):
    """
    Registra rotas auxiliares do sistema.
    
    Args:
        app: Instância da aplicação Flask
    """
    from flask import send_from_directory
    import os
    
    @app.route('/uploads/<path:filename>')
    def uploaded_file(filename):
        """Serve arquivos de upload."""
        uploads_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'uploads')
        return send_from_directory(uploads_dir, filename)

def register_error_handlers(app):
    """
    Registra handlers para erros HTTP.

    Args:
        app: Instância da aplicação Flask
    """
    @app.errorhandler(404)
    def not_found_error(error):
        """Handler para erro 404 - Página não encontrada."""
        return render_template('errors/404.html'), 404

    @app.errorhandler(500)
    def internal_error(error):
        """Handler para erro 500 - Erro interno do servidor."""
        from app.extensoes import db
        import traceback, os

        # Rollback DB session to avoid broken transactions
        try:
            db.session.rollback()
        except Exception:
            pass

        # Ensure logs directory exists and append the full traceback + request info
        try:
            log_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'logs')
            os.makedirs(log_dir, exist_ok=True)
            log_file = os.path.join(log_dir, 'error.log')
            with open(log_file, 'a', encoding='utf-8') as f:
                f.write('\n\n===== ERROR %s UTC =====\n' % datetime.utcnow().isoformat())
                try:
                    f.write(f'Path: {request.path} Method: {request.method}\n')
                    f.write('Remote: %s\n' % request.remote_addr)
                    f.write('Headers: %s\n' % dict(request.headers))
                    try:
                        f.write('Form: %s\n' % request.form.to_dict(flat=True))
                    except Exception:
                        f.write('Form: <unable to read>\n')
                except Exception:
                    f.write('Request info: <unavailable>\n')

                f.write('Traceback:\n')
                traceback.print_exc(file=f)
        except Exception:
            # If logging failed, ignore to not cause cascading errors
            pass

        return render_template('errors/500.html'), 500

def register_context_processors(app):
    """
    Registra context processors globais.

    Args:
        app: Instância da aplicação Flask
    """
    @app.context_processor
    def inject_config():
        """Injeta configurações no contexto dos templates."""
        # Helper functions to safely format dates/times passed to templates.
        from datetime import datetime, date, time

        def format_date(val, fmt='%Y-%m-%d'):
            if not val:
                return ''
            # If it's already a date/datetime object
            try:
                if hasattr(val, 'strftime'):
                    return val.strftime(fmt)
            except Exception:
                pass
            # If it's a string, try to parse common formats
            if isinstance(val, str):
                for pattern in ('%Y-%m-%d', '%d/%m/%Y', '%Y-%m-%dT%H:%M:%S', '%Y-%m-%dT%H:%M'):
                    try:
                        dt = datetime.strptime(val, pattern)
                        return dt.strftime(fmt)
                    except Exception:
                        continue
            return ''

        def format_time(val, fmt='%H:%M'):
            if not val:
                return ''
            try:
                if hasattr(val, 'strftime'):
                    return val.strftime(fmt)
            except Exception:
                pass
            if isinstance(val, str):
                # try parsing common time formats
                for pattern in ('%H:%M:%S', '%H:%M'):
                    try:
                        dt = datetime.strptime(val, pattern)
                        return dt.strftime(fmt)
                    except Exception:
                        continue
            return ''

        def format_datetime(val, fmt='%Y-%m-%dT%H:%M'):
            if not val:
                return ''
            try:
                if hasattr(val, 'strftime'):
                    return val.strftime(fmt)
            except Exception:
                pass
            if isinstance(val, str):
                for pattern in ('%Y-%m-%dT%H:%M:%S', '%Y-%m-%d %H:%M:%S', '%Y-%m-%dT%H:%M'):
                    try:
                        dt = datetime.strptime(val, pattern)
                        return dt.strftime(fmt)
                    except Exception:
                        continue
            return ''

        return {
            'COMPANY_NAME': 'ERP JSP',
            'SYSTEM_VERSION': '3.0',
            'format_date': format_date,
            'format_time': format_time,
            'format_datetime': format_datetime
        }
    @app.context_processor
    def utility_processor():
        from flask import url_for
        def safe_url_for(endpoint, **values):
            try:
                return url_for(endpoint, **values)
            except Exception:
                # If endpoint is not available, return a harmless anchor
                return '#'
        return {'safe_url_for': safe_url_for}


# Cria a instância da aplicação para Gunicorn/WSGI
# Gunicorn importa: app.app:app
app = create_app()