# -*- coding: utf-8 -*-
"""
ERP JSP v3.0 - Rotas do Financeiro
=================================

Rotas para gerenciamento financeiro.
Inclui lançamentos, contas a pagar e receber.

Autor: JSP Soluções
Data: 2025
"""

from flask import Blueprint, render_template, redirect, url_for, request, flash, jsonify
from datetime import datetime, date
from decimal import Decimal
from app.extensoes import db
from app.financeiro.financeiro_model import LancamentoFinanceiro, CategoriaFinanceira, ContaBancaria, CentroCusto
from app.cliente.cliente_model import Cliente
from app.fornecedor.fornecedor_model import Fornecedor

# Criar blueprint
bp_financeiro = Blueprint('financeiro', __name__, template_folder='templates')


def converter_valor_monetario(valor_str):
    """Converte valor monetário do formato brasileiro para decimal."""
    if not valor_str:
        return Decimal('0.00')
    
    # Remove R$, espaços e pontos (separadores de milhares)
    valor_limpo = valor_str.replace('R$', '').replace(' ', '').replace('.', '')
    
    # Substitui vírgula por ponto (separador decimal)
    valor_limpo = valor_limpo.replace(',', '.')
    
    try:
        return Decimal(valor_limpo)
    except:
        return Decimal('0.00')


@bp_financeiro.route('/')
def dashboard():
    """Dashboard financeiro com resumo e indicadores."""
    try:
        # Resumo do mês atual
        resumo = LancamentoFinanceiro.get_resumo_mes()
        
        # Lançamentos vencidos
        vencidos = LancamentoFinanceiro.get_vencidos().count()
        
        # Pendentes
        pendentes = LancamentoFinanceiro.get_pendentes().count()
        
        # Contas a receber este mês
        contas_receber = LancamentoFinanceiro.get_contas_receber().filter(
            db.extract('month', LancamentoFinanceiro.data_vencimento) == date.today().month
        ).count()
        
        # Contas a pagar este mês
        contas_pagar = LancamentoFinanceiro.get_contas_pagar().filter(
            db.extract('month', LancamentoFinanceiro.data_vencimento) == date.today().month
        ).count()
        
        # Últimos lançamentos (usando data_criacao_auditoria ou data_lancamento)
        ultimos_lancamentos = LancamentoFinanceiro.query.filter_by(ativo=True).order_by(
            LancamentoFinanceiro.data_lancamento.desc()
        ).limit(10).all()
        
        return render_template('financeiro/dashboard.html',
                             resumo=resumo,
                             vencidos=vencidos,
                             pendentes=pendentes,
                             contas_receber=contas_receber,
                             contas_pagar=contas_pagar,
                             ultimos_lancamentos=ultimos_lancamentos,
                             data_atual=date.today())
    
    except Exception as e:
        flash(f'Erro ao carregar dashboard: {str(e)}', 'danger')
        return render_template('financeiro/dashboard.html')


@bp_financeiro.route('/lancamentos')
def listar_lancamentos():
    """Lista todos os lançamentos financeiros."""
    try:
        print("DEBUG: Iniciando listar_lancamentos")
        
        # Filtros
        tipo = request.args.get('tipo')
        status = request.args.get('status')
        categoria = request.args.get('categoria')
        data_inicio = request.args.get('data_inicio')
        data_fim = request.args.get('data_fim')
        
        print(f"DEBUG: Filtros: tipo={tipo}, status={status}")
        
        # Query base
        query = LancamentoFinanceiro.query.filter_by(ativo=True)
        
        # Aplicar filtros
        if tipo:
            query = query.filter(LancamentoFinanceiro.tipo == tipo)
        
        if status:
            query = query.filter(LancamentoFinanceiro.status == status)
        
        if categoria:
            query = query.filter(LancamentoFinanceiro.categoria == categoria)
        
        if data_inicio:
            data_inicio_obj = datetime.strptime(data_inicio, '%Y-%m-%d').date()
            query = query.filter(LancamentoFinanceiro.data_lancamento >= data_inicio_obj)
        
        if data_fim:
            data_fim_obj = datetime.strptime(data_fim, '%Y-%m-%d').date()
            query = query.filter(LancamentoFinanceiro.data_lancamento <= data_fim_obj)
        
        # Ordenação
        lancamentos = query.order_by(LancamentoFinanceiro.data_lancamento.desc()).all()
        print(f"DEBUG: Encontrados {len(lancamentos)} lançamentos")
        
        # Categorias para filtro
        categorias = db.session.query(LancamentoFinanceiro.categoria).filter(
            LancamentoFinanceiro.categoria.isnot(None),
            LancamentoFinanceiro.ativo == True
        ).distinct().all()
        categorias = [c[0] for c in categorias if c[0]]
        
        print("DEBUG: Renderizando template")
        return render_template('financeiro/listar_lancamentos.html',
                             lancamentos=lancamentos,
                             categorias=categorias,
                             filtros={
                                 'tipo': tipo,
                                 'status': status,
                                 'categoria': categoria,
                                 'data_inicio': data_inicio,
                                 'data_fim': data_fim
                             })
    
    except Exception as e:
        print(f"DEBUG: Erro em listar_lancamentos: {str(e)}")
        flash(f'Erro ao listar lançamentos: {str(e)}', 'danger')
        return redirect(url_for('financeiro.dashboard'))


@bp_financeiro.route('/lancamentos/novo')
def novo_lancamento():
    """Formulário para novo lançamento."""
    try:
        clientes = Cliente.query.filter_by(ativo=True).all()
        fornecedores = Fornecedor.query.filter_by(ativo=True).all()
        contas_bancarias = ContaBancaria.query.filter_by(ativo=True, ativa=True).all()
        centros_custo = CentroCusto.query.filter_by(ativo=True).all()
        
        return render_template('financeiro/form_lancamento.html',
                             clientes=clientes,
                             fornecedores=fornecedores,
                             contas_bancarias=contas_bancarias,
                             centros_custo=centros_custo,
                             date=date)
    
    except Exception as e:
        flash(f'Erro ao carregar formulário: {str(e)}', 'danger')
        return redirect(url_for('financeiro.listar_lancamentos'))


@bp_financeiro.route('/lancamentos/criar', methods=['POST'])
def criar_lancamento():
    """Cria novo lançamento financeiro."""
    try:
        # Dados do formulário
        descricao = request.form.get('descricao')
        valor_str = request.form.get('valor')
        tipo = request.form.get('tipo')
        categoria = request.form.get('categoria')
        subcategoria = request.form.get('subcategoria')
        data_lancamento_str = request.form.get('data_lancamento')
        data_vencimento_str = request.form.get('data_vencimento')
        status = request.form.get('status', 'pendente')
        observacoes = request.form.get('observacoes')
        numero_documento = request.form.get('numero_documento')
        forma_pagamento = request.form.get('forma_pagamento')
        cliente_id = request.form.get('cliente_id')
        fornecedor_id = request.form.get('fornecedor_id')
        conta_bancaria_id = request.form.get('conta_bancaria_id')
        centro_custo_id = request.form.get('centro_custo_id')
        recorrente = bool(request.form.get('recorrente'))
        frequencia = request.form.get('frequencia')
        
        # Validações básicas
        if not descricao:
            flash('Descrição é obrigatória', 'danger')
            return redirect(url_for('financeiro.novo_lancamento'))
        
        if not valor_str:
            flash('Valor é obrigatório', 'danger')
            return redirect(url_for('financeiro.novo_lancamento'))
        
        if not tipo:
            flash('Tipo é obrigatório', 'danger')
            return redirect(url_for('financeiro.novo_lancamento'))
        
        # Conversões
        valor = converter_valor_monetario(valor_str)
        
        if valor <= 0:
            flash('Valor deve ser maior que zero', 'danger')
            return redirect(url_for('financeiro.novo_lancamento'))
        
        # Datas
        data_lancamento = datetime.strptime(data_lancamento_str, '%Y-%m-%d').date() if data_lancamento_str else date.today()
        data_vencimento = datetime.strptime(data_vencimento_str, '%Y-%m-%d').date() if data_vencimento_str else None
        
        # Criar lançamento
        lancamento = LancamentoFinanceiro(
            descricao=descricao,
            valor=valor,
            tipo=tipo,
            categoria=categoria,
            subcategoria=subcategoria,
            data_lancamento=data_lancamento,
            data_vencimento=data_vencimento,
            status=status,
            observacoes=observacoes,
            numero_documento=numero_documento,
            forma_pagamento=forma_pagamento,
            cliente_id=int(cliente_id) if cliente_id else None,
            fornecedor_id=int(fornecedor_id) if fornecedor_id else None,
            conta_bancaria_id=int(conta_bancaria_id) if conta_bancaria_id else None,
            centro_custo_id=int(centro_custo_id) if centro_custo_id else None,
            recorrente=recorrente,
            frequencia=frequencia if recorrente else None
        )
        
        db.session.add(lancamento)
        db.session.commit()
        
        flash(f'Lançamento "{descricao}" criado com sucesso!', 'success')
        return redirect(url_for('financeiro.listar_lancamentos'))
    
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao criar lançamento: {str(e)}', 'danger')
        return redirect(url_for('financeiro.novo_lancamento'))


@bp_financeiro.route('/lancamentos/<int:id>/editar')
def editar_lancamento(id):
    """Formulário para editar lançamento."""
    try:
        lancamento = LancamentoFinanceiro.query.get_or_404(id)
        clientes = Cliente.query.filter_by(ativo=True).all()
        fornecedores = Fornecedor.query.filter_by(ativo=True).all()
        contas_bancarias = ContaBancaria.query.filter_by(ativo=True, ativa=True).all()
        centros_custo = CentroCusto.query.filter_by(ativo=True).all()
        
        return render_template('financeiro/form_lancamento.html',
                             lancamento=lancamento,
                             clientes=clientes,
                             fornecedores=fornecedores,
                             contas_bancarias=contas_bancarias,
                             centros_custo=centros_custo,
                             date=date)
    
    except Exception as e:
        flash(f'Erro ao carregar lançamento: {str(e)}', 'danger')
        return redirect(url_for('financeiro.listar_lancamentos'))


@bp_financeiro.route('/lancamentos/<int:id>/atualizar', methods=['POST'])
def atualizar_lancamento(id):
    """Atualiza lançamento financeiro."""
    try:
        lancamento = LancamentoFinanceiro.query.get_or_404(id)
        
        # Dados do formulário
        lancamento.descricao = request.form.get('descricao')
        valor_str = request.form.get('valor')
        lancamento.tipo = request.form.get('tipo')
        lancamento.categoria = request.form.get('categoria')
        lancamento.subcategoria = request.form.get('subcategoria')
        data_lancamento_str = request.form.get('data_lancamento')
        data_vencimento_str = request.form.get('data_vencimento')
        lancamento.status = request.form.get('status', 'pendente')
        lancamento.observacoes = request.form.get('observacoes')
        lancamento.numero_documento = request.form.get('numero_documento')
        lancamento.forma_pagamento = request.form.get('forma_pagamento')
        cliente_id = request.form.get('cliente_id')
        fornecedor_id = request.form.get('fornecedor_id')
        conta_bancaria_id = request.form.get('conta_bancaria_id')
        centro_custo_id = request.form.get('centro_custo_id')
        lancamento.recorrente = bool(request.form.get('recorrente'))
        lancamento.frequencia = request.form.get('frequencia')
        
        # Validações
        if not lancamento.descricao:
            flash('Descrição é obrigatória', 'danger')
            return redirect(url_for('financeiro.editar_lancamento', id=id))
        
        # Conversões
        lancamento.valor = converter_valor_monetario(valor_str)
        
        if lancamento.valor <= 0:
            flash('Valor deve ser maior que zero', 'danger')
            return redirect(url_for('financeiro.editar_lancamento', id=id))
        
        # Datas
        if data_lancamento_str:
            lancamento.data_lancamento = datetime.strptime(data_lancamento_str, '%Y-%m-%d').date()
        
        if data_vencimento_str:
            lancamento.data_vencimento = datetime.strptime(data_vencimento_str, '%Y-%m-%d').date()
        else:
            lancamento.data_vencimento = None
        
        # Relacionamentos
        lancamento.cliente_id = int(cliente_id) if cliente_id else None
        lancamento.fornecedor_id = int(fornecedor_id) if fornecedor_id else None
        lancamento.conta_bancaria_id = int(conta_bancaria_id) if conta_bancaria_id else None
        lancamento.centro_custo_id = int(centro_custo_id) if centro_custo_id else None
        
        if not lancamento.recorrente:
            lancamento.frequencia = None
        
        db.session.commit()
        
        flash(f'Lançamento "{lancamento.descricao}" atualizado com sucesso!', 'success')
        return redirect(url_for('financeiro.listar_lancamentos'))
    
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao atualizar lançamento: {str(e)}', 'danger')
        return redirect(url_for('financeiro.editar_lancamento', id=id))


@bp_financeiro.route('/lancamentos/<int:id>/excluir', methods=['GET', 'POST'])
def excluir_lancamento(id):
    """Exclui lançamento financeiro (soft delete)."""
    try:
        lancamento = LancamentoFinanceiro.query.get_or_404(id)
        
        # Se for GET, mostrar página de confirmação
        if request.method == 'GET':
            return render_template('financeiro/confirmar_exclusao.html', 
                                 lancamento=lancamento,
                                 data_hoje=datetime.now().date())
        
        # Se for POST, executar exclusão
        if request.method == 'POST':
            # Soft delete
            lancamento.ativo = False
            lancamento.data_exclusao = datetime.utcnow()
            
            db.session.commit()
            
            flash(f'Lançamento "{lancamento.descricao}" excluído com sucesso!', 'success')
            return redirect(url_for('financeiro.listar_lancamentos'))
    
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao excluir lançamento: {str(e)}', 'danger')
        return redirect(url_for('financeiro.listar_lancamentos'))


@bp_financeiro.route('/lancamentos/<int:id>/pagar', methods=['POST'])
def marcar_como_pago(id):
    """Marca lançamento como pago/recebido."""
    try:
        lancamento = LancamentoFinanceiro.query.get_or_404(id)
        data_pagamento_str = request.form.get('data_pagamento')
        
        if data_pagamento_str:
            data_pagamento = datetime.strptime(data_pagamento_str, '%Y-%m-%d').date()
        else:
            data_pagamento = date.today()
        
        lancamento.marcar_como_pago(data_pagamento)
        
        action = 'pago' if lancamento.tipo in ['despesa', 'conta_pagar'] else 'recebido'
        flash(f'Lançamento marcado como {action}!', 'success')
        
        return redirect(url_for('financeiro.listar_lancamentos'))
    
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao marcar como pago: {str(e)}', 'danger')
        return redirect(url_for('financeiro.listar_lancamentos'))


@bp_financeiro.route('/contas-pagar')
def contas_pagar():
    """Lista contas a pagar."""
    try:
        contas = LancamentoFinanceiro.get_contas_pagar().order_by(
            LancamentoFinanceiro.data_vencimento.asc()
        ).all()
        
        # Estatísticas
        total_pendente = sum(float(c.valor) for c in contas if c.status == 'pendente')
        vencidas = [c for c in contas if c.situacao_vencimento == 'vencido' and c.status == 'pendente']
        
        return render_template('financeiro/contas_pagar.html',
                             contas=contas,
                             total_pendente=total_pendente,
                             vencidas=vencidas,
                             date=date)
    
    except Exception as e:
        flash(f'Erro ao carregar contas a pagar: {str(e)}', 'danger')
        return redirect(url_for('financeiro.dashboard'))


@bp_financeiro.route('/contas-receber')
def contas_receber():
    """Lista contas a receber."""
    try:
        contas = LancamentoFinanceiro.get_contas_receber().order_by(
            LancamentoFinanceiro.data_vencimento.asc()
        ).all()
        
        # Estatísticas
        total_pendente = sum(float(c.valor) for c in contas if c.status == 'pendente')
        vencidas = [c for c in contas if c.situacao_vencimento == 'vencido' and c.status == 'pendente']
        
        return render_template('financeiro/contas_receber.html',
                             contas=contas,
                             total_pendente=total_pendente,
                             vencidas=vencidas,
                             date=date)
    
    except Exception as e:
        flash(f'Erro ao carregar contas a receber: {str(e)}', 'danger')
        return redirect(url_for('financeiro.dashboard'))


# API Routes
@bp_financeiro.route('/api/resumo-mes')
def api_resumo_mes():
    """API para resumo financeiro do mês."""
    try:
        mes = request.args.get('mes', type=int)
        ano = request.args.get('ano', type=int)
        
        resumo = LancamentoFinanceiro.get_resumo_mes(mes, ano)
        
        return jsonify({
            'status': 'success',
            'data': resumo
        })
    
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@bp_financeiro.route('/chaves-documentos')
def chaves_documentos():
    """Página de chaves de documentos fiscais e tributários."""
    return render_template('financeiro/chaves_documentos.html')


@bp_financeiro.route('/api/indicadores')
def api_indicadores():
    """API para indicadores financeiros."""
    try:
        # Lançamentos vencidos
        vencidos = LancamentoFinanceiro.get_vencidos().count()
        
        # Pendentes
        pendentes = LancamentoFinanceiro.get_pendentes().count()
        
        # Resumo do mês
        resumo = LancamentoFinanceiro.get_resumo_mes()
        
        return jsonify({
            'status': 'success',
            'data': {
                'vencidos': vencidos,
                'pendentes': pendentes,
                'resumo_mes': resumo
            }
        })
    
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@bp_financeiro.route('/api/dashboard-dados')
def api_dashboard_dados():
    """API completa para dados do dashboard com gráficos."""
    try:
        from datetime import timedelta
        from sqlalchemy import func, extract
        
        hoje = date.today()
        mes_atual = hoje.month
        ano_atual = hoje.year
        
        # Resumo do mês atual
        resumo_mes = LancamentoFinanceiro.get_resumo_mes()
        
        # Evolução dos últimos 6 meses
        meses_labels = []
        receitas_mes = []
        despesas_mes = []
        saldos_acumulados = []
        saldo_acumulado = 0
        
        for i in range(5, -1, -1):
            mes_ref = hoje - timedelta(days=i*30)
            mes = mes_ref.month
            ano = mes_ref.year
            
            # Nome do mês
            meses_nomes = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 
                          'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez']
            meses_labels.append(meses_nomes[mes - 1])
            
            # Receitas do mês
            receitas = db.session.query(func.sum(LancamentoFinanceiro.valor)).filter(
                extract('month', LancamentoFinanceiro.data_lancamento) == mes,
                extract('year', LancamentoFinanceiro.data_lancamento) == ano,
                LancamentoFinanceiro.tipo.in_(['receita', 'conta_receber']),
                LancamentoFinanceiro.status == 'recebido',
                LancamentoFinanceiro.ativo == True
            ).scalar() or 0
            
            # Despesas do mês
            despesas = db.session.query(func.sum(LancamentoFinanceiro.valor)).filter(
                extract('month', LancamentoFinanceiro.data_lancamento) == mes,
                extract('year', LancamentoFinanceiro.data_lancamento) == ano,
                LancamentoFinanceiro.tipo.in_(['despesa', 'conta_pagar']),
                LancamentoFinanceiro.status == 'pago',
                LancamentoFinanceiro.ativo == True
            ).scalar() or 0
            
            receitas_mes.append(float(receitas))
            despesas_mes.append(float(despesas))
            
            # Saldo acumulado
            saldo_acumulado += float(receitas) - float(despesas)
            saldos_acumulados.append(saldo_acumulado)
        
        # Top 5 categorias de despesas
        categorias_despesas = db.session.query(
            LancamentoFinanceiro.categoria,
            func.sum(LancamentoFinanceiro.valor).label('total')
        ).filter(
            extract('month', LancamentoFinanceiro.data_lancamento) == mes_atual,
            extract('year', LancamentoFinanceiro.data_lancamento) == ano_atual,
            LancamentoFinanceiro.tipo.in_(['despesa', 'conta_pagar']),
            LancamentoFinanceiro.categoria.isnot(None),
            LancamentoFinanceiro.ativo == True
        ).group_by(
            LancamentoFinanceiro.categoria
        ).order_by(
            func.sum(LancamentoFinanceiro.valor).desc()
        ).limit(5).all()
        
        categorias_nomes = [cat[0] or 'Sem categoria' for cat in categorias_despesas]
        categorias_valores = [float(cat[1]) for cat in categorias_despesas]
        
        # Cores para categorias
        cores_categorias = [
            'rgba(220, 53, 69, 0.7)',
            'rgba(255, 193, 7, 0.7)',
            'rgba(23, 162, 184, 0.7)',
            'rgba(108, 117, 125, 0.7)',
            'rgba(0, 123, 255, 0.7)'
        ]
        
        # Fluxo de caixa projetado (30 dias)
        fluxo_projetado = LancamentoFinanceiro.calcular_fluxo_caixa(30)
        
        return jsonify({
            'status': 'success',
            'data': {
                'resumo_mes': resumo_mes,
                'evolucao_mensal': {
                    'meses': meses_labels,
                    'receitas': receitas_mes,
                    'despesas': despesas_mes
                },
                'fluxo_caixa': {
                    'meses': meses_labels,
                    'saldos': saldos_acumulados
                },
                'top_categorias': {
                    'categorias': categorias_nomes,
                    'valores': categorias_valores,
                    'cores': cores_categorias[:len(categorias_nomes)]
                },
                'fluxo_projetado': fluxo_projetado
            }
        })
    
    except Exception as e:
        print(f"Erro na API dashboard: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


# ========================================
# CONTAS BANCÁRIAS
# ========================================

@bp_financeiro.route('/contas-bancarias')
def listar_contas_bancarias():
    """Lista todas as contas bancárias."""
    try:
        contas = ContaBancaria.query.filter_by(ativo=True).order_by(
            ContaBancaria.principal.desc(),
            ContaBancaria.nome.asc()
        ).all()
        
        # Calcular saldo total
        saldo_total = sum(float(conta.saldo_atual) for conta in contas)
        saldo_com_limite = sum(conta.saldo_com_limite for conta in contas)
        
        # Estatísticas
        contas_ativas = len([c for c in contas if c.ativa])
        contas_inativas = len([c for c in contas if not c.ativa])
        
        return render_template('financeiro/contas_bancarias/listar.html',
                             contas=contas,
                             saldo_total=saldo_total,
                             saldo_com_limite=saldo_com_limite,
                             contas_ativas=contas_ativas,
                             contas_inativas=contas_inativas)
    
    except Exception as e:
        flash(f'Erro ao listar contas bancárias: {str(e)}', 'danger')
        return redirect(url_for('financeiro.dashboard'))


@bp_financeiro.route('/contas-bancarias/nova')
def nova_conta_bancaria():
    """Formulário para nova conta bancária."""
    return render_template('financeiro/contas_bancarias/form.html')


@bp_financeiro.route('/contas-bancarias/criar', methods=['POST'])
def criar_conta_bancaria():
    """Cria nova conta bancária."""
    try:
        # Dados do formulário
        nome = request.form.get('nome')
        tipo = request.form.get('tipo')
        banco = request.form.get('banco')
        agencia = request.form.get('agencia')
        numero_conta = request.form.get('numero_conta')
        saldo_inicial_str = request.form.get('saldo_inicial')
        limite_credito_str = request.form.get('limite_credito')
        principal = bool(request.form.get('principal'))
        ativa = bool(request.form.get('ativa', True))
        observacoes = request.form.get('observacoes')
        
        # Validações
        if not nome:
            flash('Nome da conta é obrigatório', 'danger')
            return redirect(url_for('financeiro.nova_conta_bancaria'))
        
        if not tipo:
            flash('Tipo da conta é obrigatório', 'danger')
            return redirect(url_for('financeiro.nova_conta_bancaria'))
        
        # Conversões
        saldo_inicial = converter_valor_monetario(saldo_inicial_str) if saldo_inicial_str else Decimal('0.00')
        limite_credito = converter_valor_monetario(limite_credito_str) if limite_credito_str else Decimal('0.00')
        
        # Se esta conta for principal, remover flag de outras
        if principal:
            ContaBancaria.query.filter_by(principal=True).update({'principal': False})
        
        # Criar conta
        conta = ContaBancaria(
            nome=nome,
            tipo=tipo,
            banco=banco,
            agencia=agencia,
            numero_conta=numero_conta,
            saldo_inicial=saldo_inicial,
            saldo_atual=saldo_inicial,  # Saldo atual começa igual ao inicial
            limite_credito=limite_credito,
            principal=principal,
            ativa=ativa,
            observacoes=observacoes
        )
        
        db.session.add(conta)
        db.session.commit()
        
        flash(f'Conta bancária "{nome}" criada com sucesso!', 'success')
        return redirect(url_for('financeiro.listar_contas_bancarias'))
    
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao criar conta bancária: {str(e)}', 'danger')
        return redirect(url_for('financeiro.nova_conta_bancaria'))


@bp_financeiro.route('/contas-bancarias/<int:id>/editar')
def editar_conta_bancaria(id):
    """Formulário para editar conta bancária."""
    try:
        conta = ContaBancaria.query.get_or_404(id)
        return render_template('financeiro/contas_bancarias/form.html', conta=conta)
    
    except Exception as e:
        flash(f'Erro ao carregar conta bancária: {str(e)}', 'danger')
        return redirect(url_for('financeiro.listar_contas_bancarias'))


@bp_financeiro.route('/contas-bancarias/<int:id>/atualizar', methods=['POST'])
def atualizar_conta_bancaria(id):
    """Atualiza conta bancária."""
    try:
        conta = ContaBancaria.query.get_or_404(id)
        
        # Dados do formulário
        conta.nome = request.form.get('nome')
        conta.tipo = request.form.get('tipo')
        conta.banco = request.form.get('banco')
        conta.agencia = request.form.get('agencia')
        conta.numero_conta = request.form.get('numero_conta')
        
        # Saldo inicial - só atualizar se mudou
        saldo_inicial_str = request.form.get('saldo_inicial')
        novo_saldo_inicial = converter_valor_monetario(saldo_inicial_str) if saldo_inicial_str else Decimal('0.00')
        
        # Se saldo inicial mudou, ajustar saldo atual proporcionalmente
        if novo_saldo_inicial != conta.saldo_inicial:
            diferenca = novo_saldo_inicial - conta.saldo_inicial
            conta.saldo_atual += diferenca
            conta.saldo_inicial = novo_saldo_inicial
        
        limite_credito_str = request.form.get('limite_credito')
        conta.limite_credito = converter_valor_monetario(limite_credito_str) if limite_credito_str else Decimal('0.00')
        
        principal = bool(request.form.get('principal'))
        conta.ativa = bool(request.form.get('ativa', True))
        conta.observacoes = request.form.get('observacoes')
        
        # Se esta conta for principal, remover flag de outras
        if principal and not conta.principal:
            ContaBancaria.query.filter(ContaBancaria.id != id, ContaBancaria.principal == True).update({'principal': False})
        
        conta.principal = principal
        
        # Validações
        if not conta.nome:
            flash('Nome da conta é obrigatório', 'danger')
            return redirect(url_for('financeiro.editar_conta_bancaria', id=id))
        
        if not conta.tipo:
            flash('Tipo da conta é obrigatório', 'danger')
            return redirect(url_for('financeiro.editar_conta_bancaria', id=id))
        
        db.session.commit()
        
        flash(f'Conta bancária "{conta.nome}" atualizada com sucesso!', 'success')
        return redirect(url_for('financeiro.listar_contas_bancarias'))
    
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao atualizar conta bancária: {str(e)}', 'danger')
        return redirect(url_for('financeiro.editar_conta_bancaria', id=id))


@bp_financeiro.route('/contas-bancarias/<int:id>/excluir', methods=['POST'])
def excluir_conta_bancaria(id):
    """Exclui conta bancária (soft delete)."""
    try:
        conta = ContaBancaria.query.get_or_404(id)
        
        # Verificar se há lançamentos vinculados
        lancamentos_vinculados = LancamentoFinanceiro.query.filter_by(
            conta_bancaria_id=id,
            ativo=True
        ).count()
        
        if lancamentos_vinculados > 0:
            flash(f'Não é possível excluir. Existem {lancamentos_vinculados} lançamento(s) vinculado(s) a esta conta.', 'danger')
            return redirect(url_for('financeiro.listar_contas_bancarias'))
        
        # Soft delete
        conta.ativo = False
        conta.ativa = False
        conta.data_exclusao = datetime.utcnow()
        
        db.session.commit()
        
        flash(f'Conta bancária "{conta.nome}" excluída com sucesso!', 'success')
        return redirect(url_for('financeiro.listar_contas_bancarias'))
    
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao excluir conta bancária: {str(e)}', 'danger')
        return redirect(url_for('financeiro.listar_contas_bancarias'))


@bp_financeiro.route('/contas-bancarias/dashboard')
def dashboard_contas():
    """Dashboard de contas bancárias com saldos e movimentações."""
    try:
        contas = ContaBancaria.query.filter_by(ativo=True, ativa=True).all()
        
        # Estatísticas gerais
        saldo_total = sum(float(conta.saldo_atual) for conta in contas)
        saldo_com_limite = sum(conta.saldo_com_limite for conta in contas)
        
        # Últimas movimentações por conta
        movimentacoes = {}
        for conta in contas:
            ultimas = LancamentoFinanceiro.query.filter_by(
                conta_bancaria_id=conta.id,
                ativo=True
            ).order_by(LancamentoFinanceiro.data_lancamento.desc()).limit(5).all()
            movimentacoes[conta.id] = ultimas
        
        # Projeção para próximos 30 dias
        fluxo_projetado = LancamentoFinanceiro.calcular_fluxo_caixa(30)
        
        return render_template('financeiro/contas_bancarias/dashboard.html',
                             contas=contas,
                             saldo_total=saldo_total,
                             saldo_com_limite=saldo_com_limite,
                             movimentacoes=movimentacoes,
                             fluxo_projetado=fluxo_projetado)
    
    except Exception as e:
        flash(f'Erro ao carregar dashboard: {str(e)}', 'danger')
        return redirect(url_for('financeiro.dashboard'))


@bp_financeiro.route('/contas-bancarias/transferencia')
def nova_transferencia():
    """Formulário para transferência entre contas."""
    try:
        contas = ContaBancaria.query.filter_by(ativo=True, ativa=True).all()
        return render_template('financeiro/contas_bancarias/transferencia.html', 
                             contas=contas,
                             data_hoje=date.today())
    
    except Exception as e:
        flash(f'Erro ao carregar formulário: {str(e)}', 'danger')
        return redirect(url_for('financeiro.listar_contas_bancarias'))


@bp_financeiro.route('/contas-bancarias/transferencia/executar', methods=['POST'])
def executar_transferencia():
    """Executa transferência entre contas bancárias."""
    try:
        # Dados do formulário
        conta_origem_id = request.form.get('conta_origem_id')
        conta_destino_id = request.form.get('conta_destino_id')
        valor_str = request.form.get('valor')
        data_transferencia_str = request.form.get('data_transferencia')
        descricao = request.form.get('descricao')
        
        # Validações
        if not conta_origem_id or not conta_destino_id:
            flash('Selecione as contas de origem e destino', 'danger')
            return redirect(url_for('financeiro.nova_transferencia'))
        
        if conta_origem_id == conta_destino_id:
            flash('As contas de origem e destino devem ser diferentes', 'danger')
            return redirect(url_for('financeiro.nova_transferencia'))
        
        if not valor_str:
            flash('Informe o valor da transferência', 'danger')
            return redirect(url_for('financeiro.nova_transferencia'))
        
        # Conversões
        valor = converter_valor_monetario(valor_str)
        
        if valor <= 0:
            flash('O valor deve ser maior que zero', 'danger')
            return redirect(url_for('financeiro.nova_transferencia'))
        
        data_transferencia = datetime.strptime(data_transferencia_str, '%Y-%m-%d').date() if data_transferencia_str else date.today()
        
        # Buscar contas
        conta_origem = ContaBancaria.query.get_or_404(int(conta_origem_id))
        conta_destino = ContaBancaria.query.get_or_404(int(conta_destino_id))
        
        # Verificar saldo suficiente
        if float(conta_origem.saldo_atual) < float(valor):
            flash(f'Saldo insuficiente na conta {conta_origem.nome}. Saldo disponível: {conta_origem.saldo_formatado}', 'danger')
            return redirect(url_for('financeiro.nova_transferencia'))
        
        # Criar lançamento de saída (débito)
        lancamento_saida = LancamentoFinanceiro(
            descricao=descricao or f'Transferência para {conta_destino.nome}',
            valor=valor,
            tipo='despesa',
            status='pago',
            categoria='Transferência Bancária',
            subcategoria='Débito',
            data_lancamento=data_transferencia,
            data_pagamento=data_transferencia,
            conta_bancaria_id=conta_origem.id,
            observacoes=f'Transferência para conta {conta_destino.nome} (ID: {conta_destino.id})'
        )
        
        # Criar lançamento de entrada (crédito)
        lancamento_entrada = LancamentoFinanceiro(
            descricao=descricao or f'Transferência de {conta_origem.nome}',
            valor=valor,
            tipo='receita',
            status='recebido',
            categoria='Transferência Bancária',
            subcategoria='Crédito',
            data_lancamento=data_transferencia,
            data_pagamento=data_transferencia,
            conta_bancaria_id=conta_destino.id,
            observacoes=f'Transferência da conta {conta_origem.nome} (ID: {conta_origem.id})'
        )
        
        # Atualizar saldos
        conta_origem.atualizar_saldo(valor, 'subtrair')
        conta_destino.atualizar_saldo(valor, 'adicionar')
        
        # Salvar lançamentos
        db.session.add(lancamento_saida)
        db.session.add(lancamento_entrada)
        db.session.commit()
        
        flash(f'Transferência de {formatar_valor_real(valor)} realizada com sucesso!', 'success')
        return redirect(url_for('financeiro.dashboard_contas'))
    
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao executar transferência: {str(e)}', 'danger')
        return redirect(url_for('financeiro.nova_transferencia'))


# ========================================
# CENTROS DE CUSTO
# ========================================

@bp_financeiro.route('/centros-custo')
def listar_centros_custo():
    """Lista todos os centros de custo."""
    try:
        centros = CentroCusto.query.filter_by(ativo=True).order_by(
            CentroCusto.codigo.asc()
        ).all()
        
        # Calcular total de despesas por centro (mês atual)
        hoje = date.today()
        mes_atual = hoje.month
        ano_atual = hoje.year
        
        despesas_por_centro = {}
        for centro in centros:
            despesas_mes = CentroCusto.get_despesas_mes(centro.id, mes_atual, ano_atual)
            despesas_por_centro[centro.id] = despesas_mes
            
            # Calcular percentual do orçamento se houver
            if centro.orcamento_mensal and centro.orcamento_mensal > 0:
                centro.percentual_usado = (despesas_mes / float(centro.orcamento_mensal)) * 100
            else:
                centro.percentual_usado = 0
        
        return render_template('financeiro/centros_custo/listar.html',
                             centros=centros,
                             despesas_por_centro=despesas_por_centro)
    
    except Exception as e:
        flash(f'Erro ao listar centros de custo: {str(e)}', 'danger')
        return redirect(url_for('financeiro.dashboard'))


@bp_financeiro.route('/centros-custo/novo')
def novo_centro_custo():
    """Formulário para novo centro de custo."""
    # Buscar centros para hierarquia
    centros_pais = CentroCusto.query.filter_by(ativo=True, centro_pai_id=None).all()
    return render_template('financeiro/centros_custo/form.html', centros_pais=centros_pais)


@bp_financeiro.route('/centros-custo/criar', methods=['POST'])
def criar_centro_custo():
    """Cria novo centro de custo."""
    try:
        # Dados do formulário
        codigo = request.form.get('codigo')
        nome = request.form.get('nome')
        descricao = request.form.get('descricao')
        tipo = request.form.get('tipo')
        responsavel = request.form.get('responsavel')
        orcamento_mensal_str = request.form.get('orcamento_mensal')
        centro_pai_id = request.form.get('centro_pai_id')
        
        # Validações
        if not codigo:
            flash('Código é obrigatório', 'danger')
            return redirect(url_for('financeiro.novo_centro_custo'))
        
        if not nome:
            flash('Nome é obrigatório', 'danger')
            return redirect(url_for('financeiro.novo_centro_custo'))
        
        # Verificar se código já existe
        codigo_existente = CentroCusto.query.filter_by(codigo=codigo, ativo=True).first()
        if codigo_existente:
            flash(f'Já existe um centro de custo com o código "{codigo}"', 'danger')
            return redirect(url_for('financeiro.novo_centro_custo'))
        
        # Conversões
        orcamento_mensal = converter_valor_monetario(orcamento_mensal_str) if orcamento_mensal_str else None
        
        # Criar centro de custo
        centro = CentroCusto(
            codigo=codigo,
            nome=nome,
            descricao=descricao,
            tipo=tipo,
            responsavel=responsavel,
            orcamento_mensal=orcamento_mensal,
            centro_pai_id=int(centro_pai_id) if centro_pai_id else None
        )
        
        db.session.add(centro)
        db.session.commit()
        
        flash(f'Centro de custo "{codigo} - {nome}" criado com sucesso!', 'success')
        return redirect(url_for('financeiro.listar_centros_custo'))
    
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao criar centro de custo: {str(e)}', 'danger')
        return redirect(url_for('financeiro.novo_centro_custo'))


@bp_financeiro.route('/centros-custo/<int:id>/editar')
def editar_centro_custo(id):
    """Formulário para editar centro de custo."""
    try:
        centro = CentroCusto.query.get_or_404(id)
        centros_pais = CentroCusto.query.filter(
            CentroCusto.ativo == True,
            CentroCusto.id != id,
            CentroCusto.centro_pai_id == None
        ).all()
        return render_template('financeiro/centros_custo/form.html', 
                             centro=centro,
                             centros_pais=centros_pais)
    
    except Exception as e:
        flash(f'Erro ao carregar centro de custo: {str(e)}', 'danger')
        return redirect(url_for('financeiro.listar_centros_custo'))


@bp_financeiro.route('/centros-custo/<int:id>/atualizar', methods=['POST'])
def atualizar_centro_custo(id):
    """Atualiza centro de custo."""
    try:
        centro = CentroCusto.query.get_or_404(id)
        
        # Dados do formulário
        codigo = request.form.get('codigo')
        centro.nome = request.form.get('nome')
        centro.descricao = request.form.get('descricao')
        centro.tipo = request.form.get('tipo')
        centro.responsavel = request.form.get('responsavel')
        orcamento_mensal_str = request.form.get('orcamento_mensal')
        centro_pai_id = request.form.get('centro_pai_id')
        
        # Validações
        if not codigo:
            flash('Código é obrigatório', 'danger')
            return redirect(url_for('financeiro.editar_centro_custo', id=id))
        
        if not centro.nome:
            flash('Nome é obrigatório', 'danger')
            return redirect(url_for('financeiro.editar_centro_custo', id=id))
        
        # Verificar se código já existe em outro centro
        if codigo != centro.codigo:
            codigo_existente = CentroCusto.query.filter(
                CentroCusto.codigo == codigo,
                CentroCusto.ativo == True,
                CentroCusto.id != id
            ).first()
            if codigo_existente:
                flash(f'Já existe outro centro de custo com o código "{codigo}"', 'danger')
                return redirect(url_for('financeiro.editar_centro_custo', id=id))
            centro.codigo = codigo
        
        # Conversões
        centro.orcamento_mensal = converter_valor_monetario(orcamento_mensal_str) if orcamento_mensal_str else None
        centro.centro_pai_id = int(centro_pai_id) if centro_pai_id else None
        
        db.session.commit()
        
        flash(f'Centro de custo "{centro.codigo} - {centro.nome}" atualizado com sucesso!', 'success')
        return redirect(url_for('financeiro.listar_centros_custo'))
    
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao atualizar centro de custo: {str(e)}', 'danger')
        return redirect(url_for('financeiro.editar_centro_custo', id=id))


@bp_financeiro.route('/centros-custo/<int:id>/excluir', methods=['POST'])
def excluir_centro_custo(id):
    """Exclui centro de custo (soft delete)."""
    try:
        centro = CentroCusto.query.get_or_404(id)
        
        # Verificar se há lançamentos vinculados
        lancamentos_vinculados = LancamentoFinanceiro.query.filter_by(
            centro_custo_id=id,
            ativo=True
        ).count()
        
        if lancamentos_vinculados > 0:
            flash(f'Não é possível excluir. Existem {lancamentos_vinculados} lançamento(s) vinculado(s) a este centro de custo.', 'danger')
            return redirect(url_for('financeiro.listar_centros_custo'))
        
        # Verificar se há centros filhos
        centros_filhos = CentroCusto.query.filter_by(
            centro_pai_id=id,
            ativo=True
        ).count()
        
        if centros_filhos > 0:
            flash(f'Não é possível excluir. Existem {centros_filhos} centro(s) de custo subordinado(s).', 'danger')
            return redirect(url_for('financeiro.listar_centros_custo'))
        
        # Soft delete
        centro.ativo = False
        centro.data_exclusao = datetime.utcnow()
        
        db.session.commit()
        
        flash(f'Centro de custo "{centro.codigo} - {centro.nome}" excluído com sucesso!', 'success')
        return redirect(url_for('financeiro.listar_centros_custo'))
    
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao excluir centro de custo: {str(e)}', 'danger')
        return redirect(url_for('financeiro.listar_centros_custo'))


@bp_financeiro.route('/centros-custo/<int:id>/relatorio')
def relatorio_centro_custo(id):
    """Relatório detalhado de um centro de custo."""
    try:
        centro = CentroCusto.query.get_or_404(id)
        
        # Filtros de período
        mes = request.args.get('mes', type=int) or date.today().month
        ano = request.args.get('ano', type=int) or date.today().year
        
        # Buscar todos os lançamentos do centro no período
        lancamentos = LancamentoFinanceiro.query.filter(
            LancamentoFinanceiro.centro_custo_id == id,
            LancamentoFinanceiro.ativo == True,
            db.extract('month', LancamentoFinanceiro.data_lancamento) == mes,
            db.extract('year', LancamentoFinanceiro.data_lancamento) == ano
        ).order_by(LancamentoFinanceiro.data_lancamento.desc()).all()
        
        # Calcular totais
        total_receitas = sum(float(l.valor) for l in lancamentos if l.tipo in ['receita', 'conta_receber'])
        total_despesas = sum(float(l.valor) for l in lancamentos if l.tipo in ['despesa', 'conta_pagar'])
        saldo = total_receitas - total_despesas
        
        # Calcular por categoria
        despesas_por_categoria = {}
        for lanc in lancamentos:
            if lanc.tipo in ['despesa', 'conta_pagar'] and lanc.categoria:
                if lanc.categoria not in despesas_por_categoria:
                    despesas_por_categoria[lanc.categoria] = 0
                despesas_por_categoria[lanc.categoria] += float(lanc.valor)
        
        # Ordenar por valor
        despesas_por_categoria = dict(sorted(despesas_por_categoria.items(), 
                                            key=lambda x: x[1], reverse=True))
        
        # Percentual do orçamento
        percentual_orcamento = 0
        if centro.orcamento_mensal and centro.orcamento_mensal > 0:
            percentual_orcamento = (total_despesas / float(centro.orcamento_mensal)) * 100
        
        return render_template('financeiro/centros_custo/relatorio.html',
                             centro=centro,
                             lancamentos=lancamentos,
                             total_receitas=total_receitas,
                             total_despesas=total_despesas,
                             saldo=saldo,
                             despesas_por_categoria=despesas_por_categoria,
                             percentual_orcamento=percentual_orcamento,
                             mes=mes,
                             ano=ano)
    
    except Exception as e:
        flash(f'Erro ao gerar relatório: {str(e)}', 'danger')
        return redirect(url_for('financeiro.listar_centros_custo'))


# Importar formatar_valor_real
from app.financeiro.financeiro_utils import formatar_valor_real


# =============================================================================
# CONCILIAÇÃO BANCÁRIA
# =============================================================================

@bp_financeiro.route('/conciliacao-bancaria')
def conciliacao_bancaria():
    """Página principal de conciliação bancária."""
    try:
        # Buscar contas bancárias ativas
        contas = ContaBancaria.query.filter_by(ativo=True).all()
        
        # Conta selecionada (via query string)
        conta_id = request.args.get('conta_id', type=int)
        conta_selecionada = None
        extratos_pendentes = []
        lancamentos_pendentes = []
        
        if conta_id:
            conta_selecionada = ContaBancaria.query.get(conta_id)
            if conta_selecionada:
                # Buscar extratos pendentes desta conta
                from app.financeiro.financeiro_model import ExtratoBancario
                extratos_pendentes = ExtratoBancario.get_pendentes(conta_id).all()
                
                # Buscar lançamentos não conciliados desta conta
                lancamentos_pendentes = LancamentoFinanceiro.query.filter_by(
                    conta_bancaria_id=conta_id,
                    ativo=True
                ).filter(
                    ~LancamentoFinanceiro.id.in_(
                        db.session.query(ExtratoBancario.lancamento_id).filter(
                            ExtratoBancario.lancamento_id.isnot(None)
                        )
                    )
                ).order_by(LancamentoFinanceiro.data_vencimento.desc()).limit(50).all()
        
        return render_template('financeiro/conciliacao_bancaria/conciliacao.html',
                             contas=contas,
                             conta_selecionada=conta_selecionada,
                             extratos_pendentes=extratos_pendentes,
                             lancamentos_pendentes=lancamentos_pendentes)
    
    except Exception as e:
        flash(f'Erro ao carregar conciliação: {str(e)}', 'danger')
        return redirect(url_for('financeiro.dashboard'))


@bp_financeiro.route('/conciliacao-bancaria/upload', methods=['GET', 'POST'])
def upload_extrato():
    """Upload de arquivo de extrato bancário."""
    if request.method == 'POST':
        try:
            # Validar arquivo
            if 'arquivo' not in request.files:
                flash('Nenhum arquivo selecionado.', 'warning')
                return redirect(url_for('financeiro.upload_extrato'))
            
            arquivo = request.files['arquivo']
            if arquivo.filename == '':
                flash('Nenhum arquivo selecionado.', 'warning')
                return redirect(url_for('financeiro.upload_extrato'))
            
            # Validar conta bancária
            conta_id = request.form.get('conta_bancaria_id', type=int)
            if not conta_id:
                flash('Selecione uma conta bancária.', 'warning')
                return redirect(url_for('financeiro.upload_extrato'))
            
            conta = ContaBancaria.query.get(conta_id)
            if not conta:
                flash('Conta bancária não encontrada.', 'danger')
                return redirect(url_for('financeiro.upload_extrato'))
            
            # Processar arquivo CSV
            import csv
            import io
            from app.financeiro.financeiro_model import ExtratoBancario
            
            # Ler arquivo
            stream = io.StringIO(arquivo.stream.read().decode("UTF-8"), newline=None)
            csv_reader = csv.DictReader(stream)
            
            # Formato esperado das colunas (pode variar por banco)
            # data,descricao,documento,valor,tipo
            
            contador = 0
            for row in csv_reader:
                try:
                    # Parsear data (formato DD/MM/YYYY)
                    data_str = row.get('data', '').strip()
                    if '/' in data_str:
                        dia, mes, ano = data_str.split('/')
                        data_movimento = date(int(ano), int(mes), int(dia))
                    else:
                        continue  # Pular linha sem data válida
                    
                    # Parsear descrição
                    descricao = row.get('descricao', '').strip()
                    if not descricao:
                        continue
                    
                    # Parsear valor
                    valor_str = row.get('valor', '0').strip()
                    valor = converter_valor_monetario(valor_str)
                    
                    # Tipo de movimento
                    tipo = row.get('tipo', 'debito').strip().lower()
                    if tipo not in ['debito', 'credito']:
                        tipo = 'debito' if valor < 0 else 'credito'
                    
                    # Documento (opcional)
                    documento = row.get('documento', '').strip()
                    
                    # Criar extrato
                    extrato = ExtratoBancario(
                        conta_bancaria_id=conta_id,
                        data_movimento=data_movimento,
                        descricao=descricao,
                        documento=documento,
                        valor=abs(valor),
                        tipo_movimento=tipo,
                        arquivo_origem=arquivo.filename
                    )
                    db.session.add(extrato)
                    contador += 1
                
                except Exception as e:
                    continue  # Pular linhas com erro
            
            db.session.commit()
            flash(f'Extrato importado com sucesso! {contador} lançamentos adicionados.', 'success')
            return redirect(url_for('financeiro.conciliacao_bancaria', conta_id=conta_id))
        
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao processar arquivo: {str(e)}', 'danger')
            return redirect(url_for('financeiro.upload_extrato'))
    
    # GET - Exibir formulário
    contas = ContaBancaria.query.filter_by(ativo=True).all()
    return render_template('financeiro/conciliacao_bancaria/upload.html', contas=contas)


@bp_financeiro.route('/conciliacao-bancaria/conciliar/<int:extrato_id>/<int:lancamento_id>', methods=['POST'])
def conciliar_manual(extrato_id, lancamento_id):
    """Conciliar manualmente um extrato com um lançamento."""
    try:
        from app.financeiro.financeiro_model import ExtratoBancario
        
        extrato = ExtratoBancario.query.get_or_404(extrato_id)
        lancamento = LancamentoFinanceiro.query.get_or_404(lancamento_id)
        
        # Verificar se já não está conciliado
        if extrato.conciliado:
            flash('Este extrato já está conciliado.', 'warning')
            return redirect(url_for('financeiro.conciliacao_bancaria', conta_id=extrato.conta_bancaria_id))
        
        # Realizar conciliação
        extrato.conciliar_com_lancamento(lancamento.id)
        
        flash('Conciliação realizada com sucesso!', 'success')
        return redirect(url_for('financeiro.conciliacao_bancaria', conta_id=extrato.conta_bancaria_id))
    
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao conciliar: {str(e)}', 'danger')
        return redirect(url_for('financeiro.conciliacao_bancaria'))


@bp_financeiro.route('/conciliacao-bancaria/desconciliar/<int:extrato_id>', methods=['POST'])
def desconciliar(extrato_id):
    """Desfazer conciliação de um extrato."""
    try:
        from app.financeiro.financeiro_model import ExtratoBancario
        
        extrato = ExtratoBancario.query.get_or_404(extrato_id)
        conta_id = extrato.conta_bancaria_id
        
        # Desfazer conciliação
        extrato.desconciliar()
        
        flash('Conciliação desfeita com sucesso!', 'success')
        return redirect(url_for('financeiro.conciliacao_bancaria', conta_id=conta_id))
    
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao desconciliar: {str(e)}', 'danger')
        return redirect(url_for('financeiro.conciliacao_bancaria'))


@bp_financeiro.route('/conciliacao-bancaria/historico')
def historico_conciliacao():
    """Histórico de conciliações realizadas."""
    try:
        from app.financeiro.financeiro_model import ExtratoBancario
        
        # Filtros
        conta_id = request.args.get('conta_id', type=int)
        
        # Buscar extratos conciliados
        query = ExtratoBancario.get_conciliados(conta_id)
        extratos = query.limit(100).all()
        
        # Buscar contas para filtro
        contas = ContaBancaria.query.filter_by(ativo=True).all()
        
        return render_template('financeiro/conciliacao_bancaria/historico.html',
                             extratos=extratos,
                             contas=contas,
                             conta_id=conta_id)
    
    except Exception as e:
        flash(f'Erro ao carregar histórico: {str(e)}', 'danger')
        return redirect(url_for('financeiro.dashboard'))
