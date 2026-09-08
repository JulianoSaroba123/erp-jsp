# -*- coding: utf-8 -*-
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ARQUIVOS = [
    ROOT / "app/pedido/templates/pedido/imprimir.html",
    ROOT / "app/pedido_compra/templates/pedido_compra/imprimir.html",
]

SUBSTITUICOES = (
    (".logo-cell{width:22%;vertical-align:middle}", ".logo-cell{width:24%;vertical-align:middle}"),
    (".logo-cell img{max-width:42mm;max-height:19mm;object-fit:contain;display:block}", ".logo-cell img{max-width:50mm;max-height:23mm;width:auto;height:auto;object-fit:contain;display:block}"),
    (".logo-cell { width: 22%; vertical-align: middle; }", ".logo-cell { width: 24%; vertical-align: middle; }"),
    (".logo-cell img { max-width: 42mm; max-height: 19mm; object-fit: contain; display: block; }", ".logo-cell img { max-width: 50mm; max-height: 23mm; width: auto; height: auto; object-fit: contain; display: block; }"),
)

for path in ARQUIVOS:
    texto = path.read_text(encoding="utf-8")
    original = texto
    alteracoes = 0

    for antigo, novo in SUBSTITUICOES:
        if antigo in texto:
            texto = texto.replace(antigo, novo, 1)
            alteracoes += 1

    if alteracoes != 2:
        raise SystemExit(
            f"ABORTADO: esperado ajustar 2 contratos de logo em {path}, ajustados {alteracoes}."
        )

    if texto == original:
        raise SystemExit(f"ABORTADO: nenhuma alteracao aplicada em {path}.")

    path.write_text(texto, encoding="utf-8")

print("OK - Logos de Pedido de Venda e Pedido de Compra padronizadas em tamanho institucional.")
