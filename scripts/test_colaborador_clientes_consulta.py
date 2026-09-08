# -*- coding: utf-8 -*-
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "app/app.py"
BASE = ROOT / "app/templates/base.html"
ROTAS = ROOT / "app/cliente/cliente_routes.py"
LISTA = ROOT / "app/cliente/templates/cliente/listar_colaborador.html"
VIEW = ROOT / "app/cliente/templates/cliente/visualizar_colaborador.html"

app = APP.read_text(encoding="utf-8")
base = BASE.read_text(encoding="utf-8")
rotas = ROTAS.read_text(encoding="utf-8")
lista = LISTA.read_text(encoding="utf-8")
view = VIEW.read_text(encoding="utf-8")
bloco_whitelist = app.split("endpoints_permitidos = {", 1)[1].split("}", 1)[0]

# Whitelist: consulta + cadastro operacional, sem CRUD administrativo.
for permitido in ("'cliente.listar'", "'cliente.visualizar'", "'cliente.novo_operacional'"):
    assert permitido in bloco_whitelist
for proibido in ("'cliente.novo'", "'cliente.editar'", "'cliente.excluir'"):
    assert proibido not in bloco_whitelist

# Menu operacional inclui Clientes.
bloco_menu = base.split("MINHA OPERAÇÃO", 1)[1].split("{% endif %}", 1)[0]
assert "url_for('cliente.listar')" in bloco_menu
assert ">Clientes<" in bloco_menu

# Rotas entregam templates próprios ao colaborador.
assert "from flask_login import current_user" in rotas
assert "getattr(current_user, 'tipo_usuario', None) == 'colaborador'" in rotas
assert "cliente/listar_colaborador.html" in rotas
assert "cliente/visualizar_colaborador.html" in rotas

# Lista/view nunca oferecem CRUD administrativo ou dados comerciais/financeiros.
for nome, html in (("lista", lista), ("visualizacao", view)):
    for proibido in (
        "url_for('cliente.novo')",
        "url_for('cliente.editar')",
        "url_for('cliente.excluir')",
        "limite_credito",
        "desconto_padrao",
        "forma_pagamento_padrao",
        "prazo_pagamento_padrao",
        "observacoes_internas",
        "Histórico de Vendas",
    ):
        assert proibido not in html, f"{nome} expõe conteúdo proibido: {proibido}"

# O novo fluxo operacional pode iniciar cadastro e OS.
assert "url_for('cliente.novo_operacional')" in lista
assert "url_for('ordem_servico.novo_operacional', cliente_id=cliente.id)" in view

for esperado in ("cliente.nome_display", "cliente.documento_formatado", "cliente.cidade"):
    assert esperado in lista
for esperado in ("cliente.endereco_completo", "cliente.telefone", "cliente.email", "cliente.observacoes"):
    assert esperado in view

print("COLABORADOR CLIENTES CONSULTA: OK")
