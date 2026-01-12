# -*- coding: utf-8 -*-
"""
ERP JSP v3.0 - Routes de Concessionária
========================================

Rotas para gerenciamento de concessionárias de energia elétrica.
CRUD completo com validações.

Autor: JSP Soluções
Data: 2026
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required
from datetime import date, datetime
from app.extensoes import db
from app.concessionaria.concessionaria_model import Concessionaria

# Cria o blueprint
concessionaria_bp = Blueprint('concessionaria', __name__, 
                             url_prefix='/concessionarias',
                             template_folder='templates')


@concessionaria_bp.route('/')
@concessionaria_bp.route('/listar')
@login_required
def listar():
    """Lista todas as concessionárias ativas."""
    busca = request.args.get('busca', '').strip()
    
    if busca:
        concessionarias = Concessionaria.query.filter(
            db.or_(
                Concessionaria.nome.ilike(f'%{busca}%'),
                Concessionaria.regiao.ilike(f'%{busca}%')
            ),
            Concessionaria.ativo == True
        ).order_by(Concessionaria.nome).all()
    else:
        concessionarias = Concessionaria.query.filter_by(ativo=True).order_by(Concessionaria.nome).all()
    
    return render_template('concessionaria/listar.html', 
                         concessionarias=concessionarias, 
                         busca=busca)


@concessionaria_bp.route('/novo', methods=['GET', 'POST'])
@login_required
def novo():
    """Cria uma nova concessionária."""
    if request.method == 'POST':
        try:
            # Criar nova concessionária
            concessionaria = Concessionaria(
                nome=request.form.get('nome'),
                regiao=request.form.get('regiao'),
                te=float(request.form.get('te') or 0),
                tusd=float(request.form.get('tusd') or 0),
                pis=float(request.form.get('pis') or 0),
                cofins=float(request.form.get('cofins') or 0),
                icms=float(request.form.get('icms') or 0),
                data_atualizacao=date.today(),
                ativo=True
            )
            
            db.session.add(concessionaria)
            db.session.commit()
            
            flash(f'Concessionária {concessionaria.nome} cadastrada com sucesso!', 'success')
            return redirect(url_for('concessionaria.listar'))
            
        except ValueError as e:
            flash(f'Erro nos valores numéricos: {str(e)}', 'error')
            return render_template('concessionaria/form.html')
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao cadastrar concessionária: {str(e)}', 'error')
            return render_template('concessionaria/form.html')
    
    return render_template('concessionaria/form.html')


@concessionaria_bp.route('/editar/<int:id>', methods=['GET', 'POST'])
@login_required
def editar(id):
    """Edita uma concessionária existente."""
    concessionaria = Concessionaria.query.get_or_404(id)
    
    if request.method == 'POST':
        try:
            # Atualizar dados
            concessionaria.nome = request.form.get('nome')
            concessionaria.regiao = request.form.get('regiao')
            concessionaria.te = float(request.form.get('te') or 0)
            concessionaria.tusd = float(request.form.get('tusd') or 0)
            concessionaria.pis = float(request.form.get('pis') or 0)
            concessionaria.cofins = float(request.form.get('cofins') or 0)
            concessionaria.icms = float(request.form.get('icms') or 0)
            concessionaria.data_atualizacao = date.today()
            
            db.session.commit()
            
            flash(f'Concessionária {concessionaria.nome} atualizada com sucesso!', 'success')
            return redirect(url_for('concessionaria.listar'))
            
        except ValueError as e:
            flash(f'Erro nos valores numéricos: {str(e)}', 'error')
            return render_template('concessionaria/form.html', concessionaria=concessionaria)
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao atualizar concessionária: {str(e)}', 'error')
            return render_template('concessionaria/form.html', concessionaria=concessionaria)
    
    return render_template('concessionaria/form.html', concessionaria=concessionaria)


@concessionaria_bp.route('/excluir/<int:id>', methods=['POST'])
@login_required
def excluir(id):
    """Desativa uma concessionária (soft delete)."""
    concessionaria = Concessionaria.query.get_or_404(id)
    
    try:
        concessionaria.ativo = False
        db.session.commit()
        flash(f'Concessionária {concessionaria.nome} desativada com sucesso!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao desativar concessionária: {str(e)}', 'error')
    
    return redirect(url_for('concessionaria.listar'))


@concessionaria_bp.route('/api/listar')
@login_required
def api_listar():
    """API: Lista concessionárias ativas para select."""
    concessionarias = Concessionaria.query.filter_by(ativo=True).order_by(Concessionaria.nome).all()
    
    return jsonify({
        'success': True,
        'data': [c.to_dict() for c in concessionarias]
    })


@concessionaria_bp.route('/api/detalhes/<int:id>')
@login_required
def api_detalhes(id):
    """API: Retorna detalhes de uma concessionária."""
    concessionaria = Concessionaria.query.get_or_404(id)
    
    return jsonify({
        'success': True,
        'data': concessionaria.to_dict()
    })
