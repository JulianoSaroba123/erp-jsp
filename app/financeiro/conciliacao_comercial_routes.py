# -*- coding: utf-8 -*-
"""Painel de rastreabilidade comercial x financeiro (sem escrita)."""
from flask import Blueprint, current_app, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from app.financeiro.conciliacao_comercial_service import (
    consultar_conciliacao, formato_brl,
)

bp_conciliacao_comercial = Blueprint(
    "conciliacao_comercial", __name__, template_folder="templates"
)


@bp_conciliacao_comercial.before_request
def exigir_permissao_financeira():
    if not current_user.is_authenticated:
        return redirect(url_for("auth.login"))
    if not current_user.tem_permissao("visualizar_financeiro"):
        flash("Acesso restrito a usuários autorizados do Financeiro.", "error")
        return redirect(url_for("painel.dashboard"))


@bp_conciliacao_comercial.get("/conciliacao-comercial")
@login_required
def painel():
    try:
        dados = consultar_conciliacao(
            tipo=request.args.get("tipo", "todos"),
            situacao=request.args.get("situacao", "revisar"),
            busca=request.args.get("busca", ""),
            pagina=request.args.get("pagina", 1),
        )
    except Exception:
        current_app.logger.exception("Erro ao consultar conciliação comercial")
        flash("Não foi possível consultar os vínculos comerciais. Nenhum dado foi alterado.", "error")
        return redirect(url_for("financeiro.dashboard"))

    return render_template(
        "financeiro/conciliacao_comercial.html",
        dados=dados, brl=formato_brl,
    )
