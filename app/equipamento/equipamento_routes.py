# -*- coding: utf-8 -*-
"""
ERP JSP v3.0 - Routes de Equipamento
====================================

Rotas para gerenciamento de equipamentos.
CRUD completo com integração aos clientes.

Autor: JSP Soluções
Data: 2026
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from app.extensoes import db
from app.equipamento.equipamento_model import Equipamento
from app.cliente.cliente_model import Cliente

# Cria o blueprint
equipamento_bp = Blueprint('equipamento', __name__, template_folder='templates', url_prefix='/equipamentos')


@equipamento_bp.route('/')
@equipamento_bp.route('/listar')
def listar():
    """Lista todos os equipamentos ativos."""
    busca = request.args.get('busca', '').strip()
    cliente_id = request.args.get('cliente_id', '').strip()
    
    query = Equipamento.query.filter_by(ativo=True)
    
    if busca:
        query = query.filter(
            db.or_(
                Equipamento.nome.ilike(f'%{busca}%'),
                Equipamento.marca.ilike(f'%{busca}%'),
                Equipamento.modelo.ilike(f'%{busca}%'),
                Equipamento.numero_serie.ilike(f'%{busca}%')
            )
        )
    
    if cliente_id:
        query = query.filter_by(cliente_id=cliente_id)
    
    equipamentos = query.order_by(Equipamento.nome).all()
    clientes = Cliente.query.filter_by(ativo=True).order_by(Cliente.nome).all()
    
    return render_template('equipamento/listar.html', 
                         equipamentos=equipamentos, 
                         clientes=clientes,
                         busca=busca,
                         cliente_id_filtro=cliente_id)


@equipamento_bp.route('/novo', methods=['GET', 'POST'])
def novo():
    """Cria um novo equipamento."""
    if request.method == 'POST':
        try:
            # Valida cliente
            cliente_id = request.form.get('cliente_id')
            if not cliente_id:
                flash('Selecione um cliente para o equipamento.', 'error')
                return redirect(url_for('equipamento.novo'))
            
            cliente = Cliente.query.get(cliente_id)
            if not cliente or not cliente.ativo:
                flash('Cliente inválido ou inativo.', 'error')
                return redirect(url_for('equipamento.novo'))
            
            # Cria novo equipamento
            equipamento = Equipamento(
                nome=request.form.get('nome'),
                descricao=request.form.get('descricao'),
                marca=request.form.get('marca'),
                modelo=request.form.get('modelo'),
                numero_serie=request.form.get('numero_serie'),
                tipo=request.form.get('tipo'),
                cliente_id=cliente_id,
                localizacao=request.form.get('localizacao'),
                ano_fabricacao=request.form.get('ano_fabricacao') or None,
                capacidade=request.form.get('capacidade'),
                tensao=request.form.get('tensao'),
                potencia=request.form.get('potencia'),
                observacoes=request.form.get('observacoes'),
                ativo=True
            )
            
            db.session.add(equipamento)
            db.session.commit()
            
            flash(f'Equipamento "{equipamento.nome}" cadastrado com sucesso!', 'success')
            return redirect(url_for('equipamento.listar'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao cadastrar equipamento: {str(e)}', 'error')
            print(f'ERRO ao criar equipamento: {e}')
    
    # GET - exibe formulário
    clientes = Cliente.query.filter_by(ativo=True).order_by(Cliente.nome).all()
    return render_template('equipamento/form.html', 
                         equipamento=None, 
                         clientes=clientes)


@equipamento_bp.route('/editar/<int:id>', methods=['GET', 'POST'])
def editar(id):
    """Edita um equipamento existente."""
    equipamento = Equipamento.query.get_or_404(id)
    
    if request.method == 'POST':
        try:
            # Valida cliente
            cliente_id = request.form.get('cliente_id')
            if not cliente_id:
                flash('Selecione um cliente para o equipamento.', 'error')
                return redirect(url_for('equipamento.editar', id=id))
            
            cliente = Cliente.query.get(cliente_id)
            if not cliente or not cliente.ativo:
                flash('Cliente inválido ou inativo.', 'error')
                return redirect(url_for('equipamento.editar', id=id))
            
            # Atualiza dados
            equipamento.nome = request.form.get('nome')
            equipamento.descricao = request.form.get('descricao')
            equipamento.marca = request.form.get('marca')
            equipamento.modelo = request.form.get('modelo')
            equipamento.numero_serie = request.form.get('numero_serie')
            equipamento.tipo = request.form.get('tipo')
            equipamento.cliente_id = cliente_id
            equipamento.localizacao = request.form.get('localizacao')
            equipamento.ano_fabricacao = request.form.get('ano_fabricacao') or None
            equipamento.capacidade = request.form.get('capacidade')
            equipamento.tensao = request.form.get('tensao')
            equipamento.potencia = request.form.get('potencia')
            equipamento.observacoes = request.form.get('observacoes')
            
            db.session.commit()
            
            flash(f'Equipamento "{equipamento.nome}" atualizado com sucesso!', 'success')
            return redirect(url_for('equipamento.listar'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao atualizar equipamento: {str(e)}', 'error')
            print(f'ERRO ao atualizar equipamento: {e}')
    
    # GET - exibe formulário
    clientes = Cliente.query.filter_by(ativo=True).order_by(Cliente.nome).all()
    return render_template('equipamento/form.html', 
                         equipamento=equipamento, 
                         clientes=clientes)


@equipamento_bp.route('/excluir/<int:id>', methods=['POST'])
def excluir(id):
    """Desativa um equipamento (soft delete)."""
    try:
        equipamento = Equipamento.query.get_or_404(id)
        equipamento.ativo = False
        db.session.commit()
        
        flash(f'Equipamento "{equipamento.nome}" removido com sucesso!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao remover equipamento: {str(e)}', 'error')
        print(f'ERRO ao excluir equipamento: {e}')
    
    return redirect(url_for('equipamento.listar'))


@equipamento_bp.route('/detalhes/<int:id>')
def detalhes(id):
    """Exibe detalhes de um equipamento."""
    equipamento = Equipamento.query.get_or_404(id)
    return render_template('equipamento/detalhes.html', equipamento=equipamento)


# === APIs ===

@equipamento_bp.route('/api/por-cliente/<int:cliente_id>')
def api_por_cliente(cliente_id):
    """
    API: Retorna equipamentos de um cliente específico.
    Usada para popular dropdown de equipamentos ao selecionar cliente na OS.
    """
    try:
        print(f"\n[DEBUG API] 🔍 Buscando equipamentos para cliente ID: {cliente_id}")
        equipamentos = Equipamento.buscar_por_cliente(cliente_id, apenas_ativos=True)
        print(f"[DEBUG API] 📦 Encontrados {len(equipamentos)} equipamentos")
        
        equipamentos_dict = [eq.to_dict() for eq in equipamentos]
        print(f"[DEBUG API] 📋 Dados dos equipamentos: {equipamentos_dict}")
        
        return jsonify({
            'success': True,
            'equipamentos': equipamentos_dict
        })
    except Exception as e:
        print(f"[DEBUG API] ❌ Erro ao buscar equipamentos: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@equipamento_bp.route('/api/detalhes/<int:id>')
def api_detalhes(id):
    """
    API: Retorna detalhes completos de um equipamento.
    Usada para auto-preencher campos ao selecionar equipamento na OS.
    """
    try:
        equipamento = Equipamento.query.get_or_404(id)
        
        return jsonify({
            'success': True,
            'equipamento': equipamento.to_dict()
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 404
