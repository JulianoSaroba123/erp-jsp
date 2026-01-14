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
from app.financeiro.financeiro_model import LancamentoFinanceiro, CategoriaFinanceira
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
        
        # Últimos lançamentos
        ultimos_lancamentos = LancamentoFinanceiro.query.filter_by(ativo=True).order_by(
            LancamentoFinanceiro.criado_em.desc()
        ).limit(10).all()
        
        return render_template('financeiro/dashboard.html',
                             resumo=resumo,
                             vencidos=vencidos,
                             pendentes=pendentes,
                             contas_receber=contas_receber,
                             contas_pagar=contas_pagar,
                             ultimos_lancamentos=ultimos_lancamentos)
    
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
        
        return render_template('financeiro/form_lancamento.html',
                             clientes=clientes,
                             fornecedores=fornecedores,
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
        
        return render_template('financeiro/form_lancamento.html',
                             lancamento=lancamento,
                             clientes=clientes,
                             fornecedores=fornecedores,
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