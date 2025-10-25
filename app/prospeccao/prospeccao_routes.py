# -*- coding: utf-8 -*-
"""
ERP JSP v3.0 - Routes de Prospecção
===================================

Rotas para prospecção de clientes.

Autor: JSP Soluções
Data: 2025
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from app.extensoes import db
from app.prospeccao.prospeccao_model import Prospect, buscar_empresas
import logging

# Configurar logging
logger = logging.getLogger(__name__)

# Cria o blueprint
prospeccao_bp = Blueprint('prospeccao', __name__, 
                         template_folder='templates',
                         url_prefix='/prospeccao')

@prospeccao_bp.route('/')
@prospeccao_bp.route('/dashboard')
def dashboard():
    """Dashboard de prospecção."""
    try:
        # Estatísticas básicas
        total_prospects = Prospect.query.filter_by(ativo=True).count()
        prospects_ativos = Prospect.query.filter_by(ativo=True, status='ativo').count()
        prospects_convertidos = Prospect.query.filter_by(ativo=True, status='convertido').count()
        
        # Últimos prospects
        ultimos_prospects = Prospect.query.filter_by(ativo=True).order_by(
            Prospect.criado_em.desc()
        ).limit(10).all()
        
        return render_template('prospeccao/dashboard.html',
                             total_prospects=total_prospects,
                             prospects_ativos=prospects_ativos,
                             prospects_convertidos=prospects_convertidos,
                             ultimos_prospects=ultimos_prospects)
    except Exception as e:
        logger.error(f"Erro no dashboard de prospecção: {e}")
        flash(f"Erro ao carregar dashboard: {e}", 'danger')
        return render_template('prospeccao/dashboard.html')

@prospeccao_bp.route('/buscar', methods=['GET', 'POST'])
def buscar():
    """Busca de empresas por filtros."""
    resultados = []
    filtros = {
        'cnpj': '',
        'cnae': '',
        'cidade': '',
        'estado': ''
    }
    
    if request.method == 'POST':
        try:
            # Captura os filtros do formulário
            filtros['cnpj'] = request.form.get('cnpj', '').strip()
            filtros['cnae'] = request.form.get('cnae', '').strip()
            filtros['cidade'] = request.form.get('cidade', '').strip()
            filtros['estado'] = request.form.get('estado', '').strip().upper()
            
            # Valida se ao menos um filtro foi informado
            if not any(filtros.values()):
                flash('Informe ao menos um filtro para a busca.', 'warning')
                return render_template('prospeccao/busca.html', 
                                     filtros=filtros, 
                                     resultados=resultados)
            
            # Busca empresas
            resultados = buscar_empresas(
                cnpj=filtros['cnpj'] or None,
                cnae=filtros['cnae'] or None,
                cidade=filtros['cidade'] or None,
                estado=filtros['estado'] or None
            )
            
            if resultados:
                flash(f'Encontradas {len(resultados)} empresa(s).', 'success')
            else:
                flash('Nenhuma empresa encontrada com os filtros informados.', 'info')
                
        except Exception as e:
            logger.error(f"Erro na busca de empresas: {e}")
            flash(f'Erro ao buscar empresas: {e}', 'danger')
    
    return render_template('prospeccao/busca.html', 
                         filtros=filtros, 
                         resultados=resultados)

@prospeccao_bp.route('/salvar/<cnpj>', methods=['POST'])
def salvar(cnpj):
    """Salva um prospect no banco de dados."""
    try:
        # Verifica se o prospect já existe
        prospect_existente = Prospect.buscar_por_cnpj(cnpj)
        if prospect_existente:
            flash(f'Empresa com CNPJ {cnpj} já está cadastrada como prospect.', 'warning')
            return redirect(url_for('prospeccao.buscar'))
        
        # Captura dados do formulário
        dados = {
            'cnpj': cnpj,
            'razao_social': request.form.get('razao_social', ''),
            'nome_fantasia': request.form.get('nome_fantasia', ''),
            'cnae': request.form.get('cnae', ''),
            'cidade': request.form.get('cidade', ''),
            'estado': request.form.get('estado', ''),
            'telefone': request.form.get('telefone', ''),
            'email': request.form.get('email', ''),
            'origem': 'busca_cnae'
        }
        
        # Valida dados obrigatórios
        if not dados['razao_social']:
            flash('Razão social é obrigatória.', 'danger')
            return redirect(url_for('prospeccao.buscar'))
        
        # Cria novo prospect
        novo_prospect = Prospect(**dados)
        db.session.add(novo_prospect)
        db.session.commit()
        
        logger.info(f"Prospect salvo: {cnpj} - {dados['razao_social']}")
        flash(f'Prospect {dados["razao_social"]} salvo com sucesso!', 'success')
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erro ao salvar prospect {cnpj}: {e}")
        flash(f'Erro ao salvar prospect: {e}', 'danger')
    
    return redirect(url_for('prospeccao.buscar'))

@prospeccao_bp.route('/listar')
def listar():
    """Lista todos os prospects."""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = 20
        
        # Filtros
        status_filtro = request.args.get('status', '')
        cidade_filtro = request.args.get('cidade', '')
        estado_filtro = request.args.get('estado', '')
        
        # Query base
        query = Prospect.query.filter_by(ativo=True)
        
        # Aplica filtros
        if status_filtro:
            query = query.filter_by(status=status_filtro)
        if cidade_filtro:
            query = query.filter(Prospect.cidade.ilike(f'%{cidade_filtro}%'))
        if estado_filtro:
            query = query.filter(Prospect.estado.ilike(f'%{estado_filtro}%'))
        
        # Paginação
        prospects = query.order_by(Prospect.criado_em.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return render_template('prospeccao/listar.html', 
                             prospects=prospects,
                             status_filtro=status_filtro,
                             cidade_filtro=cidade_filtro,
                             estado_filtro=estado_filtro)
                             
    except Exception as e:
        logger.error(f"Erro ao listar prospects: {e}")
        flash(f'Erro ao carregar prospects: {e}', 'danger')
        return redirect(url_for('prospeccao.dashboard'))

@prospeccao_bp.route('/prospect/<int:id>')
def detalhar(id):
    """Exibe detalhes de um prospect."""
    try:
        prospect = Prospect.query.get_or_404(id)
        return render_template('prospeccao/detalhar.html', prospect=prospect)
    except Exception as e:
        logger.error(f"Erro ao carregar prospect {id}: {e}")
        flash(f'Erro ao carregar prospect: {e}', 'danger')
        return redirect(url_for('prospeccao.listar'))

@prospeccao_bp.route('/prospect/<int:id>/converter', methods=['POST'])
def converter(id):
    """Converte um prospect em cliente."""
    try:
        prospect = Prospect.query.get_or_404(id)
        prospect.status = 'convertido'
        db.session.commit()
        
        flash(f'Prospect {prospect.razao_social} marcado como convertido!', 'success')
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erro ao converter prospect {id}: {e}")
        flash(f'Erro ao converter prospect: {e}', 'danger')
    
    return redirect(url_for('prospeccao.detalhar', id=id))

@prospeccao_bp.route('/prospect/<int:id>/excluir', methods=['POST'])
def excluir(id):
    """Exclui um prospect (soft delete)."""
    try:
        prospect = Prospect.query.get_or_404(id)
        prospect.ativo = False
        db.session.commit()
        
        flash(f'Prospect {prospect.razao_social} excluído com sucesso!', 'success')
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erro ao excluir prospect {id}: {e}")
        flash(f'Erro ao excluir prospect: {e}', 'danger')
    
    return redirect(url_for('prospeccao.listar'))