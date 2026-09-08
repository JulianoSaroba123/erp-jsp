# -*- coding: utf-8 -*-
from pathlib import Path

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
    "'auth.perfil'",
    "'auth.alterar_senha'",
    "'auth.logout'",
    "'auth.login'",
):
    assert endpoint in APP, f"Endpoint permitido ausente: {endpoint}"

# Nada sensível pode aparecer na whitelist.
bloco = APP.split("endpoints_permitidos = {", 1)[1].split("}", 1)[0]
for proibido in (
    "painel.dashboard",
    "financeiro.",
    "cliente.",
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

# Assets estáticos continuam funcionando.
assert "endpoint == 'static'" in APP
assert "endpoint.endswith('.static')" in APP

# Login de colaborador deve ir direto para Minhas OS.
assert "if getattr(current_user, 'tipo_usuario', None) == 'colaborador':" in AUTH
assert "if usuario.tipo_usuario == 'colaborador':" in AUTH
assert "next_page = url_for('ordem_servico.listar')" in AUTH

print("COLABORADOR WHITELIST GLOBAL: OK")
