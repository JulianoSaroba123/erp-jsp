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


@painel_bp.route('/importar-dados', methods=['GET', 'POST'])
@login_required
def importar_dados():
    """
    Importa dados de um arquivo JSON exportado do SQLite local.
    Apenas admin pode usar.
    """
    from flask import request, flash, jsonify
    import json
    
    # Apenas admin
    if current_user.tipo_usuario != 'admin':
        flash('Acesso negado. Apenas administradores.', 'error')
        return redirect(url_for('painel.dashboard'))
    
    if request.method == 'GET':
        return '''
        <!DOCTYPE html>
        <html>
        <head>
            <title>Importar Dados - ERP JSP</title>
            <style>
                body { font-family: Arial; background: #0a1929; color: #fff; padding: 40px; }
                .container { max-width: 600px; margin: 0 auto; }
                h1 { color: #00d4ff; }
                form { background: #1a2d42; padding: 30px; border-radius: 10px; }
                input[type=file] { margin: 20px 0; }
                button { background: #00d4ff; color: #000; padding: 15px 30px; border: none; 
                         border-radius: 5px; cursor: pointer; font-size: 16px; }
                button:hover { background: #00b8e6; }
                .warning { background: #ffcc00; color: #000; padding: 15px; border-radius: 5px; margin-bottom: 20px; }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>📦 Importar Dados</h1>
                <div class="warning">
                    ⚠️ Esta ação irá importar dados do arquivo JSON para o banco de dados.
                    Dados existentes podem ser sobrescritos!
                </div>
                <form method="POST" enctype="multipart/form-data">
                    <p>Selecione o arquivo <strong>dados_para_render.json</strong>:</p>
                    <input type="file" name="arquivo" accept=".json" required>
                    <br><br>
                    <button type="submit">🚀 Importar Dados</button>
                </form>
                <br>
                <a href="/dashboard" style="color: #00d4ff;">← Voltar ao Dashboard</a>
            </div>
        </body>
        </html>
        '''
    
    # POST - processa importação
    try:
        arquivo = request.files.get('arquivo')
        if not arquivo:
            flash('Nenhum arquivo enviado.', 'error')
            return redirect(url_for('painel.importar_dados'))
        
        dados = json.load(arquivo)
        resultados = []
        
        # Mapeia tabelas para models
        from app.cliente.cliente_model import Cliente
        from app.fornecedor.fornecedor_model import Fornecedor
        from app.produto.produto_model import Produto
        from app.ordem_servico.ordem_servico_model import OrdemServico, OrdemServicoItem, OrdemServicoAnexo
        from app.proposta.proposta_model import Proposta
        
        # Importa clientes
        if 'clientes' in dados:
            count = 0
            for row in dados['clientes']['rows']:
                if not Cliente.query.filter_by(id=row.get('id')).first():
                    cliente = Cliente()
                    for col, val in row.items():
                        if hasattr(cliente, col) and col != 'id':
                            setattr(cliente, col, val)
                    db.session.add(cliente)
                    count += 1
            db.session.commit()
            resultados.append(f"Clientes: {count} importados")
        
        # Importa fornecedores
        if 'fornecedores' in dados:
            count = 0
            for row in dados['fornecedores']['rows']:
                if not Fornecedor.query.filter_by(id=row.get('id')).first():
                    obj = Fornecedor()
                    for col, val in row.items():
                        if hasattr(obj, col) and col != 'id':
                            setattr(obj, col, val)
                    db.session.add(obj)
                    count += 1
            db.session.commit()
            resultados.append(f"Fornecedores: {count} importados")
        
        # Importa produtos
        if 'produtos' in dados:
            count = 0
            for row in dados['produtos']['rows']:
                if not Produto.query.filter_by(id=row.get('id')).first():
                    obj = Produto()
                    for col, val in row.items():
                        if hasattr(obj, col) and col != 'id':
                            setattr(obj, col, val)
                    db.session.add(obj)
                    count += 1
            db.session.commit()
            resultados.append(f"Produtos: {count} importados")
        
        # Importa ordens de serviço
        if 'ordem_servico' in dados:
            count = 0
            for row in dados['ordem_servico']['rows']:
                if not OrdemServico.query.filter_by(id=row.get('id')).first():
                    obj = OrdemServico()
                    for col, val in row.items():
                        if hasattr(obj, col) and col != 'id':
                            setattr(obj, col, val)
                    db.session.add(obj)
                    count += 1
            db.session.commit()
            resultados.append(f"Ordens de Serviço: {count} importadas")
        
        # Importa propostas
        if 'propostas' in dados:
            count = 0
            for row in dados['propostas']['rows']:
                if not Proposta.query.filter_by(id=row.get('id')).first():
                    obj = Proposta()
                    for col, val in row.items():
                        if hasattr(obj, col) and col != 'id':
                            setattr(obj, col, val)
                    db.session.add(obj)
                    count += 1
            db.session.commit()
            resultados.append(f"Propostas: {count} importadas")
        
        flash('✅ Importação concluída! ' + ' | '.join(resultados), 'success')
        return redirect(url_for('painel.dashboard'))
        
    except Exception as e:
        db.session.rollback()
        flash(f'❌ Erro na importação: {str(e)}', 'error')
        return redirect(url_for('painel.importar_dados'))


@painel_bp.route('/importar-auto')
@login_required
def importar_auto():
    """
    Importa dados automaticamente do arquivo JSON no repositório.
    Apenas admin pode usar.
    """
    import json
    import os
    from flask import flash
    
    # Apenas admin
    if current_user.tipo_usuario != 'admin':
        flash('Acesso negado. Apenas administradores.', 'error')
        return redirect(url_for('painel.dashboard'))
    
    try:
        # Caminho do arquivo JSON
        json_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'dados_para_render.json')
        
        if not os.path.exists(json_path):
            flash('❌ Arquivo dados_para_render.json não encontrado!', 'error')
            return redirect(url_for('painel.dashboard'))
        
        with open(json_path, 'r', encoding='utf-8') as f:
            dados = json.load(f)
        
        resultados = []
        
        # Importa models
        from app.cliente.cliente_model import Cliente
        from app.fornecedor.fornecedor_model import Fornecedor
        from app.produto.produto_model import Produto
        from app.ordem_servico.ordem_servico_model import OrdemServico
        from app.proposta.proposta_model import Proposta
        
        # Importa clientes
        if 'clientes' in dados:
            count = 0
            for row in dados['clientes']['rows']:
                exists = Cliente.query.filter_by(cpf_cnpj=row.get('cpf_cnpj')).first() if row.get('cpf_cnpj') else None
                if not exists:
                    cliente = Cliente()
                    for col, val in row.items():
                        if hasattr(cliente, col) and col != 'id':
                            setattr(cliente, col, val)
                    db.session.add(cliente)
                    count += 1
            db.session.commit()
            resultados.append(f"✅ Clientes: {count}")
        
        # Importa fornecedores
        if 'fornecedores' in dados:
            count = 0
            for row in dados['fornecedores']['rows']:
                exists = Fornecedor.query.filter_by(cnpj=row.get('cnpj')).first() if row.get('cnpj') else None
                if not exists:
                    obj = Fornecedor()
                    for col, val in row.items():
                        if hasattr(obj, col) and col != 'id':
                            setattr(obj, col, val)
                    db.session.add(obj)
                    count += 1
            db.session.commit()
            resultados.append(f"✅ Fornecedores: {count}")
        
        # Importa produtos
        if 'produtos' in dados:
            count = 0
            for row in dados['produtos']['rows']:
                exists = Produto.query.filter_by(nome=row.get('nome')).first() if row.get('nome') else None
                if not exists:
                    obj = Produto()
                    for col, val in row.items():
                        if hasattr(obj, col) and col != 'id':
                            setattr(obj, col, val)
                    db.session.add(obj)
                    count += 1
            db.session.commit()
            resultados.append(f"✅ Produtos: {count}")
        
        # Importa ordens de serviço
        if 'ordem_servico' in dados:
            count = 0
            for row in dados['ordem_servico']['rows']:
                obj = OrdemServico()
                for col, val in row.items():
                    if hasattr(obj, col) and col != 'id':
                        setattr(obj, col, val)
                db.session.add(obj)
                count += 1
            db.session.commit()
            resultados.append(f"✅ Ordens de Serviço: {count}")
        
        # Importa propostas
        if 'propostas' in dados:
            count = 0
            for row in dados['propostas']['rows']:
                obj = Proposta()
                for col, val in row.items():
                    if hasattr(obj, col) and col != 'id':
                        setattr(obj, col, val)
                db.session.add(obj)
                count += 1
            db.session.commit()
            resultados.append(f"✅ Propostas: {count}")
        
        flash('🎉 Importação automática concluída! ' + ' | '.join(resultados), 'success')
        return redirect(url_for('painel.dashboard'))
        
    except Exception as e:
        db.session.rollback()
        flash(f'❌ Erro na importação: {str(e)}', 'error')
        return redirect(url_for('painel.dashboard'))