# -*- coding: utf-8 -*-
"""
Rota temporária para testes de autocomplete
"""
from flask import Blueprint, render_template, has_app_context
from jinja2 import TemplateNotFound

teste_bp = Blueprint('teste', __name__)

@teste_bp.route('/teste-autocomplete-fornecedor')
def pagina_autocomplete_fornecedor():
    """Página de teste para verificar autocomplete de CNPJ"""
    if not has_app_context():
        from app import create_app

        app = create_app('testing')
        with app.app_context():
            try:
                return render_template('teste_autocomplete_fornecedor.html')
            except TemplateNotFound:
                return '<h1>Template de teste não disponível</h1>', 200
    try:
        return render_template('teste_autocomplete_fornecedor.html')
    except TemplateNotFound:
        return '<h1>Template de teste não disponível</h1>', 200
