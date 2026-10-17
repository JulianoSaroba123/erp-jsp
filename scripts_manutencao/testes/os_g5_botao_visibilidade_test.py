# -*- coding: utf-8 -*-
"""Regressão visual estática: botão G5 não pode desaparecer no cabeçalho claro."""
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[2]
TEMPLATE = ROOT / "app/ordem_servico/templates/os/visualizar.html"
CSS = ROOT / "app/static/css/jsp-executive-suite-phase-f.css"


def _botao_g5():
    texto = TEMPLATE.read_text(encoding="utf-8")
    padrao = re.compile(
        r'<a\s+href="\{\{\s*url_for\(\s*'
        r"['\"]gerador_os_vinculo\.geradores_da_os['\"]"
        r'.*?\)\s*\}\}"\s+class="([^"]+)"[^>]*>'
        r'\s*<i\s+[^>]*></i>Geradores atendidos \(G5\)\s*</a>',
        re.DOTALL,
    )
    encontrados = padrao.findall(texto)
    assert len(encontrados) == 1, "O link G5 deve existir uma única vez."
    return set(encontrados[0].split()), texto


def test_botao_g5_tem_contraste_no_cabecalho_claro():
    classes, _ = _botao_g5()
    assert {"btn", "btn-light", "action-btn"}.issubset(classes)
    assert "btn-outline-light" not in classes
    css = CSS.read_text(encoding="utf-8")
    # A suíte executiva aplica texto escuro aos botões btn-light nesse bloco.
    assert "html body .os-header .btn-light" in css
    assert "color: var(--cc-navy) !important" in css


def test_link_g5_mantem_acesso_restrito_a_admin():
    _, texto = _botao_g5()
    bloco = texto.split("Geradores atendidos (G5)", 1)[0]
    assert "{% if current_user.is_authenticated and current_user.tipo_usuario == 'admin' %}" in bloco[-500:]


def test_link_g5_e_navegacao_sem_post():
    _, texto = _botao_g5()
    assert "url_for('gerador_os_vinculo.geradores_da_os', os_id=ordem.id)" in texto
    assert "Geradores atendidos (G5)" in texto
