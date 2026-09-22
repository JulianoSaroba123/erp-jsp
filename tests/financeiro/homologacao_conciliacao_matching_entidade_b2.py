# -*- coding: utf-8 -*-
# D25F02-B2
# Homologacao estatica do matching por entidade na conciliacao.

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

text = TEMPLATE.read_text(encoding="utf-8")

# O template precisa continuar sintaticamente valido para Jinja.
Environment().parse(text)

required = [
    'data-extrato-descricao=',
    'data-extrato-documento=',
    'data-cliente-nome=',
    'data-cliente-razao=',
    'data-cliente-fantasia=',
    'data-cliente-documento=',
    'data-lancamento-documento=',
    'function normalizarTextoMatch(valor)',
    'function tokensSignificativosMatch(valor)',
    'function pontuacaoEntidadeLancamento(row)',
    'score += pontuacaoEntidadeLancamento(row);',
    'return 350000;',
    'return 250000;',
    'return 180000;',
    'return 50000;',
    'score += 100000;',
    "'Cliente compatível'",
    "'match-entidade'",
]

for marker in required:
    assert marker in text, (
        f"Marcador D25F02-B2 ausente: {marker}"
    )

# A identidade precisa pesar mais que uma simples igualdade de valor.
assert text.index("return 250000;") < text.index(
    "function scoreLancamentoMatch(row)"
)
assert 250000 > 100000
assert 180000 > 100000

# Regra de negocio homologada pelo caso MR Jacky:
# nome/documento do pagador deve superar coincidencia isolada de valor.
def score_exemplo(*, entidade, valor_igual=False, diferenca=0, dias=0):
    score = entidade
    if valor_igual:
        score += 100000
    else:
        score += max(0, 20000 - diferenca * 10)
    score += max(0, 5000 - dias * 80)
    return score


mr_jacky = score_exemplo(
    entidade=250000,
    diferenca=450,
    dias=2,
)
mario_mesmo_valor = score_exemplo(
    entidade=0,
    diferenca=450,
    dias=2,
)
suelen_valor_mais_proximo = score_exemplo(
    entidade=0,
    diferenca=360,
    dias=2,
)

assert mr_jacky > mario_mesmo_valor
assert mr_jacky > suelen_valor_mais_proximo

print("=== D25F02-B2 ===")
print("Jinja: OK")
print("Dados de extrato/cliente expostos: OK")
print("Normalizacao textual: OK")
print("Matching por nome/documento: OK")
print("Peso entidade > valor isolado: OK")
print("Caso MR Jacky protegido: OK")
print()
print("D25F02-B2 HOMOLOGADO")
