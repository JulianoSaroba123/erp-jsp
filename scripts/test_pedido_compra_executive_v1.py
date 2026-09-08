# -*- coding: utf-8 -*-
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FORM = ROOT / "app/pedido_compra/templates/pedido_compra/form.html"
PRINT = ROOT / "app/pedido_compra/templates/pedido_compra/imprimir.html"

form = FORM.read_text(encoding="utf-8")
print_html = PRINT.read_text(encoding="utf-8")

# Formulario: preenchimento automatico e metadados do cadastro.
for marker in (
    'data-descricao="{{ produto.nome|e }}"',
    'data-unidade="{{ (produto.unidade_medida or \'UN\')|e }}"',
    'data-valor="{{ produto.preco_custo',
    'class="item-total-display"',
    'id="resumo-subtotal"',
    'id="resumo-desconto"',
    'id="resumo-total"',
    'function aplicarReferencia(row)',
    'function recalcularResumo()',
    'function atualizarVinculos()',
):
    assert marker in form, f"Formulario sem contrato esperado: {marker}"

# A finalidade deve tornar o vinculo correspondente obrigatorio apenas na interface.
assert "valor === 'ORDEM_SERVICO'" in form
assert "valor === 'PEDIDO_VENDA'" in form
assert "osSelect.required = true" in form
assert "pvSelect.required = true" in form

# Impressao: identidade, fornecedor, itens e totais.
for marker in (
    "JSP ELÉTRICA INDUSTRIAL &amp; SOLAR",
    "Pedido de Compra",
    "01</span>Fornecedor",
    "02</span>Dados da Compra",
    "03</span>Itens do Pedido",
    "Total do pedido",
    "Imprimir / Salvar PDF",
    "Favor mencionar o número",
):
    assert marker in print_html, f"Impressao sem contrato esperado: {marker}"

# A impressao comercial nao deve expor controle interno de recebimento.
assert "Qtd recebida" not in print_html
assert "Qtd. recebida" not in print_html
assert "quantidade_recebida" not in print_html

print("PEDIDO COMPRA EXECUTIVE V1: OK")
