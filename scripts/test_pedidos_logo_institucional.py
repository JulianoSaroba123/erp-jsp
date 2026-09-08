# -*- coding: utf-8 -*-
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ARQUIVOS = [
    ROOT / "app/pedido/templates/pedido/imprimir.html",
    ROOT / "app/pedido_compra/templates/pedido_compra/imprimir.html",
]

for path in ARQUIVOS:
    texto = path.read_text(encoding="utf-8")

    assert "width:24%" in texto or "width: 24%" in texto, f"Celula de logo nao padronizada: {path}"
    assert "max-width:50mm" in texto or "max-width: 50mm" in texto, f"Largura da logo nao padronizada: {path}"
    assert "max-height:23mm" in texto or "max-height: 23mm" in texto, f"Altura da logo nao padronizada: {path}"
    assert "width:auto" in texto or "width: auto" in texto, f"Proporcao horizontal nao preservada: {path}"
    assert "height:auto" in texto or "height: auto" in texto, f"Proporcao vertical nao preservada: {path}"
    assert "max-width:42mm" not in texto and "max-width: 42mm" not in texto, f"Contrato antigo de logo ainda presente: {path}"

print("PEDIDOS LOGO INSTITUCIONAL: OK")
