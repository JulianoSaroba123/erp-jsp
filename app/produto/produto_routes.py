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
            
            # Coleta dados do formulário
            produto = Produto(
                nome=request.form.get('nome', '').strip(),
                descricao=request.form.get('descricao', '').strip(),
                codigo=request.form.get('codigo', '').strip(),
                codigo_barras=request.form.get('codigo_barras', '').strip(),
                categoria=request.form.get('categoria', '').strip(),
                subcategoria=request.form.get('subcategoria', '').strip(),
                marca=request.form.get('marca', '').strip(),
                modelo=request.form.get('modelo', '').strip(),
                unidade_medida=request.form.get('unidade_medida', 'UN'),
                peso=Decimal(request.form.get('peso', '0').replace(',', '.')) if request.form.get('peso') else None,
                dimensoes=request.form.get('dimensoes', '').strip(),
                preco_custo=Decimal(preco_custo) if preco_custo else 0,
                preco_venda=Decimal(preco_venda) if preco_venda else 0,
                markup=Decimal(markup) if markup else 0,
                estoque_atual=int(request.form.get('estoque_atual', 0)),
                estoque_minimo=int(request.form.get('estoque_minimo', 0)),
                estoque_maximo=int(request.form.get('estoque_maximo', 0)),
                controla_estoque=bool(request.form.get('controla_estoque')),
                status=request.form.get('status', 'ativo'),
                observacoes=request.form.get('observacoes', '').strip()
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
            
            # Atualiza dados
            produto.nome = request.form.get('nome', '').strip()
            produto.descricao = request.form.get('descricao', '').strip()
            novo_codigo = request.form.get('codigo', '').strip()
            novo_codigo_barras = request.form.get('codigo_barras', '').strip()
            produto.categoria = request.form.get('categoria', '').strip()
            produto.subcategoria = request.form.get('subcategoria', '').strip()
            produto.marca = request.form.get('marca', '').strip()
            produto.modelo = request.form.get('modelo', '').strip()
            produto.unidade_medida = request.form.get('unidade_medida', 'UN')
            produto.peso = Decimal(request.form.get('peso', '0').replace(',', '.')) if request.form.get('peso') else None
            produto.dimensoes = request.form.get('dimensoes', '').strip()
            produto.preco_custo = Decimal(preco_custo) if preco_custo else 0
            produto.preco_venda = Decimal(preco_venda) if preco_venda else 0
            produto.markup = Decimal(markup) if markup else 0
            produto.estoque_atual = int(request.form.get('estoque_atual', 0))
            produto.estoque_minimo = int(request.form.get('estoque_minimo', 0))
            produto.estoque_maximo = int(request.form.get('estoque_maximo', 0))
            produto.controla_estoque = bool(request.form.get('controla_estoque'))
            produto.status = request.form.get('status', 'ativo')
            produto.observacoes = request.form.get('observacoes', '').strip()
            
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