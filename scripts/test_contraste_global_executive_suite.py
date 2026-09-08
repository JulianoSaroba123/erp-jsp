# -*- coding: utf-8 -*-
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = (ROOT / 'app/templates/base.html').read_text(encoding='utf-8')
TOKENS = (ROOT / 'app/static/css/command-center.css').read_text(encoding='utf-8')
COMP = (ROOT / 'app/static/css/jsp-executive-suite-components.css').read_text(encoding='utf-8')
APP = (ROOT / 'app/app.py').read_text(encoding='utf-8')

assert 'data-bs-theme="light"' in BASE, 'Bootstrap global ainda não está em tema claro.'
assert 'data-bs-theme="dark"' not in BASE, 'Tema dark legado continua ativo no base.html.'

assert '--cc-text-muted: #667584;' in TOKENS, 'Token global de texto secundário não foi reforçado.'
assert '.cc-input::placeholder' in TOKENS and 'color: #687684;' in TOKENS, 'Placeholder do Command Center não foi reforçado.'

for esperado in (
    'Contraste global — ERP JSP Executive Suite',
    'html body .text-muted',
    'html body .text-secondary',
    'html body .form-text',
    'html body .form-control::placeholder',
    'html body label',
    'html body .form-label',
    'color: #687684 !important;',
    'opacity: 1 !important;',
):
    assert esperado in COMP, f'Regra global de contraste ausente: {esperado}'

assert "'ASSET_VERSION': '20260908.1'" in APP, 'Cache bust dos assets não foi atualizado.'

print('CONTRASTE GLOBAL EXECUTIVE SUITE: OK')
