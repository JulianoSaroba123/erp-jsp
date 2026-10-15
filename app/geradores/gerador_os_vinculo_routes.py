# -*- coding: utf-8 -*-
"""G5-F2: tela administrativa de vínculo OS ↔ Gerador.

Por enquanto apenas administradores. Colaboradores serão habilitados
somente após autorização por objeto/OS na etapa de execução digital.
"""
import hmac
import secrets

from flask import (
    Blueprint, abort, current_app, flash, redirect,
    render_template, request, session, url_for,
)
from flask_login import current_user, login_required
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from app.extensoes import db
from app.geradores.gerador_os_vinculo_service import (
    GeradorOSVinculoError, candidatos_da_os, listar_vinculos_os,
    obter_os_ativa, vincular_gerador_os,
)


gerador_os_vinculo_bp = Blueprint(
    "gerador_os_vinculo", __name__,
    url_prefix="/geradores/os",
    template_folder="templates",
)


def _exigir_admin():
    if getattr(current_user, "tipo_usuario", None) != "admin":
        abort(403)


def _csrf_token():
    chave = "_csrf_geradores_g5_f2"
    token = session.get(chave)
    if not token:
        token = secrets.token_urlsafe(32)
        session[chave] = token
    return token


def _validar_csrf():
    esperado = session.get("_csrf_geradores_g5_f2", "")
    recebido = request.form.get("csrf_token_g5", "")
    if not esperado or not hmac.compare_digest(esperado, recebido):
        abort(400, description="Token CSRF inválido.")


@gerador_os_vinculo_bp.get("/<int:os_id>/geradores")
@login_required
def geradores_da_os(os_id):
    _exigir_admin()
    ordem = obter_os_ativa(os_id)
    if ordem is None:
        abort(404)
    try:
        vinculados = listar_vinculos_os(os_id)
        candidatos = candidatos_da_os(os_id)
    except GeradorOSVinculoError:
        abort(404)
    ja_vinculados = {x.gerador_id for x in vinculados}
    return render_template(
        "geradores/geradores_da_os_g5.html",
        ordem=ordem,
        vinculados=vinculados,
        candidatos=candidatos,
        ja_vinculados=ja_vinculados,
        csrf_token_g5=_csrf_token(),
    )


@gerador_os_vinculo_bp.post("/<int:os_id>/geradores/vincular")
@login_required
def vincular(os_id):
    _exigir_admin()
    _validar_csrf()
    if obter_os_ativa(os_id) is None:
        abort(404)
    try:
        vinculo, criado = vincular_gerador_os(
            os_id, request.form.get("gerador_id"),
            usuario_id=current_user.id,
        )
        db.session.commit()
        flash(
            f"Gerador vinculado à OS (vínculo #{vinculo.id})."
            if criado else "Este gerador já está vinculado à OS.",
            "success" if criado else "info",
        )
    except GeradorOSVinculoError as erro:
        db.session.rollback()
        flash(str(erro), "warning")
    except IntegrityError:
        db.session.rollback()
        flash(
            "Associação simultânea ou duplicada detectada. "
            "Recarregue a lista antes de tentar novamente.", "warning",
        )
    except SQLAlchemyError:
        db.session.rollback()
        current_app.logger.exception("Erro G5-F2 ao vincular gerador à OS")
        flash("Não foi possível salvar o vínculo.", "danger")
    return redirect(
        url_for("gerador_os_vinculo.geradores_da_os", os_id=os_id)
    )
