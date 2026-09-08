# -*- coding: utf-8 -*-
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "app/app.py"
BASE = ROOT / "app/templates/base.html"
ROTAS = ROOT / "app/cliente/cliente_routes.py"


def replace_once(texto, antigo, novo, nome):
    qtd = texto.count(antigo)
    if qtd != 1:
        raise SystemExit(f"ABORTADO: esperado 1 marcador para {nome}, encontrado {qtd}.")
    return texto.replace(antigo, novo, 1)


# Whitelist global: libera apenas leitura de clientes.
app = APP.read_text(encoding="utf-8")
if "'cliente.listar'" not in app.split("endpoints_permitidos = {", 1)[1].split("}", 1)[0]:
    app = replace_once(
        app,
        """            'ordem_servico.apontamento_colaborador',\n            'auth.perfil',\n""",
        """            'ordem_servico.apontamento_colaborador',\n            'cliente.listar',\n            'cliente.visualizar',\n            'auth.perfil',\n""",
        "whitelist clientes",
    )
APP.write_text(app, encoding="utf-8")


# Menu do colaborador: Minhas OS + Clientes.
base = BASE.read_text(encoding="utf-8")
if "url_for('cliente.listar')" not in base.split("MINHA OPERAÇÃO", 1)[1].split("{% endif %}", 1)[0]:
    base = replace_once(
        base,
        """            <div class=\"nav-item\">\n                <a href=\"{{ url_for('ordem_servico.listar') }}\" class=\"nav-link\">\n                    <i class=\"nav-icon fas fa-wrench\"></i>\n                    <span class=\"nav-text\">Minhas OS</span>\n                </a>\n            </div>\n            {% endif %}\n""",
        """            <div class=\"nav-item\">\n                <a href=\"{{ url_for('ordem_servico.listar') }}\" class=\"nav-link\">\n                    <i class=\"nav-icon fas fa-wrench\"></i>\n                    <span class=\"nav-text\">Minhas OS</span>\n                </a>\n            </div>\n            <div class=\"nav-item\">\n                <a href=\"{{ url_for('cliente.listar') }}\" class=\"nav-link\">\n                    <i class=\"nav-icon fas fa-address-book\"></i>\n                    <span class=\"nav-text\">Clientes</span>\n                </a>\n            </div>\n            {% endif %}\n""",
        "menu clientes colaborador",
    )
BASE.write_text(base, encoding="utf-8")


# Cliente: usa telas dedicadas de somente consulta para colaborador.
rotas = ROTAS.read_text(encoding="utf-8")
if "from flask_login import current_user" not in rotas:
    rotas = replace_once(
        rotas,
        "from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, abort\n",
        "from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, abort\nfrom flask_login import current_user\n",
        "import current_user cliente",
    )

if "cliente/listar_colaborador.html" not in rotas:
    rotas = replace_once(
        rotas,
        "    return render_template('cliente/listar.html', clientes=clientes, busca=busca)\n",
        """    if getattr(current_user, 'tipo_usuario', None) == 'colaborador':\n        return render_template('cliente/listar_colaborador.html', clientes=clientes, busca=busca)\n\n    return render_template('cliente/listar.html', clientes=clientes, busca=busca)\n""",
        "render lista cliente colaborador",
    )

if "cliente/visualizar_colaborador.html" not in rotas:
    rotas = replace_once(
        rotas,
        "    return render_template('cliente/visualizar.html', cliente=cliente)\n",
        """    if getattr(current_user, 'tipo_usuario', None) == 'colaborador':\n        return render_template('cliente/visualizar_colaborador.html', cliente=cliente)\n\n    return render_template('cliente/visualizar.html', cliente=cliente)\n""",
        "render visualização cliente colaborador",
    )

ROTAS.write_text(rotas, encoding="utf-8")

print("OK - Consulta de Clientes para colaborador aplicada.")
