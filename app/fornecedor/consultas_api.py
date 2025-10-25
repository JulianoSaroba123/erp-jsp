# -*- coding: utf-8 -*-
"""
ERP JSP v3.0 - Rotas de Consulta Automática - Fornecedores
=========================================================

Rotas para consulta automática de CNPJ e CEP para fornecedores.

Autor: JSP Soluções
Data: 2025
"""

import requests
import re
from flask import jsonify
from app.fornecedor.fornecedor_routes import fornecedor_bp


@fornecedor_bp.route('/api/consultar-cnpj/<cnpj>')
def consultar_cnpj(cnpj):
    """Consulta dados da empresa via CNPJ usando a API ReceitaWS."""
    try:
        # Remove formatação do CNPJ
        cnpj_limpo = re.sub(r'[^0-9]', '', cnpj)
        
        if len(cnpj_limpo) != 14:
            return jsonify({'success': False, 'error': 'CNPJ deve ter 14 dígitos'}), 400
        
        # Consulta API ReceitaWS
        url = f'https://www.receitaws.com.br/v1/cnpj/{cnpj_limpo}'
        response = requests.get(url, timeout=10)
        
        if response.status_code != 200:
            return jsonify({'success': False, 'error': 'Erro ao consultar CNPJ'}), 500
        
        data = response.json()
        
        if data.get('status') == 'ERROR':
            return jsonify({'success': False, 'error': data.get('message', 'CNPJ não encontrado')}), 404
        
        # Formata os dados para retornar
        resultado = {
            'success': True,
            'data': {
                'nome': data.get('nome', ''),
                'nome_fantasia': data.get('fantasia', ''),
                'cnpj': data.get('cnpj', ''),
                'situacao': data.get('situacao', ''),
                'email': data.get('email', ''),
                'telefone': data.get('telefone', ''),
                'endereco': {
                    'logradouro': data.get('logradouro', ''),
                    'numero': data.get('numero', ''),
                    'complemento': data.get('complemento', ''),
                    'bairro': data.get('bairro', ''),
                    'cidade': data.get('municipio', ''),
                    'uf': data.get('uf', ''),
                    'cep': data.get('cep', '')
                }
            }
        }
        
        return jsonify(resultado)
        
    except Exception as e:
        return jsonify({'success': False, 'error': 'Erro interno do servidor'}), 500


@fornecedor_bp.route('/api/consultar-cep/<cep>')
def consultar_cep(cep):
    """Consulta endereço via CEP usando a API ViaCEP."""
    try:
        # Remove formatação do CEP
        cep_limpo = re.sub(r'[^0-9]', '', cep)
        
        if len(cep_limpo) != 8:
            return jsonify({'success': False, 'error': 'CEP deve ter 8 dígitos'}), 400
        
        # Consulta API ViaCEP
        url = f'https://viacep.com.br/ws/{cep_limpo}/json/'
        response = requests.get(url, timeout=10)
        
        if response.status_code != 200:
            return jsonify({'success': False, 'error': 'Erro ao consultar CEP'}), 500
        
        data = response.json()
        
        if data.get('erro'):
            return jsonify({'success': False, 'error': 'CEP não encontrado'}), 404
        
        # Formata os dados para retornar
        resultado = {
            'success': True,
            'data': {
                'cep': data.get('cep', ''),
                'logradouro': data.get('logradouro', ''),
                'complemento': data.get('complemento', ''),
                'bairro': data.get('bairro', ''),
                'cidade': data.get('localidade', ''),
                'uf': data.get('uf', '')
            }
        }
        
        return jsonify(resultado)
        
    except Exception as e:
        return jsonify({'success': False, 'error': 'Erro interno do servidor'}), 500