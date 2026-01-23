# -*- coding: utf-8 -*-
"""
ERP JSP v3.0 - Routes de Produto
=================================

Rotas para gerenciamento de produtos.
CRUD completo com controle de estoque.

Autor: JSP Soluções
Data: 2025
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from app.extensoes import db
from app.produto.produto_model import Produto
from decimal import Decimal

# Cria o blueprint
produto_bp = Blueprint('produto', __name__, template_folder='templates')

@produto_bp.route('/')
@produto_bp.route('/listar')
def listar():
    """
    Lista todos os produtos ativos.
    
    Suporte para busca por nome, código ou categoria.
    """
    # Parâmetros de busca
    busca = request.args.get('busca', '').strip()
    categoria = request.args.get('categoria', '').strip()
    status = request.args.get('status', '').strip()
    
    # Query base
    query = Produto.query.filter_by(ativo=True)
    
    # Aplica filtros se houver busca
    if busca:
        query = query.filter(
            db.or_(
                Produto.nome.ilike(f'%{busca}%'),
                Produto.codigo.ilike(f'%{busca}%'),
                Produto.codigo_barras.ilike(f'%{busca}%'),
                Produto.marca.ilike(f'%{busca}%')
            )
        )
    
    # Filtro por categoria
    if categoria:
        query = query.filter(Produto.categoria.ilike(f'%{categoria}%'))
    
    # Filtro por status
    if status:
        query = query.filter_by(status=status)
    
    # Ordena por nome
    produtos = query.order_by(Produto.nome).all()
    
    # Lista de categorias para filtro
    categorias = db.session.query(Produto.categoria).filter(
        Produto.categoria.isnot(None),
        Produto.ativo == True
    ).distinct().all()
    categorias = [cat[0] for cat in categorias if cat[0]]
    
    return render_template('produto/listar.html', 
                         produtos=produtos, 
                         busca=busca,
                         categoria=categoria,
                         status=status,
                         categorias=categorias)

@produto_bp.route('/novo', methods=['GET', 'POST'])
def novo():
    """
    Cria um novo produto.
    
    GET: Exibe formulário
    POST: Processa criação
    """
    if request.method == 'POST':
        try:
            # Converte preços
            preco_custo = request.form.get('preco_custo', '0').replace(',', '.')
            preco_venda = request.form.get('preco_venda', '0').replace(',', '.')
            markup = request.form.get('markup', '0').replace(',', '.')
            
            # Função auxiliar para converter string vazia em None
            def get_or_none(field_name):
                value = request.form.get(field_name, '').strip()
                return value if value else None
            
            # Coleta dados do formulário
            produto = Produto(
                nome=request.form.get('nome', '').strip(),
                descricao=get_or_none('descricao'),
                codigo=get_or_none('codigo'),
                codigo_barras=get_or_none('codigo_barras'),
                categoria=get_or_none('categoria'),
                subcategoria=get_or_none('subcategoria'),
                marca=get_or_none('marca'),
                modelo=get_or_none('modelo'),
                unidade_medida=request.form.get('unidade_medida', 'UN'),
                peso=Decimal(request.form.get('peso', '0').replace(',', '.')) if request.form.get('peso') else None,
                dimensoes=get_or_none('dimensoes'),
                preco_custo=Decimal(preco_custo) if preco_custo else 0,
                preco_venda=Decimal(preco_venda) if preco_venda else 0,
                markup=Decimal(markup) if markup else 0,
                estoque_atual=int(request.form.get('estoque_atual', 0)),
                estoque_minimo=int(request.form.get('estoque_minimo', 0)),
                estoque_maximo=int(request.form.get('estoque_maximo', 0)),
                controla_estoque=bool(request.form.get('controla_estoque')),
                status=request.form.get('status', 'ativo'),
                observacoes=get_or_none('observacoes')
            )
            
            # Validações
            if not produto.nome:
                flash('Nome é obrigatório!', 'error')
                return render_template('produto/form.html', produto=produto)
            
            # Verifica se código já existe
            if produto.codigo:
                existe = Produto.buscar_por_codigo(produto.codigo)
                if existe:
                    flash('Código já existe!', 'error')
                    return render_template('produto/form.html', produto=produto)
            
            # Verifica se código de barras já existe
            if produto.codigo_barras:
                existe = Produto.buscar_por_codigo_barras(produto.codigo_barras)
                if existe:
                    flash('Código de barras já existe!', 'error')
                    return render_template('produto/form.html', produto=produto)
            
            # Calcula margem se não informada
            if produto.preco_custo and produto.preco_venda:
                produto.margem_lucro = Decimal(produto.margem_lucro_calculada)
            
            # Salva produto
            produto.save()
            
            flash(f'Produto "{produto.nome}" criado com sucesso!', 'success')
            return redirect(url_for('produto.listar'))
            
        except Exception as e:
            flash(f'Erro ao criar produto: {str(e)}', 'error')
            return render_template('produto/form.html', produto=produto)
    
    # GET - exibe formulário vazio
    return render_template('produto/form.html', produto=Produto())

@produto_bp.route('/<int:id>')
def visualizar(id):
    """
    Visualiza detalhes de um produto.
    
    Args:
        id (int): ID do produto
    """
    produto = Produto.get_by_id(id)
    
    if not produto:
        flash('Produto não encontrado!', 'error')
        return redirect(url_for('produto.listar'))
    
    return render_template('produto/visualizar.html', produto=produto)

@produto_bp.route('/<int:id>/editar', methods=['GET', 'POST'])
def editar(id):
    """
    Edita um produto existente.
    
    Args:
        id (int): ID do produto
    """
    produto = Produto.get_by_id(id)
    
    if not produto:
        flash('Produto não encontrado!', 'error')
        return redirect(url_for('produto.listar'))
    
    if request.method == 'POST':
        try:
            # Converte preços
            preco_custo = request.form.get('preco_custo', '0').replace(',', '.')
            preco_venda = request.form.get('preco_venda', '0').replace(',', '.')
            markup = request.form.get('markup', '0').replace(',', '.')
            
            # Função auxiliar para converter string vazia em None
            def get_or_none(field_name):
                value = request.form.get(field_name, '').strip()
                return value if value else None
            
            # Atualiza dados
            produto.nome = request.form.get('nome', '').strip()
            produto.descricao = get_or_none('descricao')
            novo_codigo = get_or_none('codigo')
            novo_codigo_barras = get_or_none('codigo_barras')
            produto.categoria = get_or_none('categoria')
            produto.subcategoria = get_or_none('subcategoria')
            produto.marca = get_or_none('marca')
            produto.modelo = get_or_none('modelo')
            produto.unidade_medida = request.form.get('unidade_medida', 'UN')
            produto.peso = Decimal(request.form.get('peso', '0').replace(',', '.')) if request.form.get('peso') else None
            produto.dimensoes = get_or_none('dimensoes')
            produto.preco_custo = Decimal(preco_custo) if preco_custo else 0
            produto.preco_venda = Decimal(preco_venda) if preco_venda else 0
            produto.markup = Decimal(markup) if markup else 0
            produto.estoque_atual = int(request.form.get('estoque_atual', 0))
            produto.estoque_minimo = int(request.form.get('estoque_minimo', 0))
            produto.estoque_maximo = int(request.form.get('estoque_maximo', 0))
            produto.controla_estoque = bool(request.form.get('controla_estoque'))
            produto.status = request.form.get('status', 'ativo')
            produto.observacoes = get_or_none('observacoes')
            
            # Validações
            if not produto.nome:
                flash('Nome é obrigatório!', 'error')
                return render_template('produto/form.html', produto=produto)
            
            # Verifica se código mudou e já existe
            if novo_codigo and novo_codigo != produto.codigo:
                existe = Produto.buscar_por_codigo(novo_codigo)
                if existe:
                    flash('Código já existe!', 'error')
                    return render_template('produto/form.html', produto=produto)
            produto.codigo = novo_codigo
            
            # Verifica se código de barras mudou e já existe
            if novo_codigo_barras and novo_codigo_barras != produto.codigo_barras:
                existe = Produto.buscar_por_codigo_barras(novo_codigo_barras)
                if existe:
                    flash('Código de barras já existe!', 'error')
                    return render_template('produto/form.html', produto=produto)
            produto.codigo_barras = novo_codigo_barras
            
            # Atualiza margem
            if produto.preco_custo and produto.preco_venda:
                produto.margem_lucro = Decimal(produto.margem_lucro_calculada)
            
            # Salva alterações
            produto.save()
            
            flash(f'Produto "{produto.nome}" atualizado com sucesso!', 'success')
            return redirect(url_for('produto.visualizar', id=id))
            
        except Exception as e:
            flash(f'Erro ao atualizar produto: {str(e)}', 'error')
            return render_template('produto/form.html', produto=produto)
    
    # GET - exibe formulário preenchido
    return render_template('produto/form.html', produto=produto)

@produto_bp.route('/<int:id>/excluir')
def excluir(id):
    """
    Exclui (desativa) um produto.
    
    Args:
        id (int): ID do produto
    """
    produto = Produto.get_by_id(id)
    
    if not produto:
        flash('Produto não encontrado!', 'error')
        return redirect(url_for('produto.listar'))
    
    try:
        nome = produto.nome
        produto.soft_delete()
        flash(f'Produto "{nome}" excluído com sucesso!', 'success')
    except Exception as e:
        flash(f'Erro ao excluir produto: {str(e)}', 'error')
    
    return redirect(url_for('produto.listar'))

@produto_bp.route('/estoque-baixo')
def estoque_baixo():
    """Lista produtos com estoque baixo."""
    produtos = Produto.produtos_estoque_baixo()
    return render_template('produto/estoque_baixo.html', produtos=produtos)

@produto_bp.route('/api/buscar')
def api_buscar():
    """
    API para busca de produtos (para autocomplete).
    
    Returns:
        JSON: Lista de produtos encontrados
    """
    termo = request.args.get('q', '').strip()
    
    if not termo or len(termo) < 2:
        return jsonify([])
    
    produtos = Produto.query.filter(
        db.or_(
            Produto.nome.ilike(f'%{termo}%'),
            Produto.codigo.ilike(f'%{termo}%'),
            Produto.codigo_barras.ilike(f'%{termo}%')
        ),
        Produto.ativo == True
    ).limit(10).all()
    
    resultado = []
    for produto in produtos:
        resultado.append({
            'id': produto.id,
            'nome': produto.nome,
            'codigo': produto.codigo_display,
            'preco_venda': float(produto.preco_venda or 0),
            'estoque': produto.estoque_atual,
            'texto': f'{produto.nome} - {produto.codigo_display}'
        })
    
    return jsonify(resultado)