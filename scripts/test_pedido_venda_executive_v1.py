# -*- coding: utf-8 -*-
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FORM = ROOT / "app/pedido/templates/pedido/form.html"
VIEW = ROOT / "app/pedido/templates/pedido/visualizar.html"
PRINT = ROOT / "app/pedido/templates/pedido/imprimir.html"
ROUTES = ROOT / "app/pedido/pedido_routes.py"
PC_ROUTES = ROOT / "app/pedido_compra/pedido_compra_routes.py"
PC_FORM = ROOT / "app/pedido_compra/templates/pedido_compra/form.html"

form = FORM.read_text(encoding="utf-8")
view = VIEW.read_text(encoding="utf-8")
print_html = PRINT.read_text(encoding="utf-8")
routes = ROUTES.read_text(encoding="utf-8")
pc_routes = PC_ROUTES.read_text(encoding="utf-8")
pc_form = PC_FORM.read_text(encoding="utf-8")

# Parser deve aceitar tanto decimal do banco (420.00) quanto pt-BR (420,00).
assert "const temVirgula = texto.includes(',')" in form
assert "const temPonto = texto.includes('.')" in form
assert "texto.lastIndexOf(',') > texto.lastIndexOf('.')" in form
assert ".replace(/\\./g, '').replace(',', '.')" not in form.split("function parseDecimalBr", 1)[1].split("function formatMoney", 1)[0]

# Produto/servico deve oferecer preco automatico para a tela.
assert "data-valor=\"{{ produto.preco_venda or 0 }}\"" in form
assert "data-valor=\"{{ servico.valor_base or 0 }}\"" in form
assert "option.dataset.valor" in form
assert "pedido.visualizar" in form and ">Voltar</a>" in form

# Visualizacao Executive e workflow.
for marker in (
    "Fluxo da Venda",
    "Venda confirmada",
    "Compra / Separacao",
    "Material disponivel",
    "Entrega / Conclusao",
    "Pedidos de Compra vinculados",
    "Gerar Pedido de Compra",
    "pedido_compra.novo",
    "Origem:",
    "Venda direta",
    "pedido.imprimir",
):
    assert marker in view, f"Visualizacao sem contrato: {marker}"

# Rota da venda deve carregar compras vinculadas e impressao.
assert "PedidoCompra.pedido_venda_id == pedido.id" in routes
assert '@pedido_bp.route("/<int:id>/imprimir")' in routes
assert 'render_template("pedido/imprimir.html"' in routes

# Pedido de Compra deve aceitar seed do Pedido de Venda.
for marker in (
    'request.args.get("pedido_venda_id")',
    "pedido_venda_preselecionado",
    '"referencia_tipo": "P"',
    'item.produto.preco_custo',
    'itens_preview=itens_seed',
):
    assert marker in pc_routes, f"Compra sem seed da venda: {marker}"
assert "pedido_venda_preselecionado" in pc_form
assert "value == 'PEDIDO_VENDA'" in pc_form

# Impressao deve seguir identidade institucional usada no Pedido de Compra.
for marker in (
    "config.logo_base64",
    "config.nome_fantasia",
    "--navy:#163A5C",
    "--orange:#E8872F",
    "Pedido de Venda",
    "Imprimir / Salvar PDF",
    "Venda direta",
    "Total do pedido",
):
    assert marker in print_html, f"Impressao sem contrato: {marker}"

print("PEDIDO VENDA EXECUTIVE V1: OK")
