"""
Rota para autocomplete de campos de ordem de serviço
"""
from flask import Blueprint, jsonify
from app.ordem_servico.ordem_servico_model import OrdemServico
from app.extensoes import db
from sqlalchemy import distinct

@ordem_servico_bp.route('/autocomplete/<campo>')
def autocomplete_campo(campo):
    """
    Retorna valores únicos já usados para autocomplete.
    
    Campos suportados:
    - solicitante
    - tecnico_responsavel
    - titulo
    - equipamento
    - marca_modelo
    """
    campos_permitidos = {
        'solicitante': OrdemServico.solicitante,
        'tecnico_responsavel': OrdemServico.tecnico_responsavel,
        'titulo': OrdemServico.titulo,
        'equipamento': OrdemServico.equipamento,
        'marca_modelo': OrdemServico.marca_modelo
    }
    
    if campo not in campos_permitidos:
        return jsonify({'error': 'Campo não permitido'}), 400
    
    try:
        coluna = campos_permitidos[campo]
        
        # Busca valores únicos e remove nulos/vazios
        valores = db.session.query(distinct(coluna))\\
            .filter(coluna.isnot(None), coluna != '')\\
            .order_by(coluna)\\
            .limit(50)\\
            .all()
        
        # Extrai os valores da tupla
        resultado = [v[0] for v in valores if v[0]]
        
        return jsonify(resultado)
        
    except Exception as e:
        print(f"Erro ao buscar autocomplete para {campo}: {e}")
        return jsonify([])
