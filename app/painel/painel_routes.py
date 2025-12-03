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
    Importa dados automaticamente - dados embutidos no código.
    Apenas admin pode usar.
    """
    from flask import flash
    
    # Apenas admin
    if current_user.tipo_usuario != 'admin':
        flash('Acesso negado. Apenas administradores.', 'error')
        return redirect(url_for('painel.dashboard'))
    
    try:
        resultados = []
        
        # Importa models
        from app.cliente.cliente_model import Cliente
        from app.fornecedor.fornecedor_model import Fornecedor
        from app.produto.produto_model import Produto
        
        # Dados dos clientes embutidos
        clientes_data = [
            {"nome": "CONDOMINIO EDIFICIO CLOVIS DOS SANTOS", "tipo": "PJ", "cpf_cnpj": "57.052.300/0001-31", "email": "uniolivia@hotmail.com", "telefone": "(15) 3316-6352", "celular": "(15) 99796-2849", "endereco": "PRAC MARTINHO GUEDES", "numero": "86", "bairro": "CENTRO", "cidade": "TATUI", "estado": "SP", "cep": "18270-370"},
            {"nome": "Sergio Yoshio Fujiwara", "tipo": "PF", "cpf_cnpj": "077.142.788-38", "email": "sfujivara@uol.com.br", "telefone": "(15) 3542-1442", "endereco": "Rua dos Expedicionários", "numero": "458", "bairro": "Centro", "cidade": "Capão Bonito", "estado": "SP", "cep": "18300-060"},
            {"nome": "Proninho Associação dos Amigos do Ninho Verde II Eco Residence", "tipo": "PJ", "cpf_cnpj": "47.686.555/0015-06", "email": "paulohenrique@ninhoverde-2.com.br", "telefone": "(14) 99697-6537", "endereco": "ROD CASTELLO BRANCO", "numero": "KM 196", "bairro": "NVIIER-LOT.NINHO V.II E. RESID", "cidade": "PARDINHO", "estado": "SP", "cep": "18640-000"},
            {"nome": "Ultramix Tintas Industriais", "tipo": "PJ", "cpf_cnpj": "05.536.213/0001-56", "email": "ultramix@tintasultramix.com.br", "telefone": "(15) 3286-8060", "endereco": "ROD MARECHAL RONDON", "bairro": "IPIRANGA", "cidade": "JUMIRIM", "estado": "SP", "cep": "18535-000"},
            {"nome": "Pedro Do Indio Botucatu", "tipo": "PJ", "cpf_cnpj": "20.287.770/0001-74", "email": "pedradoindiobotucatu@gmail.com", "telefone": "(14) 38861-3761438136181", "endereco": "AREA RURAL", "numero": "S/N", "bairro": "AREA RURAL DE BOTUCATU", "cidade": "Botucatu", "estado": "SP", "cep": "18619-899"},
            {"nome": "Mr Jacky", "tipo": "PJ", "cpf_cnpj": "20.631.771/0001-07", "email": "mrjackyfincanceiro@gmail.com", "telefone": "(15) 98478-7891", "cidade": "TIETE"},
            {"nome": "Rodrigo Quartarolo", "tipo": "PF", "cpf_cnpj": "000.272.278-00"},
            {"nome": "Ricardo Cury", "tipo": "PJ", "cpf_cnpj": "08.143.688/0001-70", "email": "arcyagropecuaria@uol.com.br", "telefone": "(11) 30514-20611130514206", "endereco": "SÍTIO SAO JOAO", "numero": "S/N", "bairro": "SAO JOAO", "cidade": "TIETE", "estado": "SP", "cep": "18530-000"},
            {"nome": "Teste Cliente Válido", "tipo": "PF", "cpf_cnpj": "98765432101", "email": "valido@teste.com"},
            {"nome": "Sander", "tipo": "PF", "cpf_cnpj": "000.000.000-00"}
        ]
        
        # Importa clientes
        count = 0
        for row in clientes_data:
            exists = Cliente.query.filter_by(cpf_cnpj=row.get('cpf_cnpj')).first() if row.get('cpf_cnpj') else None
            if not exists:
                cliente = Cliente()
                for col, val in row.items():
                    if hasattr(cliente, col):
                        setattr(cliente, col, val)
                cliente.ativo = True
                db.session.add(cliente)
                count += 1
        db.session.commit()
        resultados.append(f"Clientes: {count}")
        
        # Dados dos fornecedores
        fornecedores_data = [
            {"nome": "Distribuidora de Peças Diesel", "email": "vendas@distpecasdiesel.com.br", "telefone": "(11) 3333-4444", "endereco": "Rua das Peças, 100", "cidade": "São Paulo", "estado": "SP"},
            {"nome": "Lubrificantes Premium", "cnpj_cpf": "33.444.555/0001-66", "email": "comercial@lubripremium.com.br", "telefone": "(11) 5555-6666", "endereco": "Av. dos Óleos, 200", "cidade": "São Caetano do Sul", "estado": "SP"}
        ]
        
        # Importa fornecedores
        count = 0
        for row in fornecedores_data:
            exists = Fornecedor.query.filter_by(nome=row.get('nome')).first()
            if not exists:
                obj = Fornecedor()
                for col, val in row.items():
                    if hasattr(obj, col):
                        setattr(obj, col, val)
                obj.ativo = True
                db.session.add(obj)
                count += 1
        db.session.commit()
        resultados.append(f"Fornecedores: {count}")
        
        # Dados dos produtos
        produtos_data = [
            {"nome": "Óleo Lubrificante SAE 15W40", "preco_venda": 35, "unidade_medida": "Litro", "estoque_atual": 50, "preco_custo": 25},
            {"nome": "Filtro de Óleo", "preco_venda": 45, "unidade_medida": "UN", "estoque_atual": 30, "preco_custo": 30},
            {"nome": "Filtro de Ar", "preco_venda": 25, "unidade_medida": "UN", "estoque_atual": 20, "preco_custo": 15},
            {"nome": "Correias em V", "preco_venda": 85, "unidade_medida": "Conjunto", "estoque_atual": 15, "preco_custo": 55},
            {"nome": "Pedaleira LLJFS14", "codigo": "5012", "preco_venda": 147.47, "unidade_medida": "UN", "estoque_atual": 1, "preco_custo": 109.24}
        ]
        
        # Importa produtos
        count = 0
        for row in produtos_data:
            exists = Produto.query.filter_by(nome=row.get('nome')).first()
            if not exists:
                obj = Produto()
                for col, val in row.items():
                    if hasattr(obj, col):
                        setattr(obj, col, val)
                obj.ativo = True
                db.session.add(obj)
                count += 1
        db.session.commit()
        resultados.append(f"Produtos: {count}")
        
        # Dados das ordens de serviço (cliente_nome para buscar o ID correto)
        from app.ordem_servico.ordem_servico_model import OrdemServico
        
        ordens_data = [
            {"numero": "OS-2025-002", "cliente_nome": "Ricardo Cury", "titulo": "Bomba Poço Artesiano", "status": "concluida", "prioridade": "alta", "data_abertura": "2025-11-18", "valor_servico": 360, "valor_total": 360, "tecnico_responsavel": "Juliano", "equipamento": "Bomba Poço artesiano", "marca_modelo": "NT"},
            {"numero": "OS-2025-003", "cliente_nome": "CONDOMINIO EDIFICIO CLOVIS DOS SANTOS", "titulo": "Gerador Diesel MWM 81 kVA", "status": "concluida", "prioridade": "normal", "data_abertura": "2025-11-11", "valor_pecas": 1100, "valor_total": 1100, "tecnico_responsavel": "Juliano", "equipamento": "Gerador Diesel MWM 81 kVA", "marca_modelo": "MWM-0229-6 / WEG- GTA 81/78KVA"},
            {"numero": "OS20250007", "cliente_nome": "Mr Jacky", "titulo": "Máquina M5", "status": "concluida", "prioridade": "normal", "data_abertura": "2025-11-18", "valor_servico": 720, "valor_total": 720, "tecnico_responsavel": "Juliano", "equipamento": "Calandra Termotransferidora M5", "marca_modelo": "TF-601"},
            {"numero": "OS20250008", "cliente_nome": "Rodrigo Quartarolo", "titulo": "Bomba de Desinfecção", "status": "concluida", "prioridade": "alta", "data_abertura": "2025-11-18", "valor_servico": 200, "valor_total": 200, "tecnico_responsavel": "Juliano", "equipamento": "Bomba de produto", "marca_modelo": "Sem Marca"},
            {"numero": "OS20250009", "cliente_nome": "Sergio Yoshio Fujiwara", "titulo": "Atendimento Emergencial", "status": "concluida", "prioridade": "alta", "data_abertura": "2025-11-21", "valor_servico": 1240, "valor_pecas": 510, "valor_total": 1750, "tecnico_responsavel": "Juliano", "equipamento": "Grupo Gerador / Pivô", "marca_modelo": "BTA225-MI 09"},
            {"numero": "OS20250010", "cliente_nome": "Mr Jacky", "titulo": "Revisadora 01", "status": "concluida", "prioridade": "normal", "data_abertura": "2025-11-21", "valor_servico": 180, "valor_pecas": 181.45, "valor_total": 361.45, "tecnico_responsavel": "Juliano", "equipamento": "Revisadora 01", "marca_modelo": "S/marca"},
            {"numero": "OS20250011", "cliente_nome": "Sander", "titulo": "Grupos Geradores", "status": "concluida", "prioridade": "normal", "data_abertura": "2025-11-27", "valor_servico": 800, "valor_total": 800, "tecnico_responsavel": "Juliano", "equipamento": "Grupos Geradores 1 e 2", "marca_modelo": "MWM"},
            {"numero": "OS20250016", "cliente_nome": "CONDOMINIO EDIFICIO CLOVIS DOS SANTOS", "titulo": "Grupo Gerador", "status": "concluida", "prioridade": "normal", "data_abertura": "2025-12-02", "valor_servico": 360, "valor_total": 360, "tecnico_responsavel": "Juliano", "equipamento": "Grupo-Gerador", "marca_modelo": "MWM-0229-6 / WEG- GTA 81/78KVA"},
            {"numero": "OS20250017", "cliente_nome": "Mr Jacky", "titulo": "Maquina M5/ Revisora 01", "status": "concluida", "prioridade": "normal", "data_abertura": "2025-12-01", "valor_servico": 760, "valor_total": 760, "tecnico_responsavel": "Juliano", "equipamento": "Calandra Termo transferidora /Revisadora", "marca_modelo": "TF 601/ OMATEC"}
        ]
        
        # Importa ordens de serviço
        from datetime import datetime
        count = 0
        for row in ordens_data:
            exists = OrdemServico.query.filter_by(numero=row.get('numero')).first()
            if not exists:
                # Busca cliente pelo nome
                cliente = Cliente.query.filter_by(nome=row.get('cliente_nome')).first()
                if cliente:
                    obj = OrdemServico()
                    obj.cliente_id = cliente.id
                    for col, val in row.items():
                        if col == 'cliente_nome':
                            continue  # Pula, já processamos
                        if col == 'data_abertura' and val:
                            val = datetime.strptime(val, '%Y-%m-%d').date()
                        if hasattr(obj, col):
                            setattr(obj, col, val)
                    obj.ativo = True
                    db.session.add(obj)
                    count += 1
        db.session.commit()
        resultados.append(f"Ordens: {count}")
        
        flash('🎉 Importação concluída! ' + ' | '.join(resultados), 'success')
        return redirect(url_for('painel.dashboard'))
        
    except Exception as e:
        db.session.rollback()
        flash(f'❌ Erro na importação: {str(e)}', 'error')
        return redirect(url_for('painel.dashboard'))