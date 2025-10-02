from flask import Blueprint, render_template, request, redirect, url_for, jsonify, flash
from aplicacao.servico.servico_model import Servico
from aplicacao.extensoes import db

# Blueprint no nome "servico" para casar com url_for('servico.*')
servico_bp = Blueprint('servico', __name__, url_prefix='/servicos', template_folder='templates')

# ---------- Utils ----------
def _pt_to_float(s: str) -> float:
    s = (s or "").strip()
    if not s:
        return 0.0
    # aceita "1.234,56" e "1234.56"
    s = s.replace(".", "").replace(",", ".")
    try:
        return float(s)
    except ValueError:
        return 0.0

def _get_any(form, *keys, default="0"):
    for k in keys:
        if k in form:
            return form.get(k)
    return default

def _preco_row(s: Servico) -> float:
    """Retorna preço de venda (que inclui markup) como valor principal."""
    # Prioridade: preco_venda (com markup) -> valor -> 0
    preco_venda = getattr(s, "preco_venda", None)
    if preco_venda and preco_venda > 0:
        return preco_venda
    
    # Fallback para valor se preco_venda não estiver definido
    valor = getattr(s, "valor", None)
    if valor and valor > 0:
        return valor
    
    return 0.0

def gerar_codigo_servico():
    ultimo = Servico.query.order_by(Servico.id.desc()).first()
    if not ultimo or not (ultimo.codigo or "").startswith("SRV"):
        return "SRV0001"
    numero = int(ultimo.codigo[3:]) + 1
    return f"SRV{numero:04d}"

# ---------- API para autocomplete ----------
@servico_bp.route('/api/busca', methods=['GET'])
def api_busca_servicos():
    termo = (request.args.get('q') or '').strip()
    query = Servico.query.filter(Servico.ativo == True)
    if termo:
        query = query.filter(Servico.nome.ilike(f'%{termo}%'))
    servicos = query.order_by(Servico.nome).limit(20).all()
    return jsonify([
        {
            'id': s.id,
            'nome': s.nome,
            'valor': _preco_row(s),
            'descricao': s.descricao or ''
        } for s in servicos
    ])

# ---------- API para buscar servico por ID ----------
@servico_bp.route('/api/servico/<int:id>', methods=['GET'])
def api_buscar_servico_por_id(id):
    servico = Servico.query.filter_by(id=id, ativo=True).first()
    if not servico:
        return jsonify({'error': 'Serviço não encontrado'}), 404
    
    return jsonify({
        'id': servico.id,
        'nome': servico.nome,
        'descricao': servico.descricao or '',
        'valor': getattr(servico, 'valor', None),
        'preco_venda': getattr(servico, 'preco_venda', None),
        'preco_custo': getattr(servico, 'preco_custo', None),
        'markup_percentual': getattr(servico, 'markup_percentual', 0),
        'unidade': getattr(servico, 'unidade', 'UN'),
        'valor_hora': getattr(servico, 'preco_venda', None) or getattr(servico, 'valor', 0) or 0  # Preco_venda (com markup) como prioridade
    })

# ---------- Listagem ----------
@servico_bp.route('/')
def listar_servicos():
    servicos = Servico.query.filter_by(ativo=True).all()

    total_servicos = len(servicos)
    # usa 'valor' se existir, senão 'preco_venda'
    valor_total = sum((getattr(s, 'valor', None) or getattr(s, 'preco_venda', 0) or 0) for s in servicos)
    valor_medio = (valor_total / total_servicos) if total_servicos else 0

    return render_template('servico/lista.html',
                           servicos=servicos,
                           total_servicos=total_servicos,
                           valor_total=valor_total,
                           valor_medio=valor_medio)

# ---------- Novo ----------
@servico_bp.route('/novo', methods=['GET', 'POST'])
def novo_servico():
    if request.method == 'POST':
        servico = Servico()
        servico.codigo = gerar_codigo_servico()
        servico.nome = request.form['nome']
        servico.descricao = request.form.get('descricao')
        servico.unidade = request.form.get('unidade', 'UN')

        # aceita vírgula
        servico.preco_custo = float((request.form.get('preco_custo', '0') or '0').replace(',', '.'))

        # salva markup no campo que existir
        mk = float((request.form.get('markup_percentual', request.form.get('markup', '0')) or '0').replace(',', '.'))
        if hasattr(servico, 'markup_percentual'):
            servico.markup_percentual = mk
        elif hasattr(servico, 'markup'):
            servico.markup = mk

        # cálculo fica no Model
        try:
            servico.calcular_preco_venda(mk)
        except TypeError:
            servico.calcular_preco_venda()

        db.session.add(servico)
        db.session.commit()
        return redirect(url_for('servico.listar_servicos'))

    # 👇 evita acessar atributo inexistente no template
    return render_template('servico/cadastro.html', markup_valor=0)


# ---------- Editar ----------
@servico_bp.route('/editar/<int:id>', methods=['GET', 'POST'])
def editar_servico(id):
    servico = Servico.query.get_or_404(id)
    if request.method == 'POST':
        servico.nome = request.form['nome']
        servico.descricao = request.form.get('descricao')
        servico.unidade = request.form.get('unidade', 'UN')

        servico.preco_custo = float((request.form.get('preco_custo', '0') or '0').replace(',', '.'))

        mk = float((request.form.get('markup_percentual', request.form.get('markup', '0')) or '0').replace(',', '.'))
        if hasattr(servico, 'markup_percentual'):
            servico.markup_percentual = mk
        elif hasattr(servico, 'markup'):
            servico.markup = mk

        try:
            servico.calcular_preco_venda(mk)
        except TypeError:
            servico.calcular_preco_venda()

        db.session.commit()
        return redirect(url_for('servico.listar_servicos'))

    # 👇 prepara valor seguro para o template
    mk_val = getattr(servico, 'markup_percentual', None)
    if mk_val is None:
        mk_val = getattr(servico, 'markup', 0)
    return render_template('servico/cadastro.html', servico=servico, markup_valor=mk_val)



# ---------- Excluir (soft-delete) ----------
@servico_bp.route('/excluir/<int:id>', methods=['POST'])
def excluir_servico(id):
    servico = Servico.query.get_or_404(id)
    if hasattr(servico, 'ativo'):
        servico.ativo = False
    else:
        db.session.delete(servico)
        db.session.commit()
        return redirect(url_for('servico.listar_servicos'))
    db.session.commit()
    flash("Serviço removido.", "warning")
    return redirect(url_for('servico.listar_servicos'))
