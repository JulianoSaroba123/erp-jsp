# -*- coding: utf-8 -*-
"""
ERP JSP v3.0 - Routes do Painel
================================

Rotas para o dashboard e páginas principais.
Inclui estatísticas e visão geral do sistema.

Autor: JSP Soluções
Data: 2025
"""

from flask import Blueprint, render_template, redirect, url_for
from flask_login import login_required, current_user
from app.extensoes import db

# Cria o blueprint
painel_bp = Blueprint('painel', __name__, template_folder='templates')

@painel_bp.route('/')
def index():
    """
    Página inicial - redireciona para login ou dashboard.
    """
    if current_user.is_authenticated:
        return redirect(url_for('painel.dashboard'))
    return redirect(url_for('auth.login'))

@painel_bp.route('/dashboard')
@login_required
def dashboard():
    """
    Dashboard principal do sistema.
    
    Exibe estatísticas gerais e navegação rápida.
    """
    try:
        # Importa models apenas quando necessário para evitar imports circulares
        from app.cliente.cliente_model import Cliente
        from app.fornecedor.fornecedor_model import Fornecedor
        from app.produto.produto_model import Produto
        
        # Estatísticas básicas
        stats = {
            'total_clientes': Cliente.query.filter_by(ativo=True).count(),
            'total_fornecedores': Fornecedor.query.filter_by(ativo=True).count(),
            'total_produtos': Produto.query.filter_by(ativo=True).count(),
            'produtos_estoque_baixo': len(Produto.produtos_estoque_baixo()),
        }
        
        # Clientes recentes (últimos 5)
        clientes_recentes = Cliente.query.filter_by(ativo=True).order_by(
            Cliente.criado_em.desc()
        ).limit(5).all()
        
        # Produtos com estoque baixo
        produtos_estoque_baixo = Produto.produtos_estoque_baixo()[:5]
        
        # Valor total do estoque
        produtos_com_estoque = Produto.query.filter(
            Produto.ativo == True,
            Produto.controla_estoque == True,
            Produto.preco_custo.isnot(None)
        ).all()
        
        valor_total_estoque = sum([p.valor_estoque for p in produtos_com_estoque])
        
        stats['valor_estoque'] = valor_total_estoque
        
        return render_template('painel/dashboard.html',
                             stats=stats,
                             clientes_recentes=clientes_recentes,
                             produtos_estoque_baixo=produtos_estoque_baixo)
        
    except Exception as e:
        # Em caso de erro (ex: tabelas não criadas ainda), exibe dashboard básico
        stats = {
            'total_clientes': 0,
            'total_fornecedores': 0,
            'total_produtos': 0,
            'produtos_estoque_baixo': 0,
            'valor_estoque': 0
        }
        
        return render_template('painel/dashboard.html',
                             stats=stats,
                             clientes_recentes=[],
                             produtos_estoque_baixo=[],
                             erro_banco=True)

@painel_bp.route('/sobre')
def sobre():
    """Página sobre o sistema."""
    return render_template('painel/sobre.html')

@painel_bp.route('/configuracoes')
def configuracoes():
    """Página de configurações do sistema."""
    return render_template('painel/configuracoes.html')