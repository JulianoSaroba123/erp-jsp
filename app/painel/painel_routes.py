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
        # Importa configurações
        from app.configuracao.configuracao_utils import get_config
        config = get_config()
        
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
                             config=config,
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
                             config=None,
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
            {"numero": "OS-2025-002", "cliente_nome": "Ricardo Cury", "titulo": "Bomba Poço Artesiano", "status": "concluida", "prioridade": "alta", "data_abertura": "2025-11-18", "data_inicio": "2025-11-18 07:30:00", "data_conclusao": "2025-11-18 09:30:00", "data_vencimento_pagamento": "2025-11-25", "valor_servico": 360, "valor_total": 360, "tecnico_responsavel": "Juliano", "equipamento": "Bomba Poço artesiano", "marca_modelo": "NT", "solicitante": "Mário", "solucao": "Solicitado a substituição por uma igual ou compatível"},
            {"numero": "OS-2025-003", "cliente_nome": "CONDOMINIO EDIFICIO CLOVIS DOS SANTOS", "titulo": "Gerador Diesel MWM 81 kVA", "status": "concluida", "prioridade": "normal", "data_abertura": "2025-11-11", "data_inicio": "2025-11-20 13:30:00", "data_conclusao": "2025-11-20 17:40:00", "data_vencimento_pagamento": "2025-11-24", "valor_pecas": 1100, "valor_total": 1100, "tecnico_responsavel": "Juliano", "equipamento": "Gerador Diesel MWM 81 kVA", "marca_modelo": "MWM-0229-6 / WEG- GTA 81/78KVA", "solicitante": "Rose", "observacoes": "Orçamento enviado para aprovação do cliente"},
            {"numero": "OS20250007", "cliente_nome": "Mr Jacky", "titulo": "Máquina M5", "status": "concluida", "prioridade": "normal", "data_abertura": "2025-11-18", "data_conclusao": "2025-11-19 20:28:00", "data_vencimento_pagamento": "2025-11-24", "valor_servico": 720, "valor_total": 720, "tecnico_responsavel": "Juliano", "equipamento": "Calandra Termotransferidora M5", "marca_modelo": "TF-601", "solicitante": "Márcia", "solucao": "Realizado reaperto nos bornes de conexão dos terminais do sensor de temperatura. Reapertado a temperatura o sensor que estava solto. Feito a calibração da temperatura"},
            {"numero": "OS20250008", "cliente_nome": "Rodrigo Quartarolo", "titulo": "Bomba de Desinfecção", "status": "concluida", "prioridade": "alta", "data_abertura": "2025-11-18", "data_inicio": "2025-11-18 08:00:00", "data_conclusao": "2025-11-18 08:00:00", "data_vencimento_pagamento": "2025-11-24", "valor_servico": 200, "valor_total": 200, "tecnico_responsavel": "Juliano", "equipamento": "Bomba de produto", "marca_modelo": "Sem Marca", "solicitante": "Rodrigo", "solucao": "Solicitado o destravamento da bomba. Substituído o cabo inteiro nesse ponto e reapertado as conexões. Realizado testes de comando, ok."},
            {"numero": "OS20250009", "cliente_nome": "Sergio Yoshio Fujiwara", "titulo": "Atendimento Emergencial", "status": "concluida", "prioridade": "alta", "data_abertura": "2025-11-21", "data_inicio": "2025-11-21 13:30:00", "data_conclusao": "2025-11-21 21:45:00", "data_vencimento_pagamento": "2025-11-24", "valor_servico": 1240, "valor_pecas": 510, "valor_total": 1750, "tecnico_responsavel": "Juliano", "equipamento": "Grupo Gerador / Pivô", "marca_modelo": "BTA225-MI 09", "solicitante": "Mateus", "solucao": "Grupo gerador - Substituição da placa AVR. Pivô - Isolado o cabo de comando e detectado 2 chaves de segurança danificadas e um fim de curso danificado nas torres"},
            {"numero": "OS20250010", "cliente_nome": "Mr Jacky", "titulo": "Revisadora 01", "status": "concluida", "prioridade": "normal", "data_abertura": "2025-11-21", "data_inicio": "2025-11-21 10:35:00", "data_conclusao": "2025-11-21 11:35:00", "data_vencimento_pagamento": "2025-11-24", "valor_servico": 180, "valor_pecas": 181.45, "valor_total": 361.45, "tecnico_responsavel": "Juliano", "equipamento": "Revisadora 01", "marca_modelo": "S/marca", "solicitante": "Márcia", "solucao": "Substituição da pedaleira e Lâmpadas"},
            {"numero": "OS20250011", "cliente_nome": "Sander", "titulo": "Grupos Geradores", "status": "concluida", "prioridade": "normal", "data_abertura": "2025-11-27", "data_inicio": "2025-11-27 08:00:00", "data_conclusao": "2025-11-27 16:00:00", "data_vencimento_pagamento": "2025-12-01", "valor_servico": 800, "valor_total": 800, "tecnico_responsavel": "Juliano", "equipamento": "Grupos Geradores 1 e 2", "marca_modelo": "MWM", "solicitante": "Sander", "solucao": "Realizado a limpeza e organização dos cabos de comando dos dois grupos geradores e regulagem de abertura e fechamento da porta compartimento do painel de comando"},
            {"numero": "OS20250016", "cliente_nome": "CONDOMINIO EDIFICIO CLOVIS DOS SANTOS", "titulo": "Grupo Gerador", "status": "concluida", "prioridade": "normal", "data_abertura": "2025-12-02", "data_inicio": "2025-12-02 13:30:00", "data_conclusao": "2025-12-02 15:30:00", "data_vencimento_pagamento": "2025-12-05", "valor_servico": 360, "valor_total": 360, "tecnico_responsavel": "Juliano", "equipamento": "Grupo-Gerador", "marca_modelo": "MWM-0229-6 / WEG- GTA 81/78KVA", "solicitante": "Rose", "observacoes": "Recomendo aumentar a frequência de partidas semanais.", "solucao": "Foi desmontado o compartimento do mecanismo do acelerador eletrônico que se localiza na bomba injetora. Realizado a limpeza do compartimento do mecanismo do acelerador que estava travado. Realizado vários testes de partida e funcionamento."},
            {"numero": "OS20250017", "cliente_nome": "Mr Jacky", "titulo": "Maquina M5/ Revisora 01", "status": "concluida", "prioridade": "normal", "data_abertura": "2025-12-01", "data_inicio": "2025-12-01 09:30:00", "data_conclusao": "2025-12-01 11:30:00", "data_vencimento_pagamento": "2025-12-03", "valor_servico": 760, "valor_total": 760, "tecnico_responsavel": "Juliano", "equipamento": "Calandra Termo transferidora /Revisadora", "marca_modelo": "TF 601/ OMATEC", "solicitante": "Márcia", "solucao": "M5 - Realizado o ajuste de compensação no controlador. Feito acompanhamento do processo. Revisadora 01 - Retirado a placa de controle para manutenção e testes em bancada"}
        ]
        
        # Importa ordens de serviço
        from datetime import datetime
        count = 0
        for row in ordens_data:
            exists = OrdemServico.query.filter_by(numero=row.get('numero')).first()
            if exists:
                # Atualiza os dados existentes
                obj = exists
                cliente = Cliente.query.filter_by(nome=row.get('cliente_nome')).first()
                if cliente:
                    obj.cliente_id = cliente.id
                for col, val in row.items():
                    if col == 'cliente_nome':
                        continue
                    if col == 'data_abertura' and val:
                        val = datetime.strptime(val, '%Y-%m-%d').date()
                    elif col == 'data_vencimento_pagamento' and val:
                        val = datetime.strptime(val, '%Y-%m-%d').date()
                    elif col in ['data_inicio', 'data_conclusao'] and val:
                        val = datetime.strptime(val, '%Y-%m-%d %H:%M:%S')
                    if hasattr(obj, col):
                        setattr(obj, col, val)
                count += 1
            else:
                # Cria nova ordem
                cliente = Cliente.query.filter_by(nome=row.get('cliente_nome')).first()
                if cliente:
                    obj = OrdemServico()
                    obj.cliente_id = cliente.id
                    for col, val in row.items():
                        if col == 'cliente_nome':
                            continue
                        if col == 'data_abertura' and val:
                            val = datetime.strptime(val, '%Y-%m-%d').date()
                        elif col == 'data_vencimento_pagamento' and val:
                            val = datetime.strptime(val, '%Y-%m-%d').date()
                        elif col in ['data_inicio', 'data_conclusao'] and val:
                            val = datetime.strptime(val, '%Y-%m-%d %H:%M:%S')
                        if hasattr(obj, col):
                            setattr(obj, col, val)
                    obj.ativo = True
                    db.session.add(obj)
                    count += 1
        db.session.commit()
        resultados.append(f"Ordens: {count}")
        
        # Atualiza configuração com logo em base64 (para funcionar no Render)
        from app.configuracao.configuracao_model import Configuracao
        config = Configuracao.get_solo()
        if not config.logo_base64:
            # Logo JSP em base64 (15x15mm)
            config.logo_base64 = "/9j/4AAQSkZJRgABAQEBLAEsAAD/4QC8RXhpZgAASUkqAAgAAAAGABIBAwABAAAAAQAAABoBBQABAAAAVgAAABsBBQABAAAAXgAAACgBAwABAAAAAgAAABMCAwABAAAAAQAAAGmHBAABAAAAZgAAAAAAAAAsAQAAAQAAACwBAAABAAAABgAAkAcABAAAADAyMTABkQcABAAAAAECAwAAoAcABAAAADAxMDABoAMAAQAAAP//AAACoAMAAQAAALEAAAADoAMAAQAAALEAAAAAAAAA/+EOamh0dHA6Ly9ucy5hZG9iZS5jb20veGFwLzEuMC8APD94cGFja2V0IGJlZ2luPSfvu78nIGlkPSdXNU0wTXBDZWhpSHpyZVN6TlRjemtjOWQnPz4KPHg6eG1wbWV0YSB4bWxuczp4PSdhZG9iZTpuczptZXRhLyc+CjxyZGY6UkRGIHhtbG5zOnJkZj0naHR0cDovL3d3dy53My5vcmcvMTk5OS8wMi8yMi1yZGYtc3ludGF4LW5zIyc+CgogPHJkZjpEZXNjcmlwdGlvbiByZGY6YWJvdXQ9JycKICB4bWxuczpBdHRyaWI9J2h0dHA6Ly9ucy5hdHRyaWJ1dGlvbi5jb20vYWRzLzEuMC8nPgogIDxBdHRyaWI6QWRzPgogICA8cmRmOlNlcT4KICAgIDxyZGY6bGkgcmRmOnBhcnNlVHlwZT0nUmVzb3VyY2UnPgogICAgIDxBdHRyaWI6Q3JlYXRlZD4yMDI1LTA5LTA5PC9BdHRyaWI6Q3JlYXRlZD4KICAgICA8QXR0cmliOkV4dElkPjM3OTQzMTVlLTg3OTMtNDAyMS1iOWRjLWE0Mzc3MDhiOWRhZDwvQXR0cmliOkV4dElkPgogICAgIDxBdHRyaWI6RmJJZD41MjUyNjU5MTQxNzk1ODA8L0F0dHJpYjpGYklkPgogICAgIDxBdHRyaWI6VG91Y2hUeXBlPjI8L0F0dHJpYjpUb3VjaFR5cGU+CiAgICA8L3JkZjpsaT4KICAgPC9yZGY6U2VxPgogIDwvQXR0cmliOkFkcz4KIDwvcmRmOkRlc2NyaXB0aW9uPgoKIDxyZGY6RGVzY3JpcHRpb24gcmRmOmFib3V0PScnCiAgeG1sbnM6ZGM9J2h0dHA6Ly9wdXJsLm9yZy9kYy9lbGVtZW50cy8xLjEvJz4KICA8ZGM6dGl0bGU+CiAgIDxyZGY6QWx0PgogICAgPHJkZjpsaSB4bWw6bGFuZz0neC1kZWZhdWx0Jz5TZW0gbm9tZSAoMzUgeCAzNSBtbSkgKDE1IHggMTUgbW0pIC0gMTwvcmRmOmxpPgogICA8L3JkZjpBbHQ+CiAgPC9kYzp0aXRsZT4KIDwvcmRmOkRlc2NyaXB0aW9uPgoKIDxyZGY6RGVzY3JpcHRpb24gcmRmOmFib3V0PScnCiAgeG1sbnM6cGRmPSdodHRwOi8vbnMuYWRvYmUuY29tL3BkZi8xLjMvJz4KICA8cGRmOkF1dGhvcj5KdWxpYW5vIFNhcm9iYSBQZXJlaXJhPC9wZGY6QXV0aG9yPgogPC9yZGY6RGVzY3JpcHRpb24+CgogPHJkZjpEZXNjcmlwdGlvbiByZGY6YWJvdXQ9JycKICB4bWxuczp4bXA9J2h0dHA6Ly9ucy5hZG9iZS5jb20veGFwLzEuMC8nPgogIDx4bXA6Q3JlYXRvclRvb2w+Q2FudmEgKFJlbmRlcmVyKSBkb2M9REFHeWcxalZkckkgdXNlcj1VQURuYjRJODM3VSBicmFuZD1FTMOJVFJJQ0EgU0FST0JBICZhbXA7IFNPTEFSIHRlbXBsYXRlPTwveG1wOkNyZWF0b3JUb29sPgogPC9yZGY6RGVzY3JpcHRpb24+CjwvcmRmOlJERj4KPC94OnhtcG1ldGE+CiAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAKICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgIAogICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgCiAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAKICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgIAogICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgCiAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAKICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgIAogICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgCiAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAKICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgIAogICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgCiAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAKICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgIAogICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgCiAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAKICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgIAogICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgCiAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAKICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgIAogICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgCiAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAKICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgIAogICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgCjw/eHBhY2tldCBlbmQ9J3cnPz7/2wBDAAYEBQYFBAYGBQYHBwYIChAKCgkJChQODwwQFxQYGBcUFhYaHSUfGhsjHBYWICwgIyYnKSopGR8tMC0oMCUoKSj/2wBDAQcHBwoIChMKChMoGhYaKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCj/wAARCACxALEDASIAAhEBAxEB/8QAHwAAAQUBAQEBAQEAAAAAAAAAAAECAwQFBgcICQoL/8QAtRAAAgEDAwIEAwUFBAQAAAF9AQIDAAQRBRIhMUEGE1FhByJxFDKBkaEII0KxwRVS0fAkM2JyggkKFhcYGRolJicoKSo0NTY3ODk6Q0RFRkdISUpTVFVWV1hZWmNkZWZnaGlqc3R1dnd4eXqDhIWGh4iJipKTlJWWl5iZmqKjpKWmp6ipqrKztLW2t7i5usLDxMXGx8jJytLT1NXW19jZ2uHi4+Tl5ufo6erx8vP09fb3+Pn6/8QAHwEAAwEBAQEBAQEBAQAAAAAAAAECAwQFBgcICQoL/8QAtREAAgECBAQDBAcFBAQAAQJ3AAECAxEEBSExBhJBUQdhcRMiMoEIFEKRobHBCSMzUvAVYnLRChYkNOEl8RcYGRomJygpKjU2Nzg5OkNERUZHSElKU1RVVldYWVpjZGVmZ2hpanN0dXZ3eHl6goOEhYaHiImKkpOUlZaXmJmaoqOkpaanqKmqsrO0tba3uLm6wsPExcbHyMnK0tPU1dbX2Nna4uPk5ebn6Onq8vP09fb3+Pn6/9oADAMBAAIR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"
            config.nome_fantasia = config.nome_fantasia or "JSP Elétrica Industrial"
            db.session.commit()
            resultados.append("Logo: OK")
        
        flash('🎉 Importação concluída! ' + ' | '.join(resultados), 'success')
        return redirect(url_for('painel.dashboard'))
        
    except Exception as e:
        db.session.rollback()
        flash(f'❌ Erro na importação: {str(e)}', 'error')
        return redirect(url_for('painel.dashboard'))