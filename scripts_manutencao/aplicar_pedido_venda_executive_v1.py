# -*- coding: utf-8 -*-
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FORM = ROOT / "app/pedido/templates/pedido/form.html"
VIEW = ROOT / "app/pedido/templates/pedido/visualizar.html"
ROUTES = ROOT / "app/pedido/pedido_routes.py"
PC_ROUTES = ROOT / "app/pedido_compra/pedido_compra_routes.py"
PC_FORM = ROOT / "app/pedido_compra/templates/pedido_compra/form.html"


def replace_once(texto, antigo, novo, nome):
    qtd = texto.count(antigo)
    if qtd != 1:
        raise SystemExit(f"ABORTADO: esperado 1 marcador para {nome}, encontrado {qtd}.")
    return texto.replace(antigo, novo, 1)


# -----------------------------------------------------------------------------
# Pedido de Venda - formulario
# -----------------------------------------------------------------------------
form = FORM.read_text(encoding="utf-8")

form = form.replace(
    'data-descricao="{{ produto.nome }}"',
    'data-descricao="{{ produto.nome }}" data-valor="{{ produto.preco_venda or 0 }}"',
)
form = form.replace(
    'data-descricao="{{ servico.nome }}"',
    'data-descricao="{{ servico.nome }}" data-valor="{{ servico.valor_base or 0 }}"',
)

form = replace_once(
    form,
    """    function parseDecimalBr(value) {
        if (!value) return 0;
        const cleaned = String(value).replace('R$', '').replace(/\\s/g, '').replace(/\\./g, '').replace(',', '.');
        const num = Number(cleaned);
        return Number.isFinite(num) ? num : 0;
    }""",
    """    function parseDecimalBr(value) {
        if (!value) return 0;
        let texto = String(value).replace('R$', '').replace(/\\s/g, '').trim();
        const temVirgula = texto.includes(',');
        const temPonto = texto.includes('.');

        if (temVirgula && temPonto) {
            if (texto.lastIndexOf(',') > texto.lastIndexOf('.')) {
                texto = texto.replace(/\\./g, '').replace(',', '.');
            } else {
                texto = texto.replace(/,/g, '');
            }
        } else if (temVirgula) {
            texto = texto.replace(',', '.');
        }

        const num = Number(texto);
        return Number.isFinite(num) ? num : 0;
    }""",
    "parser decimal JS",
)

form = replace_once(
    form,
    """        const descricaoInput = row.querySelector('.item-descricao');
        if (descricaoInput && !descricaoInput.value.trim()) {
            descricaoInput.value = option.dataset.descricao || '';
        }
    }""",
    """        const descricaoInput = row.querySelector('.item-descricao');
        if (descricaoInput && !descricaoInput.value.trim()) {
            descricaoInput.value = option.dataset.descricao || '';
        }

        const valorInput = row.querySelector('.item-valor');
        if (valorInput && (!valorInput.value.trim() || parseDecimalBr(valorInput.value) === 0)) {
            valorInput.value = option.dataset.valor || '0';
        }
    }""",
    "preenchimento automatico de preco",
)

form = replace_once(
    form,
    '                <a href="{{ url_for(\'pedido.listar\') }}" class="btn btn-outline-secondary">Cancelar</a>',
    """                {% if pedido %}
                <a href="{{ url_for('pedido.visualizar', id=pedido.id) }}" class="btn btn-outline-secondary"><i class="fas fa-arrow-left me-1"></i>Voltar</a>
                {% else %}
                <a href="{{ url_for('pedido.listar') }}" class="btn btn-outline-secondary"><i class="fas fa-arrow-left me-1"></i>Voltar</a>
                {% endif %}""",
    "botao voltar formulario pedido venda",
)

FORM.write_text(form, encoding="utf-8")


# -----------------------------------------------------------------------------
# Pedido de Venda - rotas
# -----------------------------------------------------------------------------
routes = ROUTES.read_text(encoding="utf-8")
routes = replace_once(
    routes,
    "from app.pedido.pedido_model import Pedido, PedidoItem\n",
    "from app.pedido.pedido_model import Pedido, PedidoItem\nfrom app.pedido_compra.pedido_compra_model import PedidoCompra\n",
    "import PedidoCompra",
)

routes = replace_once(
    routes,
    """    itens = pedido.itens.order_by(PedidoItem.ordem.asc(), PedidoItem.id.asc()).all()
    return render_template("pedido/visualizar.html", pedido=pedido, itens=itens)


@pedido_bp.route("/<int:id>/editar", methods=["GET", "POST"])""",
    """    itens = pedido.itens.order_by(PedidoItem.ordem.asc(), PedidoItem.id.asc()).all()
    pedidos_compra = (
        PedidoCompra.query
        .filter(PedidoCompra.pedido_venda_id == pedido.id, PedidoCompra.ativo.is_(True))
        .order_by(PedidoCompra.id.desc())
        .all()
    )
    return render_template(
        "pedido/visualizar.html",
        pedido=pedido,
        itens=itens,
        pedidos_compra=pedidos_compra,
    )


@pedido_bp.route("/<int:id>/imprimir")
@login_required
def imprimir(id):
    pedido = _query_base_pedidos().filter(Pedido.id == id).first()
    if not pedido:
        flash("Pedido nao encontrado.", "error")
        return redirect(url_for("pedido.listar"))
    itens = pedido.itens.order_by(PedidoItem.ordem.asc(), PedidoItem.id.asc()).all()
    return render_template("pedido/imprimir.html", pedido=pedido, itens=itens)


@pedido_bp.route("/<int:id>/editar", methods=["GET", "POST"])""",
    "visualizacao e impressao pedido venda",
)
ROUTES.write_text(routes, encoding="utf-8")


# -----------------------------------------------------------------------------
# Pedido de Venda - visualizacao Executive V1
# -----------------------------------------------------------------------------
VIEW.write_text(r'''{% extends "base.html" %}
{% block title %}Pedido {{ pedido.numero }} - {{ super() }}{% endblock %}
{% block head %}
<link href="{{ url_for('static', filename='css/jsp-executive-suite-phase-e.css') }}?v={{ ASSET_VERSION }}" rel="stylesheet">
<style>
.pv-flow{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:.75rem;margin:1rem 0 1.25rem}.pv-step{border:1px solid #dfe6ec;border-radius:.5rem;padding:.75rem;background:#fff}.pv-step.is-done{border-color:#19a7ce;background:#f2fbfe}.pv-step-title{font-weight:700;color:#163A5C}.pv-step-meta{font-size:.78rem;color:#657581;margin-top:.25rem}.pv-origin{font-weight:700;color:#163A5C}@media(max-width:900px){.pv-flow{grid-template-columns:1fr 1fr}}
</style>
{% endblock %}
{% block breadcrumb %}<a href="{{ url_for('pedido.listar') }}">Pedidos</a><span class="breadcrumb-separator"><i class="fas fa-chevron-right"></i></span><span class="current-page">Visualizar</span>{% endblock %}
{% block content %}
<div class="card border-0 shadow-sm mb-4"><div class="card-body">
<div class="d-flex justify-content-between align-items-start mb-4 gap-3 flex-wrap">
<div><h3 class="mb-1"><i class="fas fa-shopping-cart me-2 text-info"></i>Pedido {{ pedido.numero }}</h3><p class="text-muted mb-0">Status: <span class="badge bg-secondary">{{ pedido.status_label }}</span></p></div>
<div class="d-flex gap-2 flex-wrap">
<a href="{{ url_for('pedido.listar') }}" class="btn btn-outline-secondary"><i class="fas fa-arrow-left me-1"></i>Voltar</a>
<a href="{{ url_for('pedido.editar', id=pedido.id) }}" class="btn btn-outline-warning"><i class="fas fa-edit me-1"></i>Editar</a>
<a href="{{ url_for('pedido.imprimir', id=pedido.id) }}" class="btn btn-outline-primary"><i class="fas fa-print me-1"></i>Imprimir</a>
<a href="{{ url_for('pedido_compra.novo', pedido_venda_id=pedido.id) }}" class="btn btn-primary"><i class="fas fa-shopping-basket me-1"></i>Gerar Pedido de Compra</a>
</div></div>

<div class="row g-3 mb-3">
<div class="col-lg-3 col-md-6"><strong>Cliente:</strong><br>{{ pedido.cliente.nome_exibicao if pedido.cliente else '-' }}</div>
<div class="col-lg-3 col-md-6"><strong>Origem:</strong><br><span class="pv-origin">{% if pedido.proposta %}{{ pedido.proposta.codigo }}{% else %}Venda direta{% endif %}</span></div>
<div class="col-lg-3 col-md-6"><strong>Data do Pedido:</strong><br>{{ pedido.data_pedido.strftime('%d/%m/%Y') if pedido.data_pedido else '-' }}</div>
<div class="col-lg-3 col-md-6"><strong>Prazo Previsto:</strong><br>{{ pedido.prazo_previsto.strftime('%d/%m/%Y') if pedido.prazo_previsto else '-' }}</div>
<div class="col-lg-3 col-md-6"><strong>Responsavel:</strong><br>{{ pedido.responsavel or '-' }}</div>
<div class="col-lg-3 col-md-6"><strong>Solicitante:</strong><br>{{ pedido.solicitante or '-' }}</div>
<div class="col-lg-3 col-md-6"><strong>Telefone:</strong><br>{{ pedido.telefone_contato or '-' }}</div>
<div class="col-lg-3 col-md-6"><strong>Email:</strong><br>{{ pedido.email_contato or '-' }}</div>
</div>

{% set tem_compra = pedidos_compra|length > 0 %}
{% set compra_recebida = pedidos_compra|selectattr('status','equalto','RECEBIDO')|list|length > 0 %}
<div><strong>Fluxo da Venda</strong></div>
<div class="pv-flow">
<div class="pv-step {% if pedido.status in ['CONFIRMADO','EM_EXECUCAO','CONCLUIDO'] %}is-done{% endif %}"><div class="pv-step-title">1. Venda confirmada</div><div class="pv-step-meta">Pedido comercial aceito</div></div>
<div class="pv-step {% if tem_compra %}is-done{% endif %}"><div class="pv-step-title">2. Compra / Separacao</div><div class="pv-step-meta">{% if tem_compra %}{{ pedidos_compra|length }} compra(s) vinculada(s){% else %}Aguardando necessidade de compra{% endif %}</div></div>
<div class="pv-step {% if compra_recebida %}is-done{% endif %}"><div class="pv-step-title">3. Material disponivel</div><div class="pv-step-meta">{% if compra_recebida %}Compra recebida{% else %}Aguardando recebimento/separacao{% endif %}</div></div>
<div class="pv-step {% if pedido.status == 'CONCLUIDO' %}is-done{% endif %}"><div class="pv-step-title">4. Entrega / Conclusao</div><div class="pv-step-meta">{% if pedido.status == 'CONCLUIDO' %}Venda concluida{% else %}Pendente{% endif %}</div></div>
</div>

<div class="cc-table-container table-responsive mb-4"><table class="table cc-table table-sm table-hover align-middle"><thead class="table-light"><tr><th>#</th><th>Tipo</th><th>Descricao</th><th>Quantidade</th><th>Valor Unit.</th><th>Desconto</th><th>Total</th></tr></thead><tbody>
{% for item in itens %}<tr><td>{{ loop.index }}</td><td>{{ item.tipo_item }}</td><td>{{ item.descricao }}</td><td>{{ '{:g}'.format(item.quantidade|float) }}</td><td>R$ {{ "{:,.2f}".format(item.valor_unitario or 0).replace(',', 'X').replace('.', ',').replace('X', '.') }}</td><td>R$ {{ "{:,.2f}".format(item.desconto or 0).replace(',', 'X').replace('.', ',').replace('X', '.') }}</td><td>R$ {{ "{:,.2f}".format(item.valor_total or 0).replace(',', 'X').replace('.', ',').replace('X', '.') }}</td></tr>{% endfor %}
</tbody></table></div>

<div class="row g-3 mb-4"><div class="col-md-4"><div class="cc-order-summary p-3"><strong>Subtotal</strong><br>R$ {{ "{:,.2f}".format(pedido.subtotal or 0).replace(',', 'X').replace('.', ',').replace('X', '.') }}</div></div><div class="col-md-4"><div class="cc-order-summary p-3"><strong>Desconto</strong><br>R$ {{ "{:,.2f}".format(pedido.desconto or 0).replace(',', 'X').replace('.', ',').replace('X', '.') }}</div></div><div class="col-md-4"><div class="cc-order-summary is-total p-3"><strong>Total</strong><br>R$ {{ "{:,.2f}".format(pedido.valor_total or 0).replace(',', 'X').replace('.', ',').replace('X', '.') }}</div></div></div>

<div class="card border-0 bg-light mb-4"><div class="card-body"><div class="d-flex justify-content-between align-items-center mb-2"><strong>Pedidos de Compra vinculados</strong><a href="{{ url_for('pedido_compra.novo', pedido_venda_id=pedido.id) }}" class="btn btn-sm btn-outline-primary">+ Nova compra</a></div>
{% if pedidos_compra %}<div class="table-responsive"><table class="table table-sm align-middle mb-0"><thead><tr><th>Numero</th><th>Fornecedor</th><th>Status</th><th>Total</th><th></th></tr></thead><tbody>{% for pc in pedidos_compra %}<tr><td>{{ pc.numero }}</td><td>{{ pc.fornecedor.nome if pc.fornecedor else '-' }}</td><td>{{ pc.status_label }}</td><td>R$ {{ "{:,.2f}".format(pc.total or 0).replace(',', 'X').replace('.', ',').replace('X', '.') }}</td><td class="text-end"><a href="{{ url_for('pedido_compra.visualizar', id=pc.id) }}" class="btn btn-sm btn-outline-secondary">Abrir</a></td></tr>{% endfor %}</tbody></table></div>{% else %}<span class="text-muted">Nenhum pedido de compra vinculado a esta venda.</span>{% endif %}
</div></div>

{% if pedido.condicoes_pagamento %}<div class="mb-3"><strong>Condicoes de Pagamento</strong><p class="mb-0">{{ pedido.condicoes_pagamento }}</p></div>{% endif %}
{% if pedido.observacoes %}<div class="mb-0"><strong>Observacoes</strong><p class="mb-0">{{ pedido.observacoes }}</p></div>{% endif %}
</div></div>
{% endblock %}
''', encoding="utf-8")


# -----------------------------------------------------------------------------
# Pedido de Compra - seed vindo do Pedido de Venda
# -----------------------------------------------------------------------------
pc_routes = PC_ROUTES.read_text(encoding="utf-8")
pc_routes = replace_once(
    pc_routes,
    "def _carregar_form_context(pedido_compra=None):",
    "def _carregar_form_context(pedido_compra=None, pedido_venda_preselecionado=None):",
    "assinatura contexto compra",
)
pc_routes = replace_once(
    pc_routes,
    '        "pedido_compra": pedido_compra,\n',
    '        "pedido_compra": pedido_compra,\n        "pedido_venda_preselecionado": pedido_venda_preselecionado,\n',
    "contexto pedido venda preselecionado",
)
pc_routes = replace_once(
    pc_routes,
    """def novo():
    context = _carregar_form_context()
    if request.method == "POST":""",
    """def novo():
    pedido_venda_id = parse_int(request.args.get("pedido_venda_id"), default=None)
    pedido_venda_preselecionado = None
    itens_seed = []
    if pedido_venda_id:
        pedido_venda_preselecionado = Pedido.query.filter_by(id=pedido_venda_id, ativo=True).first()
        if pedido_venda_preselecionado:
            for item in pedido_venda_preselecionado.itens.filter_by(ativo=True).order_by('ordem').all():
                if not item.produto_id or not item.produto:
                    continue
                itens_seed.append({
                    "tipo_item": PedidoCompraItem.TIPO_PRODUTO,
                    "item_id": None,
                    "referencia_tipo": "P",
                    "referencia_id": item.produto_id,
                    "descricao": item.descricao or item.produto.nome,
                    "unidade": item.produto.unidade_medida or "UN",
                    "quantidade_comprada": Decimal(str(item.quantidade or 0)),
                    "quantidade_recebida": Decimal("0"),
                    "valor_unitario": Decimal(str(item.produto.preco_custo or 0)),
                    "desconto": Decimal("0"),
                })
    context = _carregar_form_context(
        pedido_venda_preselecionado=pedido_venda_preselecionado,
    )
    if request.method == "POST":""",
    "seed pedido venda no pedido compra",
)
pc_routes = replace_once(
    pc_routes,
    '    return render_template("pedido_compra/form.html", itens_preview=[], **context)',
    '    return render_template("pedido_compra/form.html", itens_preview=itens_seed, **context)',
    "render seed compra",
)
PC_ROUTES.write_text(pc_routes, encoding="utf-8")


# -----------------------------------------------------------------------------
# Pedido de Compra - preselecoes na tela
# -----------------------------------------------------------------------------
pc_form = PC_FORM.read_text(encoding="utf-8")
pc_form = pc_form.replace(
    "(not pedido_compra and value == 'ESTOQUE')",
    "(not pedido_compra and pedido_venda_preselecionado and value == 'PEDIDO_VENDA') or (not pedido_compra and not pedido_venda_preselecionado and value == 'ESTOQUE')",
)
pc_form = pc_form.replace(
    "{% if pedido_compra and pedido_compra.pedido_venda_id == pedido_venda.id %}selected{% endif %}",
    "{% if (pedido_compra and pedido_compra.pedido_venda_id == pedido_venda.id) or (not pedido_compra and pedido_venda_preselecionado and pedido_venda_preselecionado.id == pedido_venda.id) %}selected{% endif %}",
)
PC_FORM.write_text(pc_form, encoding="utf-8")

print("OK - Pedido de Venda Executive V1 aplicado.")
