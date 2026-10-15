# -*- coding: utf-8 -*-
"""G5-F5: registro transacional de eventos e conferência de integridade.

Os eventos são acrescentados NA MESMA TRANSAÇÃO que cria/salva/conclui.
Não há assinatura digital ou prova criptográfica de identidade;
o SHA-256 detecta divergência do snapshot das respostas armazenadas.
"""
import hashlib
import json
from datetime import datetime

from app.extensoes import db
from app.auth.usuario_model import Usuario
from app.geradores.gerador_checklist_evento_model import GeradorChecklistEvento


ACAO_LABEL = {
    "CRIADO": "Checklist iniciado",
    "RASCUNHO_SALVO": "Rascunho salvo",
    "CONCLUIDO": "Checklist concluído",
}


def hash_respostas(respostas):
    if not isinstance(respostas, dict):
        raise ValueError("Snapshot de respostas inválido para auditoria.")
    conteudo = json.dumps(
        respostas, ensure_ascii=False, sort_keys=True,
        separators=(",", ":"), allow_nan=False,
    )
    return hashlib.sha256(conteudo.encode("utf-8")).hexdigest()


def registrar_evento(execucao, *, acao, usuario_id):
    """Acrescenta evento; requer bloqueio transacional da execução no chamador."""
    if acao not in ACAO_LABEL:
        raise ValueError("Ação de auditoria inválida.")
    if execucao.id is None:
        raise ValueError("Checklist ainda não persistido.")
    ultimo = (
        GeradorChecklistEvento.query
        .filter_by(execucao_id=execucao.id)
        .order_by(GeradorChecklistEvento.sequencia.desc())
        .first()
    )
    usuario = db.session.get(Usuario, usuario_id)
    if usuario is None or not usuario.ativo:
        raise ValueError("Usuário responsável pela ação indisponível.")
    evento = GeradorChecklistEvento(
        execucao_id=execucao.id,
        sequencia=1 if ultimo is None else ultimo.sequencia + 1,
        acao=acao,
        estado_resultante=execucao.estado,
        usuario_id=usuario.id,
        usuario_nome=(usuario.nome or usuario.usuario or f"Usuário #{usuario.id}")[:120],
        registrado_em=datetime.utcnow(),
        sha256_respostas=hash_respostas(execucao.respostas_snapshot),
    )
    db.session.add(evento)
    db.session.flush()
    return evento


def consultar_historico(execucao_id):
    return (
        GeradorChecklistEvento.query
        .filter_by(execucao_id=execucao_id, ativo=True)
        .order_by(GeradorChecklistEvento.sequencia.asc())
        .all()
    )


def conferir_integridade(execucao, eventos):
    """Confronta hash do último registro com as respostas armazenadas.

    Não é assinatura digital nem atestado de execução.
    """
    if not eventos:
        return False
    ultimo = eventos[-1]
    return (
        ultimo.estado_resultante == execucao.estado
        and ultimo.sha256_respostas == hash_respostas(execucao.respostas_snapshot)
        and (
            execucao.estado != "CONCLUIDO"
            or ultimo.acao == "CONCLUIDO"
        )
    )
