# -*- coding: utf-8 -*-
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'app/templates/base.html'
TOKENS = ROOT / 'app/static/css/command-center.css'
COMP = ROOT / 'app/static/css/jsp-executive-suite-components.css'
APP = ROOT / 'app/app.py'


def replace_once(path, old, new, label):
    text = path.read_text(encoding='utf-8')
    if new in text:
        return False
    count = text.count(old)
    if count != 1:
        raise SystemExit(f'ABORTADO: {label} não localizado de forma única em {path} ({count}).')
    path.write_text(text.replace(old, new, 1), encoding='utf-8')
    return True


replace_once(
    BASE,
    '<html lang="pt-BR" data-bs-theme="dark">',
    '<html lang="pt-BR" data-bs-theme="light">',
    'tema Bootstrap global',
)

replace_once(
    TOKENS,
    '  --cc-text-muted: #758491;',
    '  --cc-text-muted: #667584;',
    'token de texto secundário',
)

replace_once(
    TOKENS,
    '.cc-input::placeholder {\n  color: #A7B2BC;\n}',
    '.cc-input::placeholder {\n  color: #687684;\n  opacity: 1;\n}',
    'placeholder Command Center',
)

GLOBAL_BLOCK = r'''

/* ============================================================
   Contraste global — ERP JSP Executive Suite
   Mantém o tema claro consistente e evita textos "fantasma"
   herdados do Bootstrap dark ou de estilos legados.
   ============================================================ */
html body .text-muted,
html body .text-secondary,
html body .form-text,
html body small.text-muted,
html body .small.text-muted {
    color: var(--cc-text-muted) !important;
    opacity: 1 !important;
}

html body label,
html body .form-label,
html body .cc-label,
html body .info-label,
html body table.table thead th,
html body table.cc-table thead th {
    color: var(--cc-text-muted) !important;
    opacity: 1 !important;
}

html body .form-control::placeholder,
html body textarea.form-control::placeholder,
html body input[class*="form-control"]::placeholder,
html body .cc-input::placeholder {
    color: #687684 !important;
    opacity: 1 !important;
}

html body .breadcrumb-item.active,
html body .current-page,
html body .cc-page-header-subtitle,
html body .cc-mini-stat-label {
    opacity: 1 !important;
}
'''

comp_text = COMP.read_text(encoding='utf-8')
if 'Contraste global — ERP JSP Executive Suite' not in comp_text:
    COMP.write_text(comp_text.rstrip() + GLOBAL_BLOCK + '\n', encoding='utf-8')

app_text = APP.read_text(encoding='utf-8')
old_asset = "'ASSET_VERSION': '20260605.3'"
new_asset = "'ASSET_VERSION': '20260908.1'"
if new_asset not in app_text:
    if old_asset not in app_text:
        raise SystemExit('ABORTADO: ASSET_VERSION esperado não localizado em app/app.py.')
    APP.write_text(app_text.replace(old_asset, new_asset, 1), encoding='utf-8')

print('OK - Contraste global Executive Suite aplicado.')
