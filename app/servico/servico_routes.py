# -*- coding: utf-8 -*-
"""
ERP JSP v3.0 - Routes de Serviços
=================================

Rotas para gerenciamento de serviços.

Autor: JSP Soluções
Data: 2025
"""

from flask import Blueprint, render_template

# Cria o blueprint
servico_bp = Blueprint('servico', __name__, template_folder='templates')

@servico_bp.route('/')
@servico_bp.route('/dashboard')
def dashboard():
    """Dashboard de serviços."""
    return render_template('servico/dashboard.html')