"""
🔍 Endpoint de Status do Sistema
=================================

Verifica se todas as correções foram aplicadas.
"""

from flask import Blueprint, jsonify
from app.extensoes import db
from sqlalchemy import text

status_bp = Blueprint('status', __name__, url_prefix='/status')

@status_bp.route('/sistema')
def status_sistema():
    """Retorna status completo do sistema"""
    resultado = {
        'banco': {},
        'correcoes': {},
        'tabelas': {}
    }
    
    try:
        # 1. Verifica conexão
        db.session.execute(text("SELECT 1"))
        resultado['banco']['conectado'] = True
        
        # 2. Verifica tabelas principais
        tabelas_principais = ['ordem_servico', 'clientes', 'propostas', 'produtos']
        
        for tabela in tabelas_principais:
            try:
                # Total geral
                query_total = text(f"SELECT COUNT(*) FROM {tabela}")
                total = db.session.execute(query_total).scalar()
                
                # Total ativo=TRUE
                query_ativo = text(f"SELECT COUNT(*) FROM {tabela} WHERE ativo = TRUE")
                ativo = db.session.execute(query_ativo).scalar()
                
                # Total ativo=NULL
                query_null = text(f"SELECT COUNT(*) FROM {tabela} WHERE ativo IS NULL")
                nulo = db.session.execute(query_null).scalar()
                
                resultado['tabelas'][tabela] = {
                    'total': total,
                    'ativo_true': ativo,
                    'ativo_null': nulo,
                    'ok': nulo == 0
                }
            except:
                resultado['tabelas'][tabela] = {'erro': 'Tabela não existe ou sem coluna ativo'}
        
        # 3. Status específico de ordem_servico
        try:
            query_status = text("SELECT status, COUNT(*) FROM ordem_servico WHERE ativo = TRUE GROUP BY status")
            status_os = db.session.execute(query_status).fetchall()
            resultado['correcoes']['status_ordem_servico'] = {row[0]: row[1] for row in status_os}
        except:
            resultado['correcoes']['status_ordem_servico'] = {'erro': 'Não foi possível verificar'}
        
        # 4. Resumo
        total_nulls = sum(t.get('ativo_null', 0) for t in resultado['tabelas'].values() if isinstance(t, dict))
        resultado['correcoes']['executada'] = total_nulls == 0
        resultado['correcoes']['pendencias'] = total_nulls
        
        resultado['status'] = 'sucesso'
        
    except Exception as e:
        resultado['status'] = 'erro'
        resultado['erro'] = str(e)
    
    return jsonify(resultado)

@status_bp.route('/ordem_servico')
def status_ordem_servico():
    """Status detalhado das ordens de serviço"""
    try:
        # Total
        total = db.session.execute(text("SELECT COUNT(*) FROM ordem_servico")).scalar()
        
        # Por ativo
        ativo_true = db.session.execute(text("SELECT COUNT(*) FROM ordem_servico WHERE ativo = TRUE")).scalar()
        ativo_false = db.session.execute(text("SELECT COUNT(*) FROM ordem_servico WHERE ativo = FALSE")).scalar()
        ativo_null = db.session.execute(text("SELECT COUNT(*) FROM ordem_servico WHERE ativo IS NULL")).scalar()
        
        # Por status
        status_dist = db.session.execute(text("SELECT status, COUNT(*) FROM ordem_servico GROUP BY status")).fetchall()
        
        # Primeiras 5
        primeiras = db.session.execute(text("SELECT numero, titulo, status, ativo FROM ordem_servico LIMIT 5")).fetchall()
        
        return jsonify({
            'total': total,
            'ativo': {
                'true': ativo_true,
                'false': ativo_false,
                'null': ativo_null
            },
            'status': {row[0]: row[1] for row in status_dist},
            'primeiras_5': [
                {'numero': row[0], 'titulo': row[1], 'status': row[2], 'ativo': row[3]}
                for row in primeiras
            ],
            'correcao_necessaria': ativo_null > 0 or ativo_false > 0
        })
    except Exception as e:
        return jsonify({'erro': str(e)}), 500
