# -*- coding: utf-8 -*-
"""
Rota de Diagnóstico do Sistema
================================
Endpoint público para verificar status do sistema no Render
"""

from flask import Blueprint, jsonify
from datetime import datetime
import os
import sys

diagnostico_bp = Blueprint('diagnostico', __name__)

@diagnostico_bp.route('/diagnostico/status')
def status_sistema():
    """Retorna informações sobre o sistema e última atualização."""
    
    # Versão do Python
    python_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    
    # Variáveis de ambiente importantes (sem expor senhas)
    is_render = os.environ.get('RENDER', 'False') == 'True'
    ambiente = os.environ.get('FLASK_ENV', 'production')
    
    # Timestamp do arquivo cliente_routes para ver última modificação
    try:
        from app.cliente import cliente_routes
        routes_file = cliente_routes.__file__
        mtime = os.path.getmtime(routes_file)
        ultima_atualizacao = datetime.fromtimestamp(mtime).strftime('%Y-%m-%d %H:%M:%S')
    except:
        ultima_atualizacao = 'Desconhecido'
    
    # Verificar se correção está aplicada
    correcao_aplicada = False
    try:
        import inspect
        from app.cliente.cliente_routes import visualizar
        codigo_fonte = inspect.getsource(visualizar)
        # Verifica se tem a nova lógica de verificação
        correcao_aplicada = 'filter_by(id=id, ativo=True)' in codigo_fonte
    except:
        pass
    
    return jsonify({
        'status': 'online',
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC'),
        'ambiente': ambiente,
        'python_version': python_version,
        'is_render': is_render,
        'ultima_atualizacao_routes': ultima_atualizacao,
        'correcao_404_aplicada': correcao_aplicada,
        'mensagem': 'Sistema operacional' if correcao_aplicada else 'Deploy em andamento'
    })

@diagnostico_bp.route('/diagnostico/teste-cliente-20')
def teste_cliente_20():
    """Testa especificamente a rota do cliente 20."""
    from app.cliente.cliente_model import Cliente
    
    # Verifica se cliente 20 existe
    cliente = Cliente.query.filter_by(id=20).first()
    
    if cliente:
        return jsonify({
            'existe': True,
            'id': cliente.id,
            'nome': cliente.nome,
            'ativo': cliente.ativo
        })
    else:
        return jsonify({
            'existe': False,
            'mensagem': 'Cliente 20 não encontrado (comportamento esperado)',
            'rota_deveria': 'Redirecionar para /cliente/listar com mensagem de erro'
        })
