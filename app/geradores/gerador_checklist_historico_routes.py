# -*- coding: utf-8 -*-
"""G5-F5: consulta somente leitura ao histórico técnico de um checklist."""
from flask import Blueprint, abort, render_template
from flask_login import current_user, login_required

from app.geradores.gerador_checklist_execucao_service import (
    ExecucaoChecklistError, obter_checklist,
)
from app.geradores.gerador_checklist_auditoria_service import (
    ACAO_LABEL, conferir_integridade, consultar_historico,
)


gerador_checklist_historico_bp = Blueprint(
    "gerador_checklist_historico", __name__,
    url_prefix="/geradores/checklists",
    template_folder="templates",
)


@gerador_checklist_historico_bp.get("/<int:execucao_id>/historico")
@login_required
def historico(execucao_id):
    if getattr(current_user, "tipo_usuario", None) != "admin":
        abort(403)
    try:
        execucao = obter_checklist(
            execucao_id, leitura_historica=True,
        )
    except ExecucaoChecklistError:
        abort(404)
    eventos = consultar_historico(execucao.id)
    integridade_ok = conferir_integridade(execucao, eventos)
    return render_template(
        "geradores/checklist_historico_g5.html",
        execucao=execucao,
        eventos=eventos,
        acao_rotulos=ACAO_LABEL,
        integridade_ok=integridade_ok,
    )
