# -*- coding: utf-8 -*-
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "app/app.py"
AUTH = ROOT / "app/auth/auth_routes.py"


def replace_once(texto, antigo, novo, nome):
    qtd = texto.count(antigo)
    if qtd != 1:
        raise SystemExit(f"ABORTADO: esperado 1 marcador para {nome}, encontrado {qtd}.")
    return texto.replace(antigo, novo, 1)


# -----------------------------------------------------------------------------
# Catraca global: colaborador só pode usar Minhas OS + Perfil/Senha/Logout.
# -----------------------------------------------------------------------------
app = APP.read_text(encoding="utf-8")
if "def restringir_acesso_global_colaborador():" not in app:
    marcador = """    # Registra blueprints\n    register_blueprints(app)\n    \n    # Registra rotas auxiliares\n"""
    novo = """    # Registra blueprints\n    register_blueprints(app)\n\n    # Catraca global do perfil Colaborador.\n    # Regra de whitelist: qualquer endpoint fora da operação própria é bloqueado.\n    from flask_login import current_user\n    from flask import redirect, url_for\n\n    @app.before_request\n    def restringir_acesso_global_colaborador():\n        if not getattr(current_user, 'is_authenticated', False):\n            return None\n        if getattr(current_user, 'tipo_usuario', None) != 'colaborador':\n            return None\n\n        endpoint = request.endpoint\n        if endpoint is None:\n            return None\n\n        endpoints_permitidos = {\n            'ordem_servico.listar',\n            'ordem_servico.visualizar',\n            'ordem_servico.apontamento_colaborador',\n            'auth.perfil',\n            'auth.alterar_senha',\n            'auth.logout',\n            'auth.login',\n        }\n\n        if endpoint == 'static' or endpoint.endswith('.static'):\n            return None\n        if endpoint in endpoints_permitidos:\n            return None\n\n        return redirect(url_for('ordem_servico.listar'))\n    \n    # Registra rotas auxiliares\n"""
    app = replace_once(app, marcador, novo, "guard global colaborador")
APP.write_text(app, encoding="utf-8")


# -----------------------------------------------------------------------------
# Login: colaborador já nasce em Minhas OS, sem passar pelo dashboard geral.
# -----------------------------------------------------------------------------
auth = AUTH.read_text(encoding="utf-8")
if "tipo_usuario', None) == 'colaborador'" not in auth.split("# Se já está logado, redireciona para dashboard", 1)[1].split("if request.method == 'POST':", 1)[0]:
    auth = replace_once(
        auth,
        """    # Se já está logado, redireciona para dashboard\n    if current_user.is_authenticated:\n        return redirect(url_for('painel.dashboard'))\n""",
        """    # Se já está logado, respeita o destino permitido pelo perfil.\n    if current_user.is_authenticated:\n        if getattr(current_user, 'tipo_usuario', None) == 'colaborador':\n            return redirect(url_for('ordem_servico.listar'))\n        return redirect(url_for('painel.dashboard'))\n""",
        "redirect usuário já autenticado",
    )

if "usuario.tipo_usuario == 'colaborador'" not in auth:
    auth = replace_once(
        auth,
        """                # Redireciona para página solicitada ou dashboard\n                next_page = request.args.get('next')\n                if not next_page or not is_safe_url(next_page):\n                    next_page = url_for('painel.dashboard')\n                \n                return redirect(next_page)\n""",
        """                # Redireciona conforme o perfil. Colaborador entra direto em Minhas OS.\n                next_page = request.args.get('next')\n                if usuario.tipo_usuario == 'colaborador':\n                    next_page = url_for('ordem_servico.listar')\n                elif not next_page or not is_safe_url(next_page):\n                    next_page = url_for('painel.dashboard')\n                \n                return redirect(next_page)\n""",
        "redirect pós-login",
    )
AUTH.write_text(auth, encoding="utf-8")

print("OK - Whitelist global do colaborador aplicada.")
