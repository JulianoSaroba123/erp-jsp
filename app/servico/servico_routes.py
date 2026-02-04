# -*- coding: utf-8 -*-
"""
ERP JSP v3.0 - Routes de Serviços
==================================

Rotas CRUD completo para gerenciamento de serviços.
Os serviços cadastrados podem ser adicionados às Ordens de Serviço.

Autor: JSP Soluções
Data: 2026
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from app.extensoes import db
from app.servico.servico_model import Servico

# Cria o blueprint
servico_bp = Blueprint('servico', __name__, template_folder='templates')

@servico_bp.route('/')
@servico_bp.route('/listar')
def listar():
    """Lista todos os serviços ativos."""
    # Filtros
    categoria = request.args.get('categoria', '')
    busca = request.args.get('busca', '').strip()
    
    query = Servico.query.filter_by(ativo=True)
    
    if categoria:
        query = query.filter_by(categoria=categoria)
    
    if busca:
        query = query.filter(
            db.or_(
                Servico.nome.ilike(f'%{busca}%'),
                Servico.codigo.ilike(f'%{busca}%'),
                Servico.descricao.ilike(f'%{busca}%')
            )
        )
    
    servicos = query.order_by(Servico.nome).all()
    
    # Estatísticas
    stats = Servico.estatisticas_dashboard()
    
    return render_template('servico/listar.html', 
                         servicos=servicos, 
                         stats=stats,
                         categoria_filtro=categoria,
                         busca=busca)

@servico_bp.route('/novo', methods=['GET', 'POST'])
def novo():
    """Cria um novo serviço."""
    if request.method == 'POST':
        try:
            # Gera código automaticamente se não fornecido
            codigo = request.form.get('codigo', '').strip()
            if not codigo:
                codigo = Servico.gerar_proximo_codigo()
            
            # Verifica se código já existe
            if Servico.query.filter_by(codigo=codigo).first():
                flash(f'Código {codigo} já está em uso!', 'error')
                return render_template('servico/form.html', servico=Servico())
            
            # Cria o serviço
            servico = Servico(
                codigo=codigo,
                nome=request.form.get('nome'),
                descricao=request.form.get('descricao'),
                categoria=request.form.get('categoria', 'outros'),
                tipo_cobranca=request.form.get('tipo_cobranca', 'servico'),
                valor_base=float(request.form.get('valor_base', 0) or 0),
                valor_minimo=float(request.form.get('valor_minimo', 0) or 0) if request.form.get('valor_minimo') else None,
                tempo_estimado=int(request.form.get('tempo_estimado', 0) or 0) if request.form.get('tempo_estimado') else None,
                tempo_estimado_min=int(request.form.get('tempo_estimado_min', 0) or 0) if request.form.get('tempo_estimado_min') else None,
                tempo_estimado_max=int(request.form.get('tempo_estimado_max', 0) or 0) if request.form.get('tempo_estimado_max') else None,
                prazo_garantia=int(request.form.get('prazo_garantia', 0) or 0),
                materiais_necessarios=request.form.get('materiais_necessarios'),
                observacoes=request.form.get('observacoes'),
                instrucoes_execucao=request.form.get('instrucoes_execucao'),
                requer_agendamento='requer_agendamento' in request.form,
                disponivel_app='disponivel_app' in request.form,
                destaque='destaque' in request.form,
                ativo=True
            )
            
            # Valida dados
            erros = servico.validar_dados()
            if erros:
                for erro in erros:
                    flash(erro, 'error')
                return render_template('servico/form.html', servico=servico)
            
            db.session.add(servico)
            db.session.commit()
            
            flash(f'Serviço {servico.nome} criado com sucesso!', 'success')
            return redirect(url_for('servico.listar'))
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ Erro ao criar serviço: {str(e)}")
            import traceback
            traceback.print_exc()
            flash(f'Erro ao criar serviço: {str(e)}', 'error')
    
    # GET - formulário vazio
    servico = Servico()
    servico.codigo = Servico.gerar_proximo_codigo()  # Sugerir próximo código
    return render_template('servico/form.html', servico=servico)

@servico_bp.route('/<int:id>/editar', methods=['GET', 'POST'])
def editar(id):
    """Edita um serviço existente."""
    servico = Servico.query.filter_by(id=id).first()
    
    if servico is None:
        flash(f'Serviço #{id} não encontrado.', 'error')
        return redirect(url_for('servico.listar'))
    
    if request.method == 'POST':
        try:
            # Verifica se código já está em uso por outro serviço
            novo_codigo = request.form.get('codigo', '').strip()
            if novo_codigo and novo_codigo != servico.codigo:
                if Servico.query.filter(Servico.codigo == novo_codigo, Servico.id != id).first():
                    flash(f'Código {novo_codigo} já está em uso!', 'error')
                    return render_template('servico/form.html', servico=servico)
            
            # Atualiza os campos
            servico.codigo = novo_codigo or servico.codigo
            servico.nome = request.form.get('nome')
            servico.descricao = request.form.get('descricao')
            servico.categoria = request.form.get('categoria')
            servico.tipo_cobranca = request.form.get('tipo_cobranca')
            servico.valor_base = float(request.form.get('valor_base', 0) or 0)
            servico.valor_minimo = float(request.form.get('valor_minimo', 0) or 0) if request.form.get('valor_minimo') else None
            servico.tempo_estimado = int(request.form.get('tempo_estimado', 0) or 0) if request.form.get('tempo_estimado') else None
            servico.tempo_estimado_min = int(request.form.get('tempo_estimado_min', 0) or 0) if request.form.get('tempo_estimado_min') else None
            servico.tempo_estimado_max = int(request.form.get('tempo_estimado_max', 0) or 0) if request.form.get('tempo_estimado_max') else None
            servico.prazo_garantia = int(request.form.get('prazo_garantia', 0) or 0)
            servico.materiais_necessarios = request.form.get('materiais_necessarios')
            servico.observacoes = request.form.get('observacoes')
            servico.instrucoes_execucao = request.form.get('instrucoes_execucao')
            servico.requer_agendamento = 'requer_agendamento' in request.form
            servico.disponivel_app = 'disponivel_app' in request.form
            servico.destaque = 'destaque' in request.form
            
            # Valida dados
            erros = servico.validar_dados()
            if erros:
                for erro in erros:
                    flash(erro, 'error')
                return render_template('servico/form.html', servico=servico)
            
            db.session.commit()
            
            flash(f'Serviço {servico.nome} atualizado com sucesso!', 'success')
            return redirect(url_for('servico.listar'))
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ Erro ao atualizar serviço: {str(e)}")
            import traceback
            traceback.print_exc()
            flash(f'Erro ao atualizar serviço: {str(e)}', 'error')
    
    return render_template('servico/form.html', servico=servico)

@servico_bp.route('/<int:id>')
def visualizar(id):
    """Visualiza um serviço específico."""
    servico = Servico.query.filter_by(id=id, ativo=True).first()
    
    if servico is None:
        flash(f'Serviço #{id} não encontrado ou foi excluído.', 'error')
        return redirect(url_for('servico.listar'))
    
    return render_template('servico/visualizar.html', servico=servico)

@servico_bp.route('/<int:id>/excluir', methods=['GET', 'POST'])
def excluir(id):
    """Exclui (desativa) um serviço."""
    servico = Servico.query.filter_by(id=id, ativo=True).first()
    
    if servico is None:
        flash(f'Serviço #{id} não encontrado ou já foi excluído.', 'error')
        return redirect(url_for('servico.listar'))
    
    if request.method == 'GET':
        # Mostrar página de confirmação
        return render_template('servico/confirmar_exclusao.html', servico=servico)
    
    # POST - realizar exclusão
    try:
        servico.ativo = False
        db.session.commit()
        
        flash(f'Serviço {servico.nome} excluído com sucesso!', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao excluir serviço: {str(e)}', 'error')
    
    return redirect(url_for('servico.listar'))

@servico_bp.route('/dashboard')
def dashboard():
    """Dashboard de serviços com estatísticas."""
    stats = Servico.estatisticas_dashboard()
    
    # Serviços em destaque
    destaques = Servico.listar_destaques()
    
    # Últimos serviços criados (usando criado_em que é o campo real)
    recentes = Servico.query.filter_by(ativo=True).order_by(Servico.criado_em.desc()).limit(5).all()
    
    return render_template('servico/dashboard.html', 
                         stats=stats,
                         destaques=destaques,
                         recentes=recentes)

# ===== APIs para uso em outras rotas =====

@servico_bp.route('/api/buscar')
def api_buscar():
    """API para busca de serviços via AJAX (para usar em Ordem de Serviço)."""
    termo = request.args.get('q', '').strip()
    categoria = request.args.get('categoria', '')
    
    if not termo or len(termo) < 2:
        # Se não tem busca, retorna todos disponíveis
        query = Servico.query.filter_by(ativo=True, disponivel_app=True)
    else:
        query = Servico.query.filter(
            db.or_(
                Servico.nome.ilike(f'%{termo}%'),
                Servico.codigo.ilike(f'%{termo}%')
            ),
            Servico.ativo == True,
            Servico.disponivel_app == True
        )
    
    if categoria:
        query = query.filter_by(categoria=categoria)
    
    servicos = query.order_by(Servico.nome).limit(20).all()
    
    resultado = []
    for servico in servicos:
        resultado.append({
            'id': servico.id,
            'codigo': servico.codigo,
            'nome': servico.nome,
            'categoria': servico.categoria_display,
            'tipo_cobranca': servico.tipo_cobranca,
            'tipo_cobranca_display': servico.tipo_cobranca_display,
            'valor_base': float(servico.valor_base),
            'valor_base_formatado': servico.valor_base_formatado,
            'tempo_estimado': servico.tempo_estimado,
            'prazo_garantia': servico.prazo_garantia,
            'texto': f'{servico.codigo} - {servico.nome} ({servico.valor_base_formatado})'
        })
    
    return jsonify(resultado)

@servico_bp.route('/api/<int:id>')
def api_detalhes(id):
    """API para obter detalhes de um serviço específico."""
    servico = Servico.query.filter_by(id=id, ativo=True).first()
    
    if not servico:
        return jsonify({'erro': 'Serviço não encontrado'}), 404
    
    return jsonify(servico.to_dict())

@servico_bp.route('/api/categorias')
def api_categorias():
    """API para listar categorias disponíveis."""
    from app.servico.servico_model import CATEGORIA_CHOICES
    return jsonify([{'value': cat[0], 'label': cat[1]} for cat in CATEGORIA_CHOICES])