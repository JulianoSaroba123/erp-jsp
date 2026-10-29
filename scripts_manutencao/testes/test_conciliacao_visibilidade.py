"""Regressão: visibilidade temporária na conciliação de outubro/2026.

Sem conexão externa ou banco de produção. O filtro é só de apresentação;
não deve alterar status/atividade, DRE, saldo ou conciliação N:N.
"""
import importlib.util
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[2]
MODULE = ROOT / "app" / "financeiro" / "conciliacao_visibilidade.py"
ROUTES = ROOT / "app" / "financeiro" / "financeiro_routes.py"
TEMPLATE = ROOT / "app" / "financeiro" / "templates" / "financeiro" / "conciliacao_bancaria" / "conciliacao.html"

spec = importlib.util.spec_from_file_location("visibilidade_conciliacao", MODULE)
visibilidade = importlib.util.module_from_spec(spec)
spec.loader.exec_module(visibilidade)


def _lancamentos(*ids):
    return [SimpleNamespace(id=id) for id in ids]


def test_apenas_quatro_ids_sao_ocultos_na_cora_em_outubro():
    # O mesmo título segue disponível em outros meses ou contas,
    # independentemente da competência/estado do lançamento original.
    reg = visibilidade.sugestoes_ocultas_por_lancamento(
        1, _lancamentos(94, 96, 100, 101, 139, 140, 165, 224)
    )
    assert reg == {94:"2026-10", 96:"2026-10", 100:"2026-10", 101:"2026-10"}
    assert visibilidade.sugestoes_ocultas_por_lancamento(2, _lancamentos(94,96,100,101)) == {}
    assert visibilidade.sugestoes_ocultas_por_lancamento(None, _lancamentos(94,96)) == {}
    assert visibilidade.sugestoes_ocultas_por_lancamento(1, _lancamentos(139,140,165)) == {}


def test_filtro_nao_modifica_os_objetos_recebidos():
    itens = _lancamentos(94,96,100,101)
    estados_antes = [vars(x).copy() for x in itens]
    for _ in range(2):
        assert len(visibilidade.sugestoes_ocultas_por_lancamento(1,itens)) == 4
    assert [vars(x) for x in itens] == estados_antes


def test_template_distingue_competencia_do_extrato_e_permite_mostrar_novamente():
    html = TEMPLATE.read_text(encoding="utf-8")
    assert 'data-extrato-competencia="{{ extrato.data_movimento.strftime(\'%Y-%m\')' in html
    assert 'data-ocultar-competencias="{{ sugestoes_ocultas.get(lanc.id, \'\') }}"' in html
    assert 'id="mostrar-sugestoes-ocultas"' in html
    assert "function aplicarVisibilidadeSugestoes()" in html
    assert "meses.includes(competencia)" in html
    assert "row.style.display = ocultar ? 'none' : ''" in html
    assert "aplicarVisibilidadeSugestoes();\n    atualizarResumoConciliacao();" in html
    assert "!row.hidden" in html  # Sugestões ocultas não recebem ranking.


def test_rota_passa_somente_mapa_de_visibilidade_ao_template():
    texto = ROUTES.read_text(encoding="utf-8")
    segmento = texto.split("def conciliacao_bancaria():",1)[1].split(
        "@bp_financeiro.route('/conciliacao-bancaria/upload'",1
    )[0]
    assert "sugestoes_ocultas_por_lancamento" in segmento
    assert "sugestoes_ocultas=sugestoes_ocultas" in segmento
    assert "lancamentos_pendentes.append(lancamento)" in segmento
    # Não alteramos as regras de elegibilidade ou baixa financeira.
    assert "LancamentoFinanceiro.ativo.is_(True)" in segmento
