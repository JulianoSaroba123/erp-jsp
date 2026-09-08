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

# Whitelist: somente leitura de clientes.
assert "'cliente.listar'" in app
assert "'cliente.visualizar'" in app
for proibido in ("'cliente.novo'", "'cliente.editar'", "'cliente.excluir'"):
    assert proibido not in app.split("endpoints_permitidos = {", 1)[1].split("}", 1)[0]

# Menu operacional inclui Clientes.
bloco_menu = base.split("MINHA OPERAÇÃO", 1)[1].split("{% endif %}", 1)[0]
assert "url_for('cliente.listar')" in bloco_menu
assert ">Clientes<" in bloco_menu

# Rotas entregam templates próprios ao colaborador.
assert "from flask_login import current_user" in rotas
assert "getattr(current_user, 'tipo_usuario', None) == 'colaborador'" in rotas
assert "cliente/listar_colaborador.html" in rotas
assert "cliente/visualizar_colaborador.html" in rotas

# Templates não contêm ações mutáveis nem dados comerciais/financeiros.
for nome, html in (("lista", lista), ("visualizacao", view)):
    for proibido in (
        "cliente.novo",
        "cliente.editar",
        "cliente.excluir",
        "limite_credito",
        "desconto_padrao",
        "forma_pagamento_padrao",
        "prazo_pagamento_padrao",
        "observacoes_internas",
        "Histórico de Vendas",
    ):
        assert proibido not in html, f"{nome} expõe conteúdo proibido: {proibido}"

# Dados operacionais essenciais continuam disponíveis.
for esperado in ("cliente.nome_display", "cliente.documento_formatado", "cliente.cidade"):
    assert esperado in lista
for esperado in ("cliente.endereco_completo", "cliente.telefone", "cliente.email", "cliente.observacoes"):
    assert esperado in view

print("COLABORADOR CLIENTES CONSULTA: OK")
