# -*- coding: utf-8 -*-
"""
Endpoint admin para executar migrações no banco de dados
"""

from flask import Blueprint, jsonify
from app.extensoes import db
from sqlalchemy import text

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

@admin_bp.route('/migrate-add-conteudo', methods=['GET'])
def migrate_add_conteudo():
    """
    Adiciona coluna conteudo BYTEA na tabela ordem_servico_anexos
    Acesse: https://erp-jsp-th5o.onrender.com/admin/migrate-add-conteudo
    """
    try:
        # Verifica se a coluna já existe
        check_sql = text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'ordem_servico_anexos' 
            AND column_name = 'conteudo';
        """)
        
        result = db.session.execute(check_sql).fetchone()
        
        if result:
            return jsonify({
                'success': True,
                'message': '✅ Coluna conteudo já existe!',
                'status': 'already_exists'
            }), 200
        
        # Adiciona a coluna
        add_column_sql = text("""
            ALTER TABLE ordem_servico_anexos 
            ADD COLUMN conteudo BYTEA;
        """)
        
        db.session.execute(add_column_sql)
        db.session.commit()
        
        # Verifica novamente
        result_after = db.session.execute(check_sql).fetchone()
        
        if result_after:
            return jsonify({
                'success': True,
                'message': '✅ Coluna conteudo adicionada com sucesso!',
                'status': 'created',
                'column_info': {
                    'name': result_after[0],
                    'type': 'BYTEA'
                }
            }), 200
        else:
            return jsonify({
                'success': False,
                'message': '❌ Coluna não foi criada',
                'status': 'failed'
            }), 500
            
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'❌ Erro: {str(e)}',
            'status': 'error'
        }), 500

@admin_bp.route('/check-database', methods=['GET'])
def check_database():
    """
    Verifica estrutura da tabela ordem_servico_anexos
    Acesse: https://erp-jsp-th5o.onrender.com/admin/check-database
    """
    try:
        sql = text("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns 
            WHERE table_name = 'ordem_servico_anexos'
            ORDER BY ordinal_position;
        """)
        
        result = db.session.execute(sql).fetchall()
        
        columns = []
        for row in result:
            columns.append({
                'name': row[0],
                'type': row[1],
                'nullable': row[2]
            })
        
        return jsonify({
            'success': True,
            'table': 'ordem_servico_anexos',
            'columns': columns,
            'total_columns': len(columns)
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'❌ Erro: {str(e)}'
        }), 500
