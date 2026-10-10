# -*- coding: utf-8 -*-
"""Expiracao de sessao por inatividade (30 min), aplicada no servidor.

O marcador na sessao e obrigatorio: cookies antigos ou restaurados pelo
'lembrar-me' nunca podem reconstruir uma sessao valida sem login novo.
A atividade e renovada somente por navegacao do usuario ou ping protegido
por token CSRF, nao por polling automatico de APIs/arquivos estaticos.
"""

import hmac
import secrets
import time

from flask import flash, jsonify, redirect, request, session, url_for
from flask_login import current_user, logout_user

IDLE_SECONDS = 30 * 60
WARNING_SECONDS = 2 * 60
_LAST_ACTIVITY = "_jsp_idle_last_at"
_CSRF = "_jsp_idle_csrf"


def activate_idle_session():
    """Chamar somente depois de login_user() bem-sucedido."""
    session.permanent = True
    session[_LAST_ACTIVITY] = time.time()
    session[_CSRF] = secrets.token_urlsafe(32)
    # Elimina qualquer remember cookie criado em logins anteriores.
    session["_remember"] = "clear"


def expire_idle_session():
    """Revoga a sessao e pede ao Flask-Login para limpar remember cookie."""
    logout_user()
    session.clear()
    session["_remember"] = "clear"


def _is_user_navigation():
    """Contar navegacao de pagina/formulario, nao requisicoes de fundo."""
    if request.method not in {"GET", "POST"}:
        return False
    mode = request.headers.get("Sec-Fetch-Mode", "")
    if mode == "navigate":
        return True
    # Fallback para navegadores que nao enviam Fetch Metadata.
    # AJAX/JSON sem Sec-Fetch-Mode nao renovam a atividade.
    accept = request.headers.get("Accept", "")
    return (
        not mode
        and "text/html" in accept
        and request.headers.get("X-Requested-With", "").lower()
        != "xmlhttprequest"
    )


def init_idle_session(app):
    """Adiciona o bloqueio global a todas as rotas autenticadas do ERP."""
    if "jsp_idle_ping" in app.view_functions:
        return

    @app.before_request
    def jsp_idle_guard():
        # Recursos estaticos nao sao atividade e nao precisam autenticar.
        if request.endpoint == "static" or request.path.startswith("/static/"):
            return None

        is_ping = request.endpoint == "jsp_idle_ping"

        if not current_user.is_authenticated:
            if is_ping:
                return jsonify({"ok": False, "expired": True}), 401
            return None

        last = session.get(_LAST_ACTIVITY)
        nonce = session.get(_CSRF)
        now = time.time()
        try:
            last = float(last)
        except (TypeError, ValueError):
            last = 0

        # Login antigo, remember token restaurado ou timeout vencido.
        if not last or not nonce or now - last >= IDLE_SECONDS:
            expire_idle_session()
            if is_ping or request.is_json or request.headers.get(
                "X-Requested-With", ""
            ).lower() == "xmlhttprequest":
                return jsonify({"ok": False, "expired": True}), 401
            flash("Sessao encerrada apos 30 minutos sem atividade. Entre novamente.", "info")
            return redirect(url_for("auth.login"))

        # Botao Sair funciona sem gerar nova atividade.
        if request.endpoint == "auth.logout":
            return None

        if is_ping:
            supplied = request.headers.get("X-JSP-Idle-CSRF", "")
            if not supplied or not hmac.compare_digest(str(nonce), supplied):
                return jsonify({"ok": False, "error": "csrf"}), 403
            session[_LAST_ACTIVITY] = now
            return jsonify({"ok": True, "expires_at": now + IDLE_SECONDS})

        if _is_user_navigation():
            session[_LAST_ACTIVITY] = now

        return None

    @app.route("/auth/sessao/atividade", methods=["POST"], endpoint="jsp_idle_ping")
    def jsp_idle_ping():
        # A resposta normal e produzida pelo guard. Nunca chegar aqui sem ele.
        return jsonify({"ok": False, "expired": True}), 401

    @app.after_request
    def jsp_idle_no_cache(response):
        # Impede restauracao de HTML sensivel pelo cache do navegador.
        if response.mimetype == "text/html" and session.get(_LAST_ACTIVITY):
            response.headers["Cache-Control"] = "no-store, private"
        return response
