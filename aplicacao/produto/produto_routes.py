from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from aplicacao.extensoes import db
from aplicacao.produto.produto_model import Produto
from aplicacao.fornecedor.fornecedor_model import Fornecedor
import traceback
from datetime import datetime

produto_bp = Blueprint('produto', __name__, url_prefix='/produtos', template_folder='templates')


def gerar_codigo_produto():
    ultimo = Produto.query.order_by(Produto.id.desc()).first()
    if not ultimo or not ultimo.codigo or not ultimo.codigo.startswith('PRD'):
        return 'PRD0001'
    try:
        numero = int(ultimo.codigo[3:]) + 1
    except Exception:
        numero = 1
    return f'PRD{numero:04}'


@produto_bp.route('')
@produto_bp.route('/')
def listar_produtos():
    q = request.args.get('q', '').strip()
    page = request.args.get('pagina', type=int, default=1)
    per_page = 20
    try:
        query = Produto.query
        if q:
            like = f"%{q}%"
            query = query.filter(Produto.nome.ilike(like) | Produto.sku.ilike(like))
        pag = query.order_by(Produto.nome.asc()).paginate(page=page, per_page=per_page, error_out=False)
        ultima_alteracao = datetime.now().strftime('%d/%m/%Y %H:%M')
        return render_template('produto/lista.html', produtos=pag, paginacao=pag, q=q, ultima_alteracao=ultima_alteracao)
    except Exception as e:
        traceback.print_exc()
        flash(f'Erro ao listar produtos: {str(e)}', 'danger')
        return render_template('produto/lista.html', produtos=[], paginacao=None, q=q, ultima_alteracao=datetime.now().strftime('%d/%m/%Y %H:%M'))


@produto_bp.route('/cadastrar', methods=['GET', 'POST'])
def novo_produto():
    if request.method == 'POST':
        try:
            produto = Produto()
            produto.codigo = gerar_codigo_produto()
            produto.nome = request.form.get('nome')
            produto.sku = request.form.get('sku')
            fornecedor_id = request.form.get('fornecedor_id')
            produto.fornecedor_id = int(fornecedor_id) if fornecedor_id else None
            produto.preco = request.form.get('preco') or 0
            produto.custo = request.form.get('custo') or 0
            produto.markup = request.form.get('markup') or 0
            produto.estoque = request.form.get('estoque') or 0
            produto.unidade = request.form.get('unidade')
            produto.categoria = request.form.get('categoria')
            produto.descricao = request.form.get('descricao')
            produto.ativo = True if request.form.get('ativo') in ('on', '1', 'true') else False

            db.session.add(produto)
            db.session.commit()
            flash('Produto cadastrado com sucesso!', 'success')
            return redirect(url_for('produto.listar_produtos'))
        except Exception as e:
            db.session.rollback()
            traceback.print_exc()
            flash(f'Erro ao cadastrar produto: {str(e)}', 'danger')
            return render_template('produto/cadastro.html', produto=request.form, codigo_gerado=gerar_codigo_produto())

    return render_template('produto/cadastro.html', codigo_gerado=gerar_codigo_produto())


@produto_bp.route('/editar/<int:id>', methods=['GET', 'POST'])
def editar_produto(id):
    produto = Produto.query.get_or_404(id)
    if request.method == 'POST':
        try:
            produto.nome = request.form.get('nome')
            produto.sku = request.form.get('sku')
            fornecedor_id = request.form.get('fornecedor_id')
            produto.fornecedor_id = int(fornecedor_id) if fornecedor_id else None
            produto.preco = request.form.get('preco') or 0
            produto.custo = request.form.get('custo') or 0
            produto.markup = request.form.get('markup') or 0
            produto.estoque = request.form.get('estoque') or 0
            produto.unidade = request.form.get('unidade')
            produto.categoria = request.form.get('categoria')
            produto.descricao = request.form.get('descricao')
            produto.ativo = True if request.form.get('ativo') in ('on', '1', 'true') else False

            db.session.commit()
            flash('Produto atualizado com sucesso!', 'success')
            return redirect(url_for('produto.listar_produtos'))
        except Exception as e:
            db.session.rollback()
            traceback.print_exc()
            flash(f'Erro ao atualizar produto: {str(e)}', 'danger')

    return render_template('produto/cadastro.html', produto=produto, codigo_gerado=produto.codigo)


@produto_bp.route('/fornecedor_buscar')
def fornecedor_buscar():
    q = request.args.get('q', '').strip()
    if not q:
        return jsonify([])
    like = f"%{q}%"
    results = Fornecedor.query.filter(Fornecedor.nome.ilike(like)).limit(10).all()
    data = [{'id': f.id, 'nome': f.nome, 'codigo': f.codigo} for f in results]
    return jsonify(data)
