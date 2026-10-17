# -*- coding: utf-8 -*-
"""G2: botao de inclusao de alternador na ficha de geradores."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FICHA = ROOT / "app/geradores/templates/geradores/ficha.html"
ROTAS = ROOT / "app/geradores/gerador_routes.py"


def _secao_alternador():
    fonte = FICHA.read_text(encoding="utf-8-sig")
    inicio = fonte.index('id="alternador"')
    fim = fonte.index('id="controladora"', inicio)
    return fonte[inicio:fim]


def test_g2_botao_de_cadastro_existe_na_aba_alternador():
    secao = _secao_alternador()
    assert "Alternador ainda não cadastrado" in secao
    assert "Cadastrar Alternador" in secao
    assert (
        "url_for('geradores.novo_alternador', gerador_id=gerador.id)"
        in secao
    )
    assert 'class="btn btn-primary btn-sm mt-3"' in secao


def test_g2_botao_aparece_apenas_quando_alternador_nao_existe():
    secao = _secao_alternador()
    assert secao.count("Cadastrar Alternador") == 1
    bloco_vazio = secao.split("{% else %}", 1)[1]
    assert "Cadastrar Alternador" in bloco_vazio
    assert bloco_vazio.index("Cadastrar Alternador") < bloco_vazio.index(
        "{% endif %}"
    )
    assert "Editar Alternador" in secao.split("{% else %}", 1)[0]


def test_g2_link_reutiliza_rota_get_existente_sem_acao_automatica():
    rotas = ROTAS.read_text(encoding="utf-8-sig")
    assert '"/<int:gerador_id>/alternador/novo"' in rotas
    assert 'def novo_alternador(gerador_id):' in rotas
    assert 'methods=["GET", "POST"]' in rotas
    secao = _secao_alternador()
    assert "<form" not in secao.split("{% else %}", 1)[1]
