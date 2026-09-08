# -*- coding: utf-8 -*-
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / 'app/app.py').read_text(encoding='utf-8')
CLIENTE = (ROOT / 'app/cliente/cliente_routes.py').read_text(encoding='utf-8')
OS = (ROOT / 'app/ordem_servico/ordem_servico_routes.py').read_text(encoding='utf-8')
FORM_CLIENTE = (ROOT / 'app/cliente/templates/cliente/form_operacional_colaborador.html').read_text(encoding='utf-8')
FORM_OS = (ROOT / 'app/ordem_servico/templates/os/form_operacional_colaborador.html').read_text(encoding='utf-8')
LISTA_CLIENTE = (ROOT / 'app/cliente/templates/cliente/listar_colaborador.html').read_text(encoding='utf-8')
VIEW_CLIENTE = (ROOT / 'app/cliente/templates/cliente/visualizar_colaborador.html').read_text(encoding='utf-8')
LISTA_OS = (ROOT / 'app/ordem_servico/templates/os/listar_colaborador.html').read_text(encoding='utf-8')
VIEW_OS = (ROOT / 'app/ordem_servico/templates/os/visualizar_colaborador.html').read_text(encoding='utf-8')

bloco_whitelist = APP.split('endpoints_permitidos = {', 1)[1].split('}', 1)[0]
for endpoint in (
    "'cliente.novo_operacional'",
    "'ordem_servico.novo_operacional'",
    "'ordem_servico.editar_operacional'",
):
    assert endpoint in bloco_whitelist, f'Endpoint operacional ausente: {endpoint}'

# O guard interno da própria OS precisa permitir as mesmas rotas de campo.
bloco_guard_os = OS.split('def restringir_rotas_colaborador():', 1)[1].split('return None', 1)[0]
for endpoint in (
    "'ordem_servico.novo_operacional'",
    "'ordem_servico.editar_operacional'",
):
    assert endpoint in bloco_guard_os, f'Guard interno da OS bloqueia rota operacional: {endpoint}'

# Cadastro administrativo permanece fora da whitelist.
for endpoint in (
    "'cliente.novo'",
    "'cliente.editar'",
    "'cliente.excluir'",
    "'ordem_servico.novo'",
    "'ordem_servico.editar'",
    "'ordem_servico.excluir'",
):
    assert endpoint not in bloco_whitelist, f'Rota administrativa liberada: {endpoint}'

# Cliente de campo lê apenas dados operacionais e fixa dados financeiros.
assert "@cliente_bp.route('/novo-operacional', methods=['GET', 'POST'])" in CLIENTE
bloco_cliente = CLIENTE.split("@cliente_bp.route('/novo-operacional'", 1)[1].split("@cliente_bp.route('/novo'", 1)[0]
for esperado in (
    'limite_credito=0',
    'forma_pagamento_padrao=None',
    'desconto_padrao=0',
    'observacoes_internas=None',
    "url_for('ordem_servico.novo_operacional', cliente_id=novo_cliente.id)",
):
    assert esperado in bloco_cliente, f'Proteção de cliente ausente: {esperado}'
for proibido in (
    "request.form.get('limite_credito')",
    "request.form.get('desconto_padrao')",
    "request.form.get('forma_pagamento_padrao')",
    "request.form.get('observacoes_internas')",
):
    assert proibido not in bloco_cliente, f'Cliente de campo lê campo sensível: {proibido}'

# OS de campo é sempre operacional, em execução, com valores zerados e autoescala.
assert "@ordem_servico_bp.route('/novo-operacional', methods=['GET', 'POST'])" in OS
assert "@ordem_servico_bp.route('/<int:id>/editar-operacional', methods=['GET', 'POST'])" in OS
bloco_os = OS.split("@ordem_servico_bp.route('/novo-operacional'", 1)[1].split("@ordem_servico_bp.route('/novo'", 1)[0]
for esperado in (
    "tipo_os='operacional'",
    "status='em_execucao'",
    "valor_servico=Decimal('0.00')",
    "valor_pecas=Decimal('0.00')",
    "valor_desconto=Decimal('0.00')",
    "valor_total=Decimal('0.00')",
    'OrdemServicoColaborador(',
    'colaborador_id=colaborador.id',
    "return redirect(url_for('ordem_servico.visualizar', id=ordem.id))",
):
    assert esperado in bloco_os, f'Regra da OS de campo ausente: {esperado}'

# Nada no fluxo próprio pode disparar integração financeira.
for proibido in ('gerar_lancamento_financeiro', 'criar_lancamento', 'LancamentoFinanceiro('):
    assert proibido not in bloco_os, f'Integração financeira indevida no fluxo de campo: {proibido}'

# A edição operacional só aplica campos técnicos e valida propriedade da OS.
bloco_edicao = OS.split("@ordem_servico_bp.route('/<int:id>/editar-operacional'", 1)[1].split("@ordem_servico_bp.route('/novo'", 1)[0]
assert 'ordem_pertence_ao_colaborador' in bloco_edicao
assert "ordem.tipo_os != 'operacional'" in bloco_edicao
assert '_aplicar_campos_tecnicos_colaborador(ordem, request.form)' in bloco_edicao
for sensivel in ('valor_total =', 'valor_servico =', 'valor_pecas =', 'valor_desconto =', 'status_pagamento ='):
    assert sensivel not in bloco_edicao, f'Edição operacional toca campo sensível: {sensivel}'

# Formulários de campo não expõem campos monetários.
for nome, html in (('cliente', FORM_CLIENTE), ('os', FORM_OS)):
    for sensivel in (
        'limite_credito', 'desconto_padrao', 'forma_pagamento_padrao',
        'valor_total', 'valor_servico', 'valor_pecas', 'valor_desconto',
        'numero_parcelas', 'valor_entrada', 'status_pagamento'
    ):
        assert sensivel not in html, f'Formulário {nome} expõe campo sensível: {sensivel}'

# Botões do fluxo de campo estão presentes.
assert "url_for('cliente.novo_operacional')" in LISTA_CLIENTE
assert "url_for('ordem_servico.novo_operacional', cliente_id=cliente.id)" in VIEW_CLIENTE
assert "url_for('ordem_servico.novo_operacional')" in LISTA_OS
assert "url_for('ordem_servico.editar_operacional', id=ordem.id)" in VIEW_OS

print('COLABORADOR CAMPO V2: OK')
