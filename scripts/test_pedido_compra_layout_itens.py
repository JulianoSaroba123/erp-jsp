# -*- coding: utf-8 -*-
from pathlib import Path

TEMPLATE = Path("app/pedido_compra/templates/pedido_compra/form.html")


def main():
    texto = TEMPLATE.read_text(encoding="utf-8")

    obrigatorios = [
        "pedido-compra-itens-table",
        "pedido-compra-itens-wrap",
        "overflow-x: auto",
        "table-layout: fixed",
        "pc-col-referencia",
        "pc-col-descricao",
        "pc-col-total",
        "pc-col-acoes",
        'name="item_referencia_id[]"',
        'name="item_descricao[]"',
        'name="item_quantidade[]"',
        'name="item_valor_unitario[]"',
        'name="item_desconto[]"',
        'aria-label="Remover item"',
    ]

    for trecho in obrigatorios:
        assert trecho in texto, f"Contrato visual ausente: {trecho}"

    assert texto.count('<col class="pc-col-') == 9, "Esperadas 9 colunas dimensionadas na Executive V1"
    assert "Remover</button>" not in texto, "Botao textual antigo ainda presente"
    assert "min-width: 1260px" in texto, "Tabela principal deve manter largura confortavel na Executive V1"

    print("PEDIDO COMPRA LAYOUT ITENS: OK")


if __name__ == "__main__":
    main()
