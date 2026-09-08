# -*- coding: utf-8 -*-
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "app/app.py").read_text(encoding="utf-8")
AUTH = (ROOT / "app/auth/auth_routes.py").read_text(encoding="utf-8")

# Guard global obrigatório.
assert "@app.before_request" in APP
assert "def restringir_acesso_global_colaborador():" in APP
assert "getattr(current_user, 'tipo_usuario', None) != 'colaborador'" in APP
assert "return redirect(url_for('ordem_servico.listar'))" in APP

# Whitelist mínima e explícita.
for endpoint in (
    "'ordem_servico.listar'",
    "'ordem_servico.visualizar'",
    "'ordem_servico.apontamento_colaborador'",
    "'ordem_servico.novo_operacional'",
    "'ordem_servico.editar_operacional'",
    "'cliente.listar'",
    "'cliente.visualizar'",
    "'cliente.novo_operacional'",
    "'auth.perfil'",
    "'auth.alterar_senha'",
    "'auth.logout'",
    "'auth.login'",
):
    assert endpoint in APP, f"Endpoint permitido ausente: {endpoint}"

bloco = APP.split("endpoints_permitidos = {", 1)[1].split("}", 1)[0]

# Clientes: consulta + cadastro operacional. CRUD administrativo segue proibido.
endpoints_cliente = set(re.findall(r"'(cliente\.[^']+)'", bloco))
assert endpoints_cliente == {
    'cliente.listar',
    'cliente.visualizar',
    'cliente.novo_operacional',
}, f"Whitelist de Clientes fora do contrato operacional: {sorted(endpoints_cliente)}"

# OS: criação/edição somente pelas rotas operacionais próprias.
for proibido in ("'ordem_servico.novo'", "'ordem_servico.editar'", "'ordem_servico.excluir'"):
    assert proibido not in bloco, f"Rota administrativa de OS liberada: {proibido}"

# Demais domínios sensíveis continuam totalmente fora da whitelist.
for proibido in (
    "painel.dashboard",
    "financeiro.",
    "proposta.",
    "pedido.",
    "pedido_compra.",
    "produto.",
    "fornecedor.",
    "colaborador.",
    "usuario.",
    "configuracao.",
):
    assert proibido not in bloco, f"Endpoint sensível liberado na whitelist: {proibido}"

assert "endpoint == 'static'" in APP
assert "endpoint.endswith('.static')" in APP

# Login de colaborador deve ir direto para Minhas OS.
assert "if getattr(current_user, 'tipo_usuario', None) == 'colaborador':" in AUTH
assert "if usuario.tipo_usuario == 'colaborador':" in AUTH
assert "next_page = url_for('ordem_servico.listar')" in AUTH

print("COLABORADOR WHITELIST GLOBAL: OK")
