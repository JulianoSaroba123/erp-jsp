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
    
    Exibe estatísticas gerais, financeiras e navegação rápida.
    """
    try:
        # Importa models apenas quando necessário para evitar imports circulares
        from app.cliente.cliente_model import Cliente
        from app.fornecedor.fornecedor_model import Fornecedor
        from app.produto.produto_model import Produto
        from app.ordem_servico.ordem_servico_model import OrdemServico
        from app.financeiro.financeiro_utils import calcular_metricas_dashboard, formatar_valor_real
        
        # === ESTATÍSTICAS BÁSICAS ===
        stats_basicas = {
            'total_clientes': Cliente.query.filter_by(ativo=True).count(),
            'total_fornecedores': Fornecedor.query.filter_by(ativo=True).count(),
            'total_produtos': Produto.query.filter_by(ativo=True).count(),
            'produtos_estoque_baixo': len(Produto.produtos_estoque_baixo()),
        }
        
        # === MÉTRICAS FINANCEIRAS INTEGRADAS ===
        try:
            metricas_financeiras = calcular_metricas_dashboard()
        except Exception as e:
            print(f"⚠️ Erro ao calcular métricas financeiras: {e}")
            metricas_financeiras = {
                'total_ordens': 0, 'ordens_abertas': 0, 'ordens_concluidas': 0,
                'valor_total_ordens': 0, 'valor_ordens_concluidas': 0, 'valor_ordens_abertas': 0,
                'receita_mes': 0, 'qtd_ordens_mes': 0,
                'total_receitas_mes': 0, 'total_despesas_mes': 0, 'saldo_mes': 0,
                'total_contas_receber': 0, 'total_contas_pagar': 0,
                'qtd_contas_receber': 0, 'qtd_contas_pagar': 0,
                'fluxo_caixa': 0
            }
        
        # === COMBINAR ESTATÍSTICAS ===
        stats = {**stats_basicas, **metricas_financeiras}
        
        # === DADOS AUXILIARES ===
        # Clientes recentes (últimos 5)
        clientes_recentes = Cliente.query.filter_by(ativo=True).order_by(
            Cliente.criado_em.desc()
        ).limit(5).all()
        
        # Produtos com estoque baixo
        produtos_estoque_baixo = Produto.produtos_estoque_baixo()[:5]
        
        # Ordens de serviço recentes (últimas 5)
        ordens_recentes = OrdemServico.query.filter_by(ativo=True).order_by(
            OrdemServico.criado_em.desc()
        ).limit(5).all()
        
        # Valor total do estoque
        produtos_com_estoque = Produto.query.filter(
            Produto.ativo == True,
            Produto.controla_estoque == True,
            Produto.preco_custo.isnot(None)
        ).all()
        
        valor_total_estoque = sum([p.valor_estoque for p in produtos_com_estoque])
        stats['valor_estoque'] = valor_total_estoque
        
        # === FORMATAÇÃO DE VALORES ===
        # Formatar valores para exibição no template
        stats['valor_total_ordens_fmt'] = formatar_valor_real(stats['valor_total_ordens'])
        stats['valor_ordens_concluidas_fmt'] = formatar_valor_real(stats['valor_ordens_concluidas'])
        stats['valor_ordens_abertas_fmt'] = formatar_valor_real(stats['valor_ordens_abertas'])
        stats['receita_mes_fmt'] = formatar_valor_real(stats['receita_mes'])
        stats['total_receitas_mes_fmt'] = formatar_valor_real(stats['total_receitas_mes'])
        stats['total_despesas_mes_fmt'] = formatar_valor_real(stats['total_despesas_mes'])
        stats['saldo_mes_fmt'] = formatar_valor_real(stats['saldo_mes'])
        stats['total_contas_receber_fmt'] = formatar_valor_real(stats['total_contas_receber'])
        stats['total_contas_pagar_fmt'] = formatar_valor_real(stats['total_contas_pagar'])
        stats['fluxo_caixa_fmt'] = formatar_valor_real(stats['fluxo_caixa'])
        stats['valor_estoque_fmt'] = formatar_valor_real(valor_total_estoque)
        
        # === CORES PARA INDICADORES ===
        # Cor do saldo (verde se positivo, vermelho se negativo)
        stats['saldo_mes_cor'] = 'success' if stats['saldo_mes'] >= 0 else 'danger'
        stats['fluxo_caixa_cor'] = 'success' if stats['fluxo_caixa'] >= 0 else 'danger'
        
        return render_template('painel/dashboard.html',
                             stats=stats,
                             clientes_recentes=clientes_recentes,
                             produtos_estoque_baixo=produtos_estoque_baixo,
                             ordens_recentes=ordens_recentes)
        
    except Exception as e:
        print(f" Erro no dashboard: {e}")
        # Em caso de erro, exibe dashboard básico
        stats = {
            'total_clientes': 0, 'total_fornecedores': 0, 'total_produtos': 0,
            'produtos_estoque_baixo': 0, 'valor_estoque': 0,
            'total_ordens': 0, 'ordens_abertas': 0, 'ordens_concluidas': 0,
            'valor_total_ordens': 0, 'valor_ordens_concluidas': 0, 'valor_ordens_abertas': 0,
            'receita_mes': 0, 'qtd_ordens_mes': 0,
            'total_receitas_mes': 0, 'total_despesas_mes': 0, 'saldo_mes': 0,
            'total_contas_receber': 0, 'total_contas_pagar': 0,
            'qtd_contas_receber': 0, 'qtd_contas_pagar': 0, 'fluxo_caixa': 0,
            # Valores formatados zerados
            'valor_total_ordens_fmt': 'R$ 0,00', 'valor_ordens_concluidas_fmt': 'R$ 0,00',
            'valor_ordens_abertas_fmt': 'R$ 0,00', 'receita_mes_fmt': 'R$ 0,00',
            'total_receitas_mes_fmt': 'R$ 0,00', 'total_despesas_mes_fmt': 'R$ 0,00',
            'saldo_mes_fmt': 'R$ 0,00', 'total_contas_receber_fmt': 'R$ 0,00',
            'total_contas_pagar_fmt': 'R$ 0,00', 'fluxo_caixa_fmt': 'R$ 0,00',
            'valor_estoque_fmt': 'R$ 0,00',
            # Cores
            'saldo_mes_cor': 'secondary', 'fluxo_caixa_cor': 'secondary'
        }
        
        return render_template('painel/dashboard.html',
                             stats=stats,
                             clientes_recentes=[],
                             produtos_estoque_baixo=[],
                             ordens_recentes=[],
                             erro_banco=True)

@painel_bp.route('/sobre')
def sobre():
    """Página sobre o sistema."""
    return render_template('painel/sobre.html')

@painel_bp.route('/configuracoes')
def configuracoes():
    """Página de configurações do sistema."""
    return render_template('painel/configuracoes.html')