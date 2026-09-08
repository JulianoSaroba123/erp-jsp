# -*- coding: utf-8 -*-
from pathlib import Path

FORM = Path("app/pedido_compra/templates/pedido_compra/form.html")
PRINT = Path("app/pedido_compra/templates/pedido_compra/imprimir.html")


def replace_once(texto, antigo, novo, nome):
    qtd = texto.count(antigo)
    if qtd != 1:
        raise SystemExit(f"ABORTADO: esperado 1 marcador para {nome}, encontrado {qtd}.")
    return texto.replace(antigo, novo, 1)


form = FORM.read_text(encoding="utf-8")
form = replace_once(
    form,
    ".pedido-compra-itens-table { width: 100%; min-width: 1260px; table-layout: fixed; margin-bottom: 0; }",
    ".pedido-compra-itens-table { width: 100%; min-width: 1280px; table-layout: fixed; margin-bottom: 0; }",
    "largura minima da tabela",
)
form = replace_once(
    form,
    "    .pedido-compra-itens-table .pc-col-tipo { width: 7%; }\n    .pedido-compra-itens-table .pc-col-referencia { width: 21%; }\n    .pedido-compra-itens-table .pc-col-descricao { width: 21%; }",
    "    .pedido-compra-itens-table .pc-col-tipo { width: 9%; }\n    .pedido-compra-itens-table .pc-col-referencia { width: 20%; }\n    .pedido-compra-itens-table .pc-col-descricao { width: 20%; }",
    "larguras Tipo/Referencia/Descricao",
)
form = replace_once(
    form,
    "    <div class=\"col-12 d-flex gap-2\">\n        <button class=\"btn btn-primary\" type=\"submit\">Salvar</button>\n        <a class=\"btn btn-outline-secondary\" href=\"{{ url_for('pedido_compra.listar') }}\">Cancelar</a>\n    </div>",
    "    <div class=\"col-12 d-flex gap-2\">\n        <button class=\"btn btn-primary\" type=\"submit\">Salvar</button>\n        {% if pedido_compra %}\n        <a class=\"btn btn-outline-secondary\" href=\"{{ url_for('pedido_compra.visualizar', id=pedido_compra.id) }}\"><i class=\"fas fa-arrow-left me-1\" aria-hidden=\"true\"></i>Voltar</a>\n        {% else %}\n        <a class=\"btn btn-outline-secondary\" href=\"{{ url_for('pedido_compra.listar') }}\"><i class=\"fas fa-arrow-left me-1\" aria-hidden=\"true\"></i>Voltar</a>\n        {% endif %}\n    </div>",
    "botao Voltar no formulario",
)
FORM.write_text(form, encoding="utf-8")

imp = PRINT.read_text(encoding="utf-8")
imp = replace_once(
    imp,
    "        .no-print { max-width: 210mm; margin: 12px auto; text-align: right; }\n        .print-btn {\n            border: 0; border-radius: 5px; background: var(--navy); color: #fff;\n            cursor: pointer; font-weight: 700; padding: 9px 16px;\n        }",
    "        .no-print { max-width: 210mm; margin: 12px auto; display: flex; justify-content: flex-end; gap: 8px; }\n        .toolbar-btn {\n            border: 1px solid var(--navy); border-radius: 5px; cursor: pointer;\n            font-weight: 700; padding: 9px 16px; text-decoration: none; display: inline-flex;\n            align-items: center; justify-content: center; font-family: Arial, Helvetica, sans-serif; font-size: 9pt;\n        }\n        .back-btn { background: #fff; color: var(--navy); }\n        .print-btn { background: var(--navy); color: #fff; }",
    "barra de acoes da impressao",
)
imp = replace_once(
    imp,
    '<div class="no-print"><button class="print-btn" type="button" onclick="window.print()">Imprimir / Salvar PDF</button></div>',
    '<div class="no-print"><a class="toolbar-btn back-btn" href="{{ url_for(\'pedido_compra.visualizar\', id=pedido_compra.id) }}">← Voltar</a><button class="toolbar-btn print-btn" type="button" onclick="window.print()">Imprimir / Salvar PDF</button></div>',
    "botao Voltar na impressao",
)
imp = replace_once(
    imp,
    '<td class="logo-cell"><img src="{{ url_for(\'static\', filename=\'img/JSP.jpg\') }}" alt="JSP"></td>',
    '<td class="logo-cell">{% if config and config.logo_base64 %}<img src="{{ config.logo_base64 }}" alt="Logo JSP">{% else %}<img src="{{ url_for(\'static\', filename=\'img/JSP.jpg\') }}" alt="Logo JSP">{% endif %}</td>',
    "logo institucional",
)
imp = replace_once(
    imp,
    '                    <div class="company-name">JSP ELÉTRICA INDUSTRIAL &amp; SOLAR</div>\n                    <div class="company-meta">CNPJ 41.280.764/0001-65 &nbsp;|&nbsp; Tietê/SP</div>',
    '                    <div class="company-name">{{ config.nome_fantasia if config and config.nome_fantasia else \'JSP ELÉTRICA INDUSTRIAL & SOLAR\' }}</div>\n                    <div class="company-meta">CNPJ {{ config.cnpj if config and config.cnpj else \'41.280.764/0001-65\' }} &nbsp;|&nbsp; {{ config.cidade if config and config.cidade else \'Tietê\' }}/{{ config.uf if config and config.uf else \'SP\' }}</div>',
    "identidade institucional do cabecalho",
)
PRINT.write_text(imp, encoding="utf-8")

print("OK - Pedido de Compra padronizado com a identidade visual institucional.")
