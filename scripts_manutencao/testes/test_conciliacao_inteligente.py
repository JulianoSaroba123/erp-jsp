"""Regressões estruturais do ranking conservador na conciliação.

A validação comportamental do motor JavaScript roda separadamente pelo Node,
em ambiente isolado de produção.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HTML = ROOT / "app" / "financeiro" / "templates" / "financeiro" / "conciliacao_bancaria" / "conciliacao.html"
JS = ROOT / "app" / "static" / "js" / "conciliacao_match.js"
ROUTES = ROOT / "app" / "financeiro" / "financeiro_routes.py"


def test_dados_necessarios_estao_no_dom_sem_consulta_extra():
    html = HTML.read_text(encoding="utf-8")
    for atributo in [
        'data-extrato-data="{{ extrato.data_movimento.isoformat()',
        'data-data-pagamento="{{ lanc.data_pagamento.isoformat()',
        'data-lancamento-status="{{ lanc.status }}"',
        'data-lancamento-descricao="{{ (lanc.descricao or \'\')|e }}"',
        'data-fornecedor-nome="{{ ((lanc.fornecedor.nome or \'\')',
        'data-fornecedor-documento="{{ ((lanc.fornecedor.cnpj_cpf or \'\')',
        'data-cliente-nome="{{ ((lanc.cliente.nome or \'\')',
        'id="aviso-correspondencias"',
    ]:
        assert atributo in html, atributo


def test_filtro_reversivel_preserva_conciliacao_nn():
    html = HTML.read_text(encoding="utf-8")
    assert "js/conciliacao_match.js" in html
    assert "window.JSPConciliacaoMatch.avaliar" in html
    assert "mostrar-sugestoes-ocultas" in html
    assert "configurado || Boolean(avaliacao && avaliacao.ocultarPadrao)" in html
    assert "row.hidden = ocultar;" in html
    assert "row.style.display = ocultar ? 'none' : '';" in html
    assert "function obterLancamentosSelecionados()" in html
    assert "function conciliarSelecionados()" in html
    assert "alocacoes: alocacoes" in html
    assert "dados.saldo_final_extrato" in html


def test_ranking_nao_aponta_primeiro_da_lista_sem_indicios():
    html = HTML.read_text(encoding="utf-8")
    assert "function scoreLancamentoMatch(row)" in html
    assert "avaliacao && avaliacao.badge" in html
    assert "row.hidden" in html
    assert "Melhor candidato" not in html
    assert "scoreLancamentoMatch(b) - scoreLancamentoMatch(a)" in html


def test_politica_sem_update_em_banco():
    js = JS.read_text(encoding="utf-8")
    assert "ocultarPadrao" in js
    assert "pagamento_antigo" in js
    assert "sem_indicios" in js
    assert "natureza_incompativel" in js
    assert "pontuacao" in js
    assert "fetch(" not in js
    assert "XMLHttpRequest" not in js
    codigo = ROUTES.read_text(encoding="utf-8").split(
        "def conciliacao_bancaria():", 1
    )[1].split("@bp_financeiro.route('/conciliacao-bancaria/upload'", 1)[0]
    assert "sugestoes_ocultas_por_lancamento" in codigo
    assert "sugestoes_ocultas=sugestoes_ocultas" in codigo
