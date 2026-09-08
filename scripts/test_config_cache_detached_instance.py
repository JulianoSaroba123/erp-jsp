# -*- coding: utf-8 -*-
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
UTILS = ROOT / 'app/configuracao/configuracao_utils.py'
BASE = ROOT / 'app/templates/base.html'
APP = ROOT / 'app/app.py'

utils = UTILS.read_text(encoding='utf-8')
base = BASE.read_text(encoding='utf-8')
app = APP.read_text(encoding='utf-8')

# A causa raiz não pode voltar: jamais cachear diretamente o model ORM.
assert '_cached = Configuracao.get_solo()' not in utils
assert '_cached = _snapshot_config(Configuracao.get_solo())' in utils

# Snapshot deve aceitar acesso por atributo e .get(), compatível com os usos atuais.
assert 'class ConfigSnapshot(dict):' in utils
assert 'def __getattr__(self, key):' in utils
assert 'def __setattr__(self, key, value):' in utils
assert 'for coluna in Configuracao.__table__.columns' in utils

# Base e context processor continuam consumindo config do mesmo jeito.
assert 'config.logo_base64' in base
assert "return {'config': cfg}" in app

# A API pública de cache permanece preservada.
for esperado in ('def get_config(force_reload=False):', 'def invalidate_cache():'):
    assert esperado in utils

print('CONFIG CACHE DETACHED INSTANCE: OK')
