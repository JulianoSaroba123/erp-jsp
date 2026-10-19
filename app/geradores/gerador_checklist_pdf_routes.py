# -*- coding: utf-8 -*-
"""G5-F4: exportação de checklists via GET, restrita a administradores."""
from io import BytesIO

from flask import Blueprint, abort, current_app, render_template, request, send_file
from flask_login import current_user, login_required

from app.geradores.gerador_checklist_execucao_service import (
    ExecucaoChecklistError, obter_checklist,
)
from app.geradores.gerador_checklist_pdf_service import (
    PDFChecklistError, gerar_pdf_checklist,
)
from app.geradores.gerador_checklist_generico_pdf_service import gerar_pdf_modelo_generico
from app.geradores.gerador_checklist_auditoria_service import (
    conferir_integridade, consultar_historico,
)


gerador_checklist_pdf_bp = Blueprint(
    "gerador_checklist_pdf", __name__,
    url_prefix="/geradores/checklists",
)


@gerador_checklist_pdf_bp.get("/<int:execucao_id>/pdf")
@login_required
def pdf_checklist(execucao_id):
    if getattr(current_user, "tipo_usuario", None) != "admin":
        abort(403)
    modo = request.args.get("modo", "branco").strip().lower()
    if modo not in {"branco", "preenchido"}:
        abort(400, description="Modo de PDF não reconhecido.")

    try:
        execucao = obter_checklist(
            execucao_id, leitura_historica=True,
        )
    except ExecucaoChecklistError:
        abort(404)

    # Evitar emitir documento concluído se as respostas atuais divergirem
    # do último evento de auditoria. PDF em branco não é prova de execução.
    if modo == "preenchido":
        eventos = consultar_historico(execucao.id)
        if not conferir_integridade(execucao, eventos):
            current_app.logger.error(
                "G5-F5: integridade do checklist %s divergente; PDF bloqueado",
                execucao.id,
            )
            abort(409, description="Integridade do histórico divergente. Revisão necessária.")

    try:
        conteudo = gerar_pdf_checklist(execucao, modo=modo)
    except PDFChecklistError as exc:
        # Rascunhos não podem ser exportados como execução concluída.
        abort(409, description=str(exc))
    except Exception:
        current_app.logger.exception(
            "G5-F4: falha ao gerar PDF do checklist %s", execucao_id
        )
        abort(500, description="Falha interna ao gerar PDF do checklist.")

    nome = (
        f"JSP_G5_Checklist_{execucao_id}_"
        f"{'EM_BRANCO' if modo == 'branco' else 'PREENCHIDO'}.pdf"
    )
    resposta = send_file(
        BytesIO(conteudo),
        mimetype="application/pdf",
        download_name=nome,
        as_attachment=False,
        conditional=False,
    )
    resposta.headers["Cache-Control"] = "private, no-store, max-age=0"
    resposta.headers["Pragma"] = "no-cache"
    resposta.headers["X-Content-Type-Options"] = "nosniff"
    return resposta


@gerador_checklist_pdf_bp.get("/modelo-generico")
@login_required
def modelo_generico():
    """Tela de seleção; não lê nem escreve prontuários/OS."""
    if getattr(current_user, "tipo_usuario", None) != "admin":
        abort(403)
    return render_template("geradores/checklist_generico_g5.html")


@gerador_checklist_pdf_bp.get("/modelo-generico/pdf")
@login_required
def modelo_generico_pdf():
    """PDF referencial genérico, sem IDs reais nem efeitos sobre o banco."""
    if getattr(current_user, "tipo_usuario", None) != "admin":
        abort(403)
    tipo = request.args.get("tipo", "INTERMEDIARIA").strip().upper()
    try:
        pdf = gerar_pdf_modelo_generico(tipo)
    except PDFChecklistError as erro:
        abort(400, description=str(erro))
    except Exception:
        current_app.logger.exception("G5: falha na geração do checklist genérico")
        abort(500, description="Falha ao gerar checklist genérico.")

    resposta = send_file(
        BytesIO(pdf), mimetype="application/pdf",
        download_name=f"JSP_G5_CHECKLIST_GENERICO_{tipo}.pdf",
        as_attachment=False, conditional=False,
    )
    resposta.headers["Cache-Control"] = "private, no-store, max-age=0"
    resposta.headers["Pragma"] = "no-cache"
    resposta.headers["X-Content-Type-Options"] = "nosniff"
    return resposta
