# -*- coding: utf-8 -*-
"""
Rota temporária para testes de autocomplete
"""
from flask import Blueprint, render_template

teste_bp = Blueprint('teste', __name__)

@teste_bp.route('/teste-autocomplete-fornecedor')
def teste_autocomplete():
    """Página de teste para verificar autocomplete de CNPJ"""
    return render_template('teste_autocomplete_fornecedor.html')
