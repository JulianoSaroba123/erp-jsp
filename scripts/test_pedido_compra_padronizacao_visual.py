# -*- coding: utf-8 -*-
from pathlib import Path

FORM = Path("app/pedido_compra/templates/pedido_compra/form.html")
PRINT = Path("app/pedido_compra/templates/pedido_compra/imprimir.html")


def main():
    form = FORM.read_text(encoding="utf-8")
    imp = PRINT.read_text(encoding="utf-8")

    obrigatorios_form = [
        ".pc-col-tipo { width: 9%; }",
        ".pc-col-referencia { width: 20%; }",
        ".pc-col-descricao { width: 20%; }",
        "min-width: 1280px",
        "pedido_compra.visualizar",
        ">Voltar</a>",
        ">Produto</option>",
        ">Servico</option>",
    ]
    for trecho in obrigatorios_form:
        assert trecho in form, f"Contrato do formulario ausente: {trecho}"

    obrigatorios_print = [
        "config.logo_base64",
        "config.nome_fantasia",
        "config.cnpj",
        "config.cidade",
        "config.uf",
        "toolbar-btn back-btn",
        "pedido_compra.visualizar",
        "Imprimir / Salvar PDF",
        "--navy: #163A5C",
        "--orange: #E8872F",
    ]
    for trecho in obrigatorios_print:
        assert trecho in imp, f"Contrato da impressao ausente: {trecho}"

    assert "Qtd recebida" not in imp and "Qtd. recebida" not in imp, "Controle interno voltou para documento comercial"
    print("PEDIDO COMPRA PADRONIZACAO VISUAL: OK")


if __name__ == "__main__":
    main()
