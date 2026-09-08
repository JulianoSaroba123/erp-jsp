# -*- coding: utf-8 -*-
from pathlib import Path
import runpy

ROOT = Path(__file__).resolve().parents[1]
BASE_PATCH = ROOT / 'scripts_manutencao/aplicar_colaborador_campo_v2.py'
OS = ROOT / 'app/ordem_servico/ordem_servico_routes.py'

# Aplica o pacote principal primeiro.
runpy.run_path(str(BASE_PATCH), run_name='__main__')

texto = OS.read_text(encoding='utf-8')
antigo = """    permitidas = {\n        'ordem_servico.listar',\n        'ordem_servico.visualizar',\n        'ordem_servico.apontamento_colaborador',\n    }\n"""
novo = """    permitidas = {\n        'ordem_servico.listar',\n        'ordem_servico.visualizar',\n        'ordem_servico.apontamento_colaborador',\n        'ordem_servico.novo_operacional',\n        'ordem_servico.editar_operacional',\n    }\n"""

guard = texto.split('def restringir_rotas_colaborador():', 1)[1].split('if request.endpoint not in permitidas:', 1)[0]
if "'ordem_servico.novo_operacional'" not in guard:
    qtd = texto.count(antigo)
    if qtd != 1:
        raise SystemExit(f'ABORTADO: guard interno da OS não localizado de forma única ({qtd}).')
    texto = texto.replace(antigo, novo, 1)
    OS.write_text(texto, encoding='utf-8')

print('OK - Colaborador Campo V2 FINAL aplicado, incluindo guard interno da OS.')
