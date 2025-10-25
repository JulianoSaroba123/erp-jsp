# -*- coding: utf-8 -*-
"""
ERP JSP v3.0 - Routes de Fornecedor
====================================

Rotas para gerenciamento de fornecedores.
CRUD completo com validações.

Autor: JSP Soluções
Data: 2025
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from app.extensoes import db
from app.fornecedor.fornecedor_model import Fornecedor

# Cria o blueprint
fornecedor_bp = Blueprint('fornecedor', __name__, template_folder='templates')

@fornecedor_bp.route('/')
@fornecedor_bp.route('/listar')
def listar():
    """
    Lista todos os fornecedores ativos.
    
    Suporte para busca por nome, documento ou categoria.
    """
    # Parâmetros de busca
    busca = request.args.get('busca', '').strip()
    categoria = request.args.get('categoria', '').strip()
    
    # Query base
    query = Fornecedor.query.filter_by(ativo=True)
    
    # Aplica filtros se houver busca
    if busca:
        query = query.filter(
            db.or_(
                Fornecedor.nome.ilike(f'%{busca}%'),
                Fornecedor.nome_fantasia.ilike(f'%{busca}%'),
                Fornecedor.cnpj_cpf.ilike(f'%{busca}%'),
                Fornecedor.email.ilike(f'%{busca}%')
            )
        )
    
    # Filtro por categoria
    if categoria:
        query = query.filter(Fornecedor.categoria.ilike(f'%{categoria}%'))
    
    # Ordena por nome
    fornecedores = query.order_by(Fornecedor.nome).all()
    
    # Lista de categorias para filtro
    categorias = db.session.query(Fornecedor.categoria).filter(
        Fornecedor.categoria.isnot(None),
        Fornecedor.ativo == True
    ).distinct().all()
    categorias = [cat[0] for cat in categorias if cat[0]]
    
    return render_template('fornecedor/listar.html', 
                         fornecedores=fornecedores, 
                         busca=busca,
                         categoria=categoria,
                         categorias=categorias)

@fornecedor_bp.route('/novo', methods=['GET', 'POST'])
def novo():
    """
    Cria um novo fornecedor.
    
    GET: Exibe formulário
    POST: Processa criação
    """
    if request.method == 'POST':
        try:
            # Coleta dados do formulário
            fornecedor = Fornecedor(
                nome=request.form.get('nome', '').strip(),
                nome_fantasia=request.form.get('nome_fantasia', '').strip(),
                tipo=request.form.get('tipo', 'PJ'),
                cnpj_cpf=''.join(filter(str.isdigit, request.form.get('cnpj_cpf', ''))),
                inscricao_estadual=request.form.get('inscricao_estadual', '').strip(),
                inscricao_municipal=request.form.get('inscricao_municipal', '').strip(),
                email=request.form.get('email', '').strip(),
                telefone=request.form.get('telefone', '').strip(),
                celular=request.form.get('celular', '').strip(),
                site=request.form.get('site', '').strip(),
                contato_nome=request.form.get('contato_nome', '').strip(),
                contato_cargo=request.form.get('contato_cargo', '').strip(),
                contato_email=request.form.get('contato_email', '').strip(),
                contato_telefone=request.form.get('contato_telefone', '').strip(),
                cep=request.form.get('cep', '').strip(),
                endereco=request.form.get('endereco', '').strip(),
                numero=request.form.get('numero', '').strip(),
                complemento=request.form.get('complemento', '').strip(),
                bairro=request.form.get('bairro', '').strip(),
                cidade=request.form.get('cidade', '').strip(),
                estado=request.form.get('estado', '').strip(),
                categoria=request.form.get('categoria', '').strip(),
                condicoes_pagamento=request.form.get('condicoes_pagamento', '').strip(),
                prazo_entrega=request.form.get('prazo_entrega', '').strip(),
                observacoes=request.form.get('observacoes', '').strip()
            )
            
            # Validações
            if not fornecedor.nome:
                flash('Nome é obrigatório!', 'error')
                return render_template('fornecedor/form.html', fornecedor=fornecedor)
            
            if fornecedor.cnpj_cpf:
                # Verifica se documento já existe
                existe = Fornecedor.buscar_por_documento(fornecedor.cnpj_cpf)
                if existe:
                    flash('CNPJ/CPF já cadastrado!', 'error')
                    return render_template('fornecedor/form.html', fornecedor=fornecedor)
                
                # Valida formato do documento
                if not fornecedor.validar_documento():
                    flash('CNPJ/CPF inválido!', 'error')
                    return render_template('fornecedor/form.html', fornecedor=fornecedor)
            
            # Salva fornecedor
            fornecedor.save()
            
            flash(f'Fornecedor "{fornecedor.nome}" criado com sucesso!', 'success')
            return redirect(url_for('fornecedor.listar'))
            
        except Exception as e:
            flash(f'Erro ao criar fornecedor: {str(e)}', 'error')
            return render_template('fornecedor/form.html', fornecedor=fornecedor)
    
    # GET - exibe formulário vazio
    return render_template('fornecedor/form.html', fornecedor=Fornecedor())

@fornecedor_bp.route('/<int:id>')
def visualizar(id):
    """
    Visualiza detalhes de um fornecedor.
    
    Args:
        id (int): ID do fornecedor
    """
    fornecedor = Fornecedor.get_by_id(id)
    
    if not fornecedor:
        flash('Fornecedor não encontrado!', 'error')
        return redirect(url_for('fornecedor.listar'))
    
    return render_template('fornecedor/visualizar.html', fornecedor=fornecedor)

@fornecedor_bp.route('/<int:id>/editar', methods=['GET', 'POST'])
def editar(id):
    """
    Edita um fornecedor existente.
    
    Args:
        id (int): ID do fornecedor
    """
    fornecedor = Fornecedor.get_by_id(id)
    
    if not fornecedor:
        flash('Fornecedor não encontrado!', 'error')
        return redirect(url_for('fornecedor.listar'))
    
    if request.method == 'POST':
        try:
            # Atualiza dados
            fornecedor.nome = request.form.get('nome', '').strip()
            fornecedor.nome_fantasia = request.form.get('nome_fantasia', '').strip()
            fornecedor.tipo = request.form.get('tipo', 'PJ')
            novo_doc = ''.join(filter(str.isdigit, request.form.get('cnpj_cpf', '')))
            fornecedor.inscricao_estadual = request.form.get('inscricao_estadual', '').strip()
            fornecedor.inscricao_municipal = request.form.get('inscricao_municipal', '').strip()
            fornecedor.email = request.form.get('email', '').strip()
            fornecedor.telefone = request.form.get('telefone', '').strip()
            fornecedor.celular = request.form.get('celular', '').strip()
            fornecedor.site = request.form.get('site', '').strip()
            fornecedor.contato_nome = request.form.get('contato_nome', '').strip()
            fornecedor.contato_cargo = request.form.get('contato_cargo', '').strip()
            fornecedor.contato_email = request.form.get('contato_email', '').strip()
            fornecedor.contato_telefone = request.form.get('contato_telefone', '').strip()
            fornecedor.cep = request.form.get('cep', '').strip()
            fornecedor.endereco = request.form.get('endereco', '').strip()
            fornecedor.numero = request.form.get('numero', '').strip()
            fornecedor.complemento = request.form.get('complemento', '').strip()
            fornecedor.bairro = request.form.get('bairro', '').strip()
            fornecedor.cidade = request.form.get('cidade', '').strip()
            fornecedor.estado = request.form.get('estado', '').strip()
            fornecedor.categoria = request.form.get('categoria', '').strip()
            fornecedor.condicoes_pagamento = request.form.get('condicoes_pagamento', '').strip()
            fornecedor.prazo_entrega = request.form.get('prazo_entrega', '').strip()
            fornecedor.observacoes = request.form.get('observacoes', '').strip()
            
            # Validações
            if not fornecedor.nome:
                flash('Nome é obrigatório!', 'error')
                return render_template('fornecedor/form.html', fornecedor=fornecedor)
            
            # Verifica se documento mudou e se já existe
            if novo_doc and novo_doc != fornecedor.cnpj_cpf:
                existe = Fornecedor.buscar_por_documento(novo_doc)
                if existe:
                    flash('CNPJ/CPF já cadastrado!', 'error')
                    return render_template('fornecedor/form.html', fornecedor=fornecedor)
            
            fornecedor.cnpj_cpf = novo_doc
            
            # Valida formato do documento
            if fornecedor.cnpj_cpf and not fornecedor.validar_documento():
                flash('CNPJ/CPF inválido!', 'error')
                return render_template('fornecedor/form.html', fornecedor=fornecedor)
            
            # Salva alterações
            fornecedor.save()
            
            flash(f'Fornecedor "{fornecedor.nome}" atualizado com sucesso!', 'success')
            return redirect(url_for('fornecedor.visualizar', id=id))
            
        except Exception as e:
            flash(f'Erro ao atualizar fornecedor: {str(e)}', 'error')
            return render_template('fornecedor/form.html', fornecedor=fornecedor)
    
    # GET - exibe formulário preenchido
    return render_template('fornecedor/form.html', fornecedor=fornecedor)

@fornecedor_bp.route('/<int:id>/excluir')
def excluir(id):
    """
    Exclui (desativa) um fornecedor.
    
    Args:
        id (int): ID do fornecedor
    """
    fornecedor = Fornecedor.get_by_id(id)
    
    if not fornecedor:
        flash('Fornecedor não encontrado!', 'error')
        return redirect(url_for('fornecedor.listar'))
    
    try:
        nome = fornecedor.nome
        fornecedor.soft_delete()
        flash(f'Fornecedor "{nome}" excluído com sucesso!', 'success')
    except Exception as e:
        flash(f'Erro ao excluir fornecedor: {str(e)}', 'error')
    
    return redirect(url_for('fornecedor.listar'))

@fornecedor_bp.route('/api/buscar')
def api_buscar():
    """
    API para busca de fornecedores (para autocomplete).
    
    Returns:
        JSON: Lista de fornecedores encontrados
    """
    termo = request.args.get('q', '').strip()
    
    if not termo or len(termo) < 2:
        return jsonify([])
    
    fornecedores = Fornecedor.query.filter(
        db.or_(
            Fornecedor.nome.ilike(f'%{termo}%'),
            Fornecedor.nome_fantasia.ilike(f'%{termo}%'),
            Fornecedor.cnpj_cpf.ilike(f'%{termo}%')
        ),
        Fornecedor.ativo == True
    ).limit(10).all()
    
    resultado = []
    for fornecedor in fornecedores:
        resultado.append({
            'id': fornecedor.id,
            'nome': fornecedor.nome,
            'nome_fantasia': fornecedor.nome_fantasia or '',
            'documento': fornecedor.documento_formatado,
            'categoria': fornecedor.categoria or '',
            'texto': f'{fornecedor.nome_display} - {fornecedor.documento_formatado}'
        })
    
    return jsonify(resultado)

# Importa as rotas de API para consultas automáticas
from app.fornecedor import consultas_api