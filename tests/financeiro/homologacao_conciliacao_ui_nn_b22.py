# -*- coding: utf-8 -*-
# D25F01-B2.2
# Homologacao estatica da ligacao UI -> rota N:N.

from pathlib import Path
from jinja2 import Environment

ROOT = Path(__file__).resolve().parents[2]

TEMPLATE = (
    ROOT
    / "app"
    / "financeiro"
    / "templates"
    / "financeiro"
    / "conciliacao_bancaria"
    / "conciliacao.html"
)

ROUTES = (
    ROOT
    / "app"
    / "financeiro"
    / "financeiro_routes.py"
)

text = TEMPLATE.read_text(encoding="utf-8")
routes = ROUTES.read_text(encoding="utf-8")

Environment().parse(text)

required = [
    "async function conciliarSelecionados()",
    'id="btn-conciliar-nn"',
    'onclick="conciliarSelecionados()"',
    "/financeiro/conciliacao-bancaria/conciliar-nn",
    "'X-CSRFToken':",
    "csrf_token()",
    "credentials: 'same-origin'",
    "'Content-Type': 'application/json'",
    "JSON.stringify({",
    "extrato_id:",
    "alocacoes:",
    "confirm(resumo)",
    "conciliacaoEmAndamento",
    "window.location.reload()",
    "dados.ok !== true",
    "dados.erro",
]

for marker in required:
    assert marker in text, (
        f"Marcador B2.2 ausente: {marker}"
    )

forbidden = [
    "function previsualizarConciliacao()",
    "btn-previsualizar-conciliacao",
    "B1 - pré-visualização",
    "Nenhuma gravação foi realizada.",
]

for marker in forbidden:
    assert marker not in text, (
        f"Legado B1 permaneceu: {marker}"
    )

assert "def conciliar_nn():" in routes
assert "'/conciliacao-bancaria/conciliar-nn'" in routes
assert "def conciliar_manual(" in routes

print("=== D25F01-B2.2 ===")
print("Jinja: OK")
print("Botao UI -> conciliarSelecionados(): OK")
print("Payload N:N: OK")
print("CSRF: OK")
print("Bloqueio de clique duplo: OK")
print("Tratamento HTTP/JSON: OK")
print("Rota N:N existente: OK")
print("Rota legada 1:1 preservada: OK")
print()
print("D25F01-B2.2 HOMOLOGADO")
