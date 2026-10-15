# -*- coding: utf-8 -*-
"""G5-F3: interface admin para checklist digital e histórico imutável."""
import hmac
import secrets

from flask import (
    Blueprint, abort, current_app, flash, redirect,
    render_template, request, session, url_for,
)
from flask_login import current_user, login_required
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from app.extensoes import db
from app.geradores.gerador_checklist_catalogo import (
    STATUS_VALIDOS, STATUS_ROTULOS, itens_do_modelo,
)
from app.geradores.gerador_checklist_execucao_service import (
    ExecucaoChecklistError, criar_checklist, listar_checklists_os,
    obter_checklist, salvar_checklist,
)
from app.geradores.gerador_os_vinculo_service import (
    GeradorOSVinculoError, listar_vinculos_os, obter_os_ativa,
)


gerador_checklist_bp = Blueprint(
    "gerador_checklist", __name__, url_prefix="/geradores/checklists",
    template_folder="templates",
)


def _admin():
    if getattr(current_user, "tipo_usuario", None) != "admin":
        abort(403)


def _csrf_token():
    key = "_csrf_geradores_g5_f3"
    token = session.get(key)
    if not token:
        token = secrets.token_urlsafe(32)
        session[key] = token
    return token


def _csrf_valido():
    recebido = request.form.get("csrf_token_g5_f3", "")
    esperado = session.get("_csrf_geradores_g5_f3", "")
    if not esperado or not hmac.compare_digest(esperado, recebido):
        abort(400, description="CSRF inválido.")


@gerador_checklist_bp.get("/os/<int:os_id>")
@login_required
def listar_os(os_id):
    _admin()
    ordem = obter_os_ativa(os_id)
    if ordem is None:
        abort(404)
    return render_template(
        "geradores/checklists_os_g5.html",
        ordem=ordem,
        vinculados=listar_vinculos_os(os_id),
        checklists=listar_checklists_os(os_id),
        csrf_token_g5_f3=_csrf_token(),
    )


@gerador_checklist_bp.post("/vinculos/<int:vinculo_id>/iniciar")
@login_required
def iniciar(vinculo_id):
    _admin()
    _csrf_valido()
    try:
        checklist, criado = criar_checklist(
            vinculo_id,
            request.form.get("tipo_plano"),
            usuario_id=current_user.id,
        )
        db.session.commit()
        flash(
            "Checklist criado e pronto para preenchimento."
            if criado else "Checklist existente recuperado sem duplicação.",
            "success" if criado else "info",
        )
        return redirect(
            url_for("gerador_checklist.editar", execucao_id=checklist.id)
        )
    except (ExecucaoChecklistError, GeradorOSVinculoError, ValueError) as erro:
        db.session.rollback()
        flash(str(erro), "warning")
    except IntegrityError:
        db.session.rollback()
        flash("Checklist já existe. Reabra pela listagem.", "warning")
    except SQLAlchemyError:
        db.session.rollback()
        current_app.logger.exception("G5-F3: falha ao criar checklist")
        flash("Não foi possível criar o checklist.", "danger")
    return redirect(url_for("geradores.listar"))


@gerador_checklist_bp.get("/<int:execucao_id>")
@login_required
def editar(execucao_id):
    _admin()
    try:
        execucao = obter_checklist(execucao_id, leitura_historica=True)
    except ExecucaoChecklistError:
        abort(404)
    respostas = {
        x["item_id"]: x
        for x in (execucao.respostas_snapshot or {}).get("respostas", [])
    }
    return render_template(
        "geradores/checklist_editar_g5.html",
        execucao=execucao,
        respostas=respostas,
        status_validos=STATUS_VALIDOS,
        status_rotulos=STATUS_ROTULOS,
        csrf_token_g5_f3=_csrf_token(),
    )


def _respostas_form(tipo):
    ids = itens_do_modelo(tipo)
    return {
        item_id: {
            "status": request.form.get(f"status__{item_id}", ""),
            "medicao": request.form.get(f"medicao__{item_id}", ""),
            "observacao": request.form.get(f"observacao__{item_id}", ""),
        }
        for item_id in ids
    }


@gerador_checklist_bp.post("/<int:execucao_id>/salvar")
@login_required
def salvar(execucao_id):
    _admin()
    _csrf_valido()
    try:
        execucao = obter_checklist(execucao_id)
        respostas = _respostas_form(execucao.tipo_plano)
        concluir = request.form.get("acao") == "concluir"
        if request.form.get("acao") not in {"salvar", "concluir"}:
            abort(400, description="Ação inválida.")
        campos = {
            "usuario_id": current_user.id,
            "observacoes_gerais": request.form.get("observacoes_gerais", ""),
            "data_servico": request.form.get("data_servico") or None,
        }
        try:
            salvar_checklist(
                execucao_id, respostas, concluir=concluir, **campos,
            )
        except ExecucaoChecklistError as erro:
            if not concluir:
                raise
            # Mesmo que falte item para concluir, salvar respostas válidas
            # como rascunho para não perder o preenchimento de campo.
            db.session.rollback()
            try:
                salvar_checklist(
                    execucao_id, respostas, concluir=False, **campos,
                )
                db.session.commit()
                flash(
                    f"Checklist NÃO concluído: {erro}. "
                    "Respostas válidas preservadas como rascunho.",
                    "warning",
                )
                return redirect(
                    url_for("gerador_checklist.editar", execucao_id=execucao_id)
                )
            except ExecucaoChecklistError:
                db.session.rollback()
                raise erro
        db.session.commit()
        flash(
            "Checklist concluído e bloqueado para edição."
            if concluir else "Rascunho salvo com sucesso.",
            "success",
        )
    except ExecucaoChecklistError as erro:
        db.session.rollback()
        flash(str(erro), "warning")
    except SQLAlchemyError:
        db.session.rollback()
        current_app.logger.exception("G5-F3: falha ao salvar checklist")
        flash("Não foi possível salvar o checklist.", "danger")
    return redirect(url_for("gerador_checklist.editar", execucao_id=execucao_id))
