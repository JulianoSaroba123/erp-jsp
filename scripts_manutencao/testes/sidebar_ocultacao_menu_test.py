from pathlib import Path


def test_sidebar_nao_exibe_prospeccao_e_precificacao():
    template_path = Path(__file__).resolve().parents[2] / "app" / "templates" / "base.html"
    source = template_path.read_text(encoding="utf-8")

    assert "url_for('prospeccao.dashboard')" not in source
    assert "url_for('precificacao.calculadora')" not in source
    assert "<span class=\"nav-text\">Prospecção</span>" not in source
    assert "<span class=\"nav-text\">Precificação</span>" not in source
