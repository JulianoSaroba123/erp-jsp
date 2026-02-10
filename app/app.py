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
    # Define o caminho da pasta static dentro de app/
    static_folder = os.path.join(os.path.dirname(__file__), 'static')
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

    # Aplica a configuração correta baseada no ambiente
    app.config.from_object(config[config_name])
    
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
            
            # Importa todos os modelos para db.create_all() funcionar
            try:
                from app.kits_distribuidor.kits_model import KitFotovoltaico
                print("[OK] Modelo KitFotovoltaico importado")
            except Exception as e:
                print(f" ⚠ Modelo KitFotovoltaico não disponível: {e}")
            
            # Importa modelos do Módulo Energia Solar v3.0
            try:
                from app.concessionaria.concessionaria_model import Concessionaria
                from app.energia_solar.orcamento_model import OrcamentoItem
                from app.energia_solar.catalogo_model import ProjetoSolar, KitSolar, PlacaSolar, InversorSolar
                from app.energia_solar.energia_solar_model import CalculoEnergiaSolar
                from app.energia_solar.custo_fixo_model import CustoPadraoSolar
                print("[OK] Modelos Energia Solar v3.0 importados (7 tabelas)")
            except Exception as e:
                print(f" ⚠ Erro ao importar modelos Energia Solar v3.0: {e}")
            
            # Importa modelo de Equipamentos
            try:
                from app.equipamento.equipamento_model import Equipamento
                print("[OK] Modelo Equipamento importado")
            except Exception as e:
                print(f" ⚠ Erro ao importar modelo Equipamento: {e}")
            
            # Importa modelos Financeiros Avançados
            try:
                from app.financeiro.financeiro_model import (
                    LancamentoFinanceiro, 
                    CategoriaFinanceira, 
                    PlanoContas,
                    ContaBancaria,
                    CentroCusto,
                    HistoricoFinanceiro,
                    ExtratoBancario,
                    CustoFixo,
                    OrcamentoAnual,
                    NotaFiscal
                )
                print("[OK] Modelos Financeiros Avançados importados (9 tabelas)")
            except Exception as e:
                print(f" ⚠ Erro ao importar modelos Financeiros: {e}")
            
            db.create_all()
            print("[OK] Tabelas do banco de dados verificadas/criadas!")
            
            # === MIGRAÇÕES AUTOMÁTICAS ===
            print("\n🔧 Executando migrações automáticas...")
            
            # Migração: Adicionar coluna numero_projeto em calculo_energia_solar (PRIORIDADE MÁXIMA)
            try:
                from sqlalchemy import text, inspect
                inspector = inspect(db.engine)
                
                print("📋 Verificando tabela calculo_energia_solar...")
                if 'calculo_energia_solar' in inspector.get_table_names():
                    colunas = [c['name'] for c in inspector.get_columns('calculo_energia_solar')]
                    print(f"   Colunas existentes: {len(colunas)}")
                    
                    # Adiciona coluna 'numero_projeto' se não existir
                    if 'numero_projeto' not in colunas:
                        print("   🔧 Adicionando coluna 'numero_projeto'...")
                        db.session.execute(text("ALTER TABLE calculo_energia_solar ADD COLUMN numero_projeto VARCHAR(50)"))
                        db.session.commit()
                        print("   ✅ Coluna 'numero_projeto' adicionada em calculo_energia_solar")
                    else:
                        print("   ✓ Coluna 'numero_projeto' já existe")
                else:
                    print("   ⚠️ Tabela calculo_energia_solar não encontrada")
            except Exception as e:
                db.session.rollback()
                print(f"   ❌ ERRO na migração calculo_energia_solar: {e}")
                import traceback
                traceback.print_exc()
            
            # Migração: Adicionar colunas faltantes em orcamento_itens (v3.0)
            try:
                from sqlalchemy import text, inspect
                inspector = inspect(db.engine)
                
                if 'orcamento_itens' in inspector.get_table_names():
                    colunas = [c['name'] for c in inspector.get_columns('orcamento_itens')]
                    
                    # Adiciona coluna 'categoria' se não existir
                    if 'categoria' not in colunas:
                        db.session.execute(text("ALTER TABLE orcamento_itens ADD COLUMN categoria VARCHAR(50)"))
                        db.session.commit()
                        print("[OK] Coluna 'categoria' adicionada em orcamento_itens")
                    
                    # Adiciona coluna 'ordem' se não existir
                    if 'ordem' not in colunas:
                        db.session.execute(text("ALTER TABLE orcamento_itens ADD COLUMN ordem INTEGER DEFAULT 0"))
                        db.session.commit()
                        print("[OK] Coluna 'ordem' adicionada em orcamento_itens")
                    
                    # Adiciona coluna 'criado_em' se não existir
                    if 'criado_em' not in colunas:
                        db.session.execute(text("ALTER TABLE orcamento_itens ADD COLUMN criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP"))
                        db.session.commit()
                        print("[OK] Coluna 'criado_em' adicionada em orcamento_itens")
            except Exception as e:
                db.session.rollback()
                print(f"⚠️ Aviso na migração orcamento_itens: {e}")
            
            print("✅ Migrações automáticas concluídas!\n")
            
            # Migração: Adicionar colunas de auditoria em lancamentos_financeiros
            try:
                from sqlalchemy import text, inspect
                inspector = inspect(db.engine)
                
                if 'lancamentos_financeiros' in inspector.get_table_names():
                    colunas = [c['name'] for c in inspector.get_columns('lancamentos_financeiros')]
                    print("📋 Verificando colunas em lancamentos_financeiros...")
                    
                    # Adiciona colunas de auditoria se não existirem
                    if 'usuario_criador' not in colunas:
                        print("   🔧 Adicionando coluna 'usuario_criador'...")
                        db.session.execute(text("ALTER TABLE lancamentos_financeiros ADD COLUMN usuario_criador VARCHAR(100)"))
                        db.session.commit()
                    
                    if 'usuario_editor' not in colunas:
                        print("   🔧 Adicionando coluna 'usuario_editor'...")
                        db.session.execute(text("ALTER TABLE lancamentos_financeiros ADD COLUMN usuario_editor VARCHAR(100)"))
                        db.session.commit()
                    
                    if 'data_criacao_auditoria' not in colunas:
                        print("   🔧 Adicionando coluna 'data_criacao_auditoria'...")
                        db.session.execute(text("ALTER TABLE lancamentos_financeiros ADD COLUMN data_criacao_auditoria TIMESTAMP DEFAULT CURRENT_TIMESTAMP"))
                        db.session.commit()
                    
                    if 'data_edicao_auditoria' not in colunas:
                        print("   🔧 Adicionando coluna 'data_edicao_auditoria'...")
                        db.session.execute(text("ALTER TABLE lancamentos_financeiros ADD COLUMN data_edicao_auditoria TIMESTAMP"))
                        db.session.commit()
                    
                    # Adiciona colunas de gestão financeira avançada
                    if 'conta_bancaria_id' not in colunas:
                        print("   🔧 Adicionando coluna 'conta_bancaria_id'...")
                        db.session.execute(text("ALTER TABLE lancamentos_financeiros ADD COLUMN conta_bancaria_id INTEGER REFERENCES contas_bancarias(id)"))
                        db.session.commit()
                    
                    if 'centro_custo_id' not in colunas:
                        print("   🔧 Adicionando coluna 'centro_custo_id'...")
                        db.session.execute(text("ALTER TABLE lancamentos_financeiros ADD COLUMN centro_custo_id INTEGER REFERENCES centros_custo(id)"))
                        db.session.commit()
                    
                    if 'comprovante_anexo' not in colunas:
                        print("   🔧 Adicionando coluna 'comprovante_anexo'...")
                        db.session.execute(text("ALTER TABLE lancamentos_financeiros ADD COLUMN comprovante_anexo VARCHAR(255)"))
                        db.session.commit()
                    
                    if 'numero_parcela' not in colunas:
                        print("   🔧 Adicionando coluna 'numero_parcela'...")
                        db.session.execute(text("ALTER TABLE lancamentos_financeiros ADD COLUMN numero_parcela VARCHAR(20)"))
                        db.session.commit()
                    
                    if 'valor_original' not in colunas:
                        print("   🔧 Adicionando coluna 'valor_original'...")
                        db.session.execute(text("ALTER TABLE lancamentos_financeiros ADD COLUMN valor_original NUMERIC(12, 2)"))
                        db.session.commit()
                    
                    if 'juros' not in colunas:
                        print("   🔧 Adicionando coluna 'juros'...")
                        db.session.execute(text("ALTER TABLE lancamentos_financeiros ADD COLUMN juros NUMERIC(12, 2) DEFAULT 0"))
                        db.session.commit()
                    
                    if 'desconto' not in colunas:
                        print("   🔧 Adicionando coluna 'desconto'...")
                        db.session.execute(text("ALTER TABLE lancamentos_financeiros ADD COLUMN desconto NUMERIC(12, 2) DEFAULT 0"))
                        db.session.commit()
                    
                    if 'multa' not in colunas:
                        print("   🔧 Adicionando coluna 'multa'...")
                        db.session.execute(text("ALTER TABLE lancamentos_financeiros ADD COLUMN multa NUMERIC(12, 2) DEFAULT 0"))
                        db.session.commit()
                    
                    if 'plano_conta_id' not in colunas:
                        print("   🔧 Adicionando coluna 'plano_conta_id'...")
                        db.session.execute(text("ALTER TABLE lancamentos_financeiros ADD COLUMN plano_conta_id INTEGER REFERENCES plano_contas(id)"))
                        db.session.commit()
                    
                    # 🎯 RASTREABILIDADE - Campos de origem do lançamento
                    if 'origem' not in colunas:
                        print("   🔧 Adicionando coluna 'origem'...")
                        db.session.execute(text("ALTER TABLE lancamentos_financeiros ADD COLUMN origem VARCHAR(50) DEFAULT 'MANUAL'"))
                        db.session.commit()
                        # Atualizar registros existentes
                        db.session.execute(text("UPDATE lancamentos_financeiros SET origem = 'MANUAL' WHERE origem IS NULL"))
                        db.session.commit()
                        print("   ✅ Coluna 'origem' adicionada e registros atualizados!")
                    
                    if 'custo_fixo_id' not in colunas:
                        print("   🔧 Adicionando coluna 'custo_fixo_id'...")
                        db.session.execute(text("ALTER TABLE lancamentos_financeiros ADD COLUMN custo_fixo_id INTEGER REFERENCES custos_fixos(id)"))
                        db.session.commit()
                        print("   ✅ Coluna 'custo_fixo_id' adicionada!")
                    
                    print("   ✅ Colunas verificadas/criadas!")
            except Exception as e:
                db.session.rollback()
                print(f"   ⚠️ Erro na migração de colunas financeiras: {e}")
            
            # Migração completa para PlanoContas
            try:
                print("\n🔍 Verificando tabela plano_contas...")
                
                # Verifica se a tabela existe
                resultado_plano = db.session.execute(text("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name = 'plano_contas'
                """))
                colunas_plano = {row[0] for row in resultado_plano}
                
                if not colunas_plano:
                    print("   ⚠️ Tabela plano_contas não existe, será criada pelo create_all()")
                else:
                    print(f"   📊 Tabela encontrada com {len(colunas_plano)} colunas")
                    
                    # Adiciona colunas faltantes
                    if 'descricao' not in colunas_plano:
                        print("   🔧 Adicionando coluna 'descricao'...")
                        db.session.execute(text("ALTER TABLE plano_contas ADD COLUMN descricao TEXT"))
                        db.session.commit()
                    
                    if 'nivel' not in colunas_plano:
                        print("   🔧 Adicionando coluna 'nivel'...")
                        db.session.execute(text("ALTER TABLE plano_contas ADD COLUMN nivel INTEGER DEFAULT 1"))
                        db.session.commit()
                    
                    if 'conta_pai_id' not in colunas_plano:
                        print("   🔧 Adicionando coluna 'conta_pai_id'...")
                        db.session.execute(text("ALTER TABLE plano_contas ADD COLUMN conta_pai_id INTEGER REFERENCES plano_contas(id)"))
                        db.session.commit()
                    
                    if 'aceita_lancamento' not in colunas_plano:
                        print("   🔧 Adicionando coluna 'aceita_lancamento'...")
                        db.session.execute(text("ALTER TABLE plano_contas ADD COLUMN aceita_lancamento BOOLEAN DEFAULT true"))
                        db.session.commit()
                    
                    if 'ativa' not in colunas_plano:
                        print("   🔧 Adicionando coluna 'ativa'...")
                        db.session.execute(text("ALTER TABLE plano_contas ADD COLUMN ativa BOOLEAN DEFAULT true"))
                        db.session.commit()
                    
                    if 'natureza' not in colunas_plano:
                        print("   🔧 Adicionando coluna 'natureza'...")
                        db.session.execute(text("ALTER TABLE plano_contas ADD COLUMN natureza VARCHAR(20)"))
                        db.session.commit()
                    
                    if 'ordem' not in colunas_plano:
                        print("   🔧 Adicionando coluna 'ordem'...")
                        db.session.execute(text("ALTER TABLE plano_contas ADD COLUMN ordem INTEGER DEFAULT 0"))
                        db.session.commit()
                    
                    print("   ✅ Colunas do plano_contas verificadas/criadas!")
            except Exception as e:
                db.session.rollback()
                print(f"   ⚠️ Erro na migração de plano_contas: {e}")
            
            print("✅ Todas as migrações concluídas!\n")
            
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
        # TEMPORARIAMENTE DESABILITADO PARA CRIAR BANCO LIMPO
        # try:
        #     popular_banco_se_vazio()
        # except Exception as e:
        #     print(f" ⚠ Aviso ao popular banco: {e}")
        
        # Correção global do campo 'ativo' (todas as tabelas)
        # TEMPORARIAMENTE DESABILITADO PARA CRIAR BANCO LIMPO
        # try:
        #     from scripts.corrigir_ativo_global import corrigir_campo_ativo_global
        #     corrigir_campo_ativo_global()
        # except Exception as e:
        #     print(f" ⚠ Aviso na correção global de 'ativo': {e}")
        
        # Migração automática: aumentar tamanho dos campos de proposta
        try:
            from sqlalchemy import text, inspect
            inspector = inspect(db.engine)
            
            # Verifica se a tabela propostas existe
            if 'propostas' in inspector.get_table_names():
                # Tenta aplicar migração (ignora se já foi aplicada)
                try:
                    db.session.execute(text("ALTER TABLE propostas ALTER COLUMN forma_pagamento TYPE VARCHAR(500)"))
                    db.session.execute(text("ALTER TABLE propostas ALTER COLUMN prazo_execucao TYPE VARCHAR(500)"))
                    db.session.execute(text("ALTER TABLE propostas ALTER COLUMN garantia TYPE VARCHAR(500)"))
                    db.session.commit()
                    print("[OK] Migração de campos de proposta aplicada!")
                except Exception as e:
                    db.session.rollback()
                    # Se já foi aplicada ou não precisa, apenas ignora
                    if 'already exists' not in str(e).lower():
                        pass  # Silenciosamente ignora
        except Exception as e:
            print(f" ⚠ Aviso na migração de campos de proposta: {e}")
        
        # Corrige sequências de ID (PostgreSQL)
        try:
            from sqlalchemy import text
            tabelas = ['propostas', 'clientes', 'fornecedores', 'produtos', 'ordem_servico', 
                      'usuarios', 'proposta_produto', 'proposta_servico', 'proposta_parcela']
            
            for tabela in tabelas:
                try:
                    query = f"SELECT setval(pg_get_serial_sequence('{tabela}', 'id'), COALESCE((SELECT MAX(id) FROM {tabela}), 1), true)"
                    db.session.execute(text(query))
                    db.session.commit()
                except Exception:
                    db.session.rollback()
                    pass  # Ignora se tabela não existe ou não tem sequência
            print("[OK] Sequências de ID verificadas/corrigidas!")
        except Exception as e:
            print(f" ⚠ Aviso na correção de sequências: {e}")
        
        # Migração: adicionar colunas de precificação
        try:
            from sqlalchemy import text, inspect
            inspector = inspect(db.engine)
            
            if 'config_precificacao' in inspector.get_table_names():
                colunas_existentes = [col['name'] for col in inspector.get_columns('config_precificacao')]
                
                # Adicionar colunas se não existirem
                if 'percentual_encargos' not in colunas_existentes:
                    db.session.execute(text("ALTER TABLE config_precificacao ADD COLUMN percentual_encargos FLOAT DEFAULT 80.0"))
                    db.session.commit()
                    print("[OK] Coluna percentual_encargos adicionada!")
                
                if 'percentual_impostos' not in colunas_existentes:
                    db.session.execute(text("ALTER TABLE config_precificacao ADD COLUMN percentual_impostos FLOAT DEFAULT 13.33"))
                    db.session.commit()
                    print("[OK] Coluna percentual_impostos adicionada!")
        except Exception as e:
            print(f" ⚠ Aviso na migração de precificação: {e}")
        
        # Migração: adicionar colunas faltantes em projeto_solar (v3.0)
        try:
            from sqlalchemy import text, inspect
            inspector = inspect(db.engine)
            
            if 'projeto_solar' in inspector.get_table_names():
                colunas_existentes = [col['name'] for col in inspector.get_columns('projeto_solar')]
                
                # Lista de campos necessários com seus tipos
                campos_necessarios = {
                    'numero': "VARCHAR(20)",
                    'tipo_instalacao': "VARCHAR(20) DEFAULT 'monofasica'",
                    'circuito': "VARCHAR(20)",
                    'status_orcamento': "VARCHAR(20) DEFAULT 'pendente'",
                    'taxa_disponibilidade': "DOUBLE PRECISION",
                    'economia_mensal': "DOUBLE PRECISION",
                    'tempo_retorno': "DOUBLE PRECISION",
                    'economia_25_anos': "DOUBLE PRECISION",
                    'economia_anual': "DOUBLE PRECISION",
                    'payback_anos': "DOUBLE PRECISION",
                    'modalidade_gd': "VARCHAR(50)",
                    'aliquota_fio_b': "DOUBLE PRECISION",
                    'usuario_criador': "VARCHAR(100)",
                    'data_criacao': "TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
                    'data_atualizacao': "TIMESTAMP",
                    'perda_eficiencia_anual': "DOUBLE PRECISION DEFAULT 0.8",
                    'usar_micro_inversor': "BOOLEAN DEFAULT FALSE",
                    'largura_area': "DOUBLE PRECISION",
                    'comprimento_area': "DOUBLE PRECISION",
                    'protecao_cc_tipo': "VARCHAR(50)",
                    'protecao_cc_corrente': "VARCHAR(20)",
                    'protecao_ca_tipo': "VARCHAR(50)",
                    'protecao_ca_corrente': "VARCHAR(20)",
                    'qtd_fases': "INTEGER",
                    'cabo_fase_bitola': "VARCHAR(20)",
                    'cabo_neutro_bitola': "VARCHAR(20)",
                    'qtd_terra': "INTEGER",
                    'cabo_terra_bitola': "VARCHAR(20)",
                    'padrao_observacoes': "VARCHAR(200)"
                }
                
                # Adicionar campos que não existem
                campos_adicionados = []
                for campo, tipo in campos_necessarios.items():
                    if campo not in colunas_existentes:
                        try:
                            db.session.execute(text(f"ALTER TABLE projeto_solar ADD COLUMN {campo} {tipo}"))
                            campos_adicionados.append(campo)
                        except Exception:
                            pass
                
                if campos_adicionados:
                    db.session.commit()
                    print(f"[OK] {len(campos_adicionados)} colunas adicionadas em projeto_solar: {', '.join(campos_adicionados)}")
                
                # Sincronizar circuito com tipo_instalacao para dados existentes
                if 'circuito' in campos_adicionados or 'tipo_instalacao' in campos_adicionados:
                    try:
                        db.session.execute(text("""
                            UPDATE projeto_solar 
                            SET circuito = CASE 
                                WHEN tipo_instalacao = 'monofasica' THEN 'Monofásico'
                                WHEN tipo_instalacao = 'bifasica' THEN 'Bifásico'
                                WHEN tipo_instalacao = 'trifasica' THEN 'Trifásico'
                                ELSE circuito
                            END
                            WHERE circuito IS NULL AND tipo_instalacao IS NOT NULL
                        """))
                        db.session.commit()
                    except Exception:
                        pass
                        
        except Exception as e:
            db.session.rollback()
            print(f" ⚠ Aviso na migração de projeto_solar: {e}")
        
        # Migração: adicionar colunas largura e comprimento em placa_solar
        try:
            from sqlalchemy import text, inspect
            inspector = inspect(db.engine)
            
            if 'placa_solar' in inspector.get_table_names():
                colunas_existentes = [col['name'] for col in inspector.get_columns('placa_solar')]
                
                campos_dimensoes = {
                    'largura': 'DOUBLE PRECISION',
                    'comprimento': 'DOUBLE PRECISION'
                }
                
                campos_adicionados = []
                for campo, tipo in campos_dimensoes.items():
                    if campo not in colunas_existentes:
                        try:
                            db.session.execute(text(f"ALTER TABLE placa_solar ADD COLUMN {campo} {tipo}"))
                            campos_adicionados.append(campo)
                        except Exception:
                            pass
                
                if campos_adicionados:
                    db.session.commit()
                    print(f"[OK] {len(campos_adicionados)} colunas de dimensão adicionadas em placa_solar: {', '.join(campos_adicionados)}")
                        
        except Exception as e:
            db.session.rollback()
            print(f" ⚠ Aviso na migração de placa_solar: {e}")
        
        # Migração: adicionar coluna horas_improdutivas_percentual
        try:
            from sqlalchemy import text, inspect
            inspector = inspect(db.engine)
            
            if 'config_precificacao' in inspector.get_table_names():
                colunas_existentes = [col['name'] for col in inspector.get_columns('config_precificacao')]
                
                if 'horas_improdutivas_percentual' not in colunas_existentes:
                    db.session.execute(text("ALTER TABLE config_precificacao ADD COLUMN horas_improdutivas_percentual FLOAT DEFAULT 20.0"))
                    db.session.commit()
                    print("[OK] Coluna horas_improdutivas_percentual adicionada!")
        except Exception as e:
            db.session.rollback()
            print(f" ⚠ Aviso na migração de precificação: {e}")
        
        # Corrige ordens de serviço (migração automática de status)
        # TEMPORARIAMENTE DESABILITADO PARA CRIAR BANCO LIMPO
        # try:
        #     from scripts.corrigir_ordens_servico_render import corrigir_ordens_servico
        #     corrigir_ordens_servico()
        # except Exception as e:
        #     print(f" ⚠ Aviso na correção de OS: {e}")

    return app

def popular_banco_se_vazio():
    """Sincroniza dados do erp.db local com o banco Render"""
    from app.ordem_servico.ordem_servico_model import OrdemServico
    from app.cliente.cliente_model import Cliente
    import os
    import sqlite3
    from datetime import datetime
    
    try:
        if not os.path.exists('erp.db'):
            print("⚠️ erp.db não encontrado - pulando sincronização")
            return
        
        print("🔄 Verificando sincronização com erp.db...")
        
        total_os = OrdemServico.query.count()
        print(f"📊 OS no banco Render: {total_os}")
        
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
        
        # Busca OS existentes no Render (por número)
        os_existentes = {os.numero: os for os in OrdemServico.query.all()}
        
        # Importa/Atualiza OS do erp.db
        ordens = cursor.execute("SELECT * FROM ordem_servico WHERE ativo = 1 ORDER BY id").fetchall()
        importadas = 0
        atualizadas = 0
        puladas = 0
        
        for row in ordens:
            numero_os = row['numero']
            
            # Verifica se já existe
            if numero_os in os_existentes:
                puladas += 1
                continue
            
            # Mapeia cliente
            cliente_id_render = mapa_clientes.get(row['cliente_id'])
            if not cliente_id_render:
                print(f"   ⚠️ Cliente local {row['cliente_id']} não encontrado - pulando OS {numero_os}")
                continue
            
            # Cria nova OS
            nova_os = OrdemServico(
                numero=numero_os,
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
        
        if importadas > 0:
            db.session.commit()
            print(f"✅ Sincronização: {importadas} novas OS importadas, {puladas} já existentes")
        else:
            print(f"✅ Banco sincronizado: {puladas} OS já existem")
        
        conn.close()
        
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

    # Blueprint de equipamentos
    from app.equipamento.equipamento_routes import equipamento_bp
    app.register_blueprint(equipamento_bp)

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

    # Blueprint de energia solar
    from app.energia_solar.energia_solar_routes import energia_solar_bp
    app.register_blueprint(energia_solar_bp)

    # Blueprint de concessionárias
    from app.concessionaria.concessionaria_routes import concessionaria_bp
    app.register_blueprint(concessionaria_bp, url_prefix='/concessionarias')

    # Blueprint de kits do distribuidor (opcional - requer configuração de API)
    try:
        from app.kits_distribuidor.kits_routes import kits_bp
        app.register_blueprint(kits_bp, url_prefix='/kits-distribuidor')
        print("[OK] Blueprint kits_distribuidor registrado")
    except Exception as e:
        print(f" ⚠ Módulo kits_distribuidor não disponível: {e}")
        import traceback
        traceback.print_exc()

    # Blueprint de propostas
    from app.proposta.proposta_routes import proposta_bp
    app.register_blueprint(proposta_bp, url_prefix='/propostas')
    
    # Blueprint admin (migrações e manutenção)
    from app.admin.admin_routes import admin_bp
    app.register_blueprint(admin_bp)
    
    # Blueprint de status do sistema
    from app.status_routes import status_bp
    app.register_blueprint(status_bp)
    
    # Blueprint de diagnóstico do sistema
    try:
        from app.diagnostico_routes import diagnostico_bp
        app.register_blueprint(diagnostico_bp)
        print("[OK] Blueprint de diagnóstico registrado")
    except Exception as e:
        print(f"⚠️ Módulo diagnóstico não disponível: {e}")
    
    # Blueprint de debug (apenas para desenvolvimento/troubleshooting)
    try:
        from app.debug_routes import debug_bp
        app.register_blueprint(debug_bp)
        print("[OK] Blueprint de debug registrado")
    except Exception as e:
        print(f"⚠️ Módulo debug não disponível: {e}")


def register_auxiliary_routes(app):
    """
    Registra rotas auxiliares do sistema.
    
    Args:
        app: Instância da aplicação Flask
    """
    from flask import send_from_directory, jsonify
    import os
    
    @app.route('/uploads/<path:filename>')
    def uploaded_file(filename):
        """Serve arquivos de upload."""
        uploads_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static', 'uploads')
        return send_from_directory(uploads_dir, filename)
    
    @app.route('/offline.html')
    def offline():
        """Página offline para PWA."""
        return render_template('offline.html')
    
    @app.route('/manifest.json')
    def manifest():
        """Serve o manifest.json para PWA."""
        static_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'app', 'static')
        return send_from_directory(static_dir, 'manifest.json', mimetype='application/manifest+json')
    
    @app.route('/service-worker.js')
    def service_worker():
        """Serve o service worker para PWA."""
        static_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'app', 'static')
        return send_from_directory(static_dir, 'service-worker.js', mimetype='application/javascript')

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
    def inject_config_global():
        """Injeta a configuração principal (`config`) em todos os templates.

        Usa `get_config()` para obter a configuração atual e retorna como `config`.
        Isto permite que o `base.html` e outros templates acessem `config.logo_base64`.
        """
        try:
            from app.configuracao.configuracao_utils import get_config
            cfg = get_config()
            return {'config': cfg}
        except Exception:
            return {'config': None}
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