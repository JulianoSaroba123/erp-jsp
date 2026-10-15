# -*- coding: utf-8 -*-
"""G5-F3: criar, preencher e concluir checklists sem efeitos financeiros.

Snapshot congela dados técnicos, identidade da OS e itens vigentes.
Nenhuma função confirma transações: commit é responsabilidade da rota.
"""
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy.orm import joinedload

from app.extensoes import db
from app.geradores.gerador_checklist_catalogo import (
    ChecklistDominioError, VERSAO_CATALOGO, obter_modelo,
    validar_respostas,
)
from app.geradores.gerador_checklist_execucao_model import GeradorChecklistExecucao
from app.geradores.gerador_os_vinculo_model import GeradorOSVinculo
from app.geradores.gerador_componente_model import (
    GeradorMotor, GeradorAlternador, GeradorControladora, GeradorQTA,
)
from app.geradores.gerador_partida_model import GeradorBateria, GeradorCarregador
from app.geradores.gerador_consumivel_model import GeradorConsumivel
from app.geradores.gerador_os_vinculo_service import _id_positivo


class ExecucaoChecklistError(ValueError):
    pass


def _ativo_e_consistente(vinculo):
    if vinculo is None or not vinculo.ativo:
        raise ExecucaoChecklistError("Vínculo OS-gerador não encontrado.")
    os = vinculo.ordem_servico
    gerador = vinculo.gerador
    if os is None or not os.ativo or gerador is None or not gerador.ativo:
        raise ExecucaoChecklistError("OS ou gerador indisponível.")
    if os.cliente_id != gerador.cliente_id:
        raise ExecucaoChecklistError("Inconsistência de cliente: operação bloqueada.")
    if str(os.status or "").strip().lower() in {"cancelada", "cancelado"}:
        raise ExecucaoChecklistError("OS cancelada: operação bloqueada.")
    return os, gerador


def _ultima_ficha(classe, gerador_id):
    return (
        classe.query
        .filter_by(gerador_id=gerador_id, ativo=True)
        .order_by(classe.id.desc())
        .first()
    )


def _texto(valor):
    if valor is None:
        return None
    if isinstance(valor, Decimal):
        return format(valor, "f")
    if isinstance(valor, (date, datetime)):
        return valor.isoformat()
    return str(valor)


def _campos(objeto, *nomes):
    if objeto is None:
        return {}
    return {nome: _texto(getattr(objeto, nome, None)) for nome in nomes}


def _snapshot_identificacao(vinculo, os, gerador):
    consumiveis = (
        GeradorConsumivel.query.filter_by(gerador_id=gerador.id, ativo=True)
        .order_by(GeradorConsumivel.tipo.asc(), GeradorConsumivel.id.asc()).all()
    )
    return {
        "vinculo_id": vinculo.id,
        "os": {
            "id": os.id, "numero": os.numero, "titulo": os.titulo,
            "data_abertura": _texto(os.data_abertura),
        },
        "cliente": {
            "id": os.cliente_id,
            "nome": _texto(getattr(os.cliente, "nome", None)),
        },
        "gerador": {
            "id": gerador.id, "codigo": gerador.codigo,
            "descricao": gerador.descricao,
            "fabricante": gerador.fabricante_grupo,
            "modelo": gerador.modelo, "numero_serie": gerador.numero_serie,
            "potencia_kva": _texto(gerador.potencia_standby_kva),
            "tensao": gerador.tensao,
            "local_instalado": gerador.local_instalado,
        },
        "motor": _campos(
            _ultima_ficha(GeradorMotor, gerador.id),
            "fabricante", "modelo", "numero_serie",
        ),
        "alternador": _campos(
            _ultima_ficha(GeradorAlternador, gerador.id),
            "fabricante", "modelo", "numero_serie",
        ),
        "controladora": _campos(
            _ultima_ficha(GeradorControladora, gerador.id),
            "fabricante", "modelo",
        ),
        "qta": _campos(
            _ultima_ficha(GeradorQTA, gerador.id),
            "fabricante", "modelo",
        ),
        "bateria": _campos(
            _ultima_ficha(GeradorBateria, gerador.id),
            "fabricante", "modelo", "tensao_nominal_v",
        ),
        "carregador": _campos(
            _ultima_ficha(GeradorCarregador, gerador.id),
            "fabricante", "modelo", "tensao_nominal_v",
        ),
        "consumiveis": [
            {
                "tipo": item.tipo,
                "fabricante": item.fabricante_original,
                "referencia": item.referencia_original,
                "descricao": item.descricao,
                "quantidade": _texto(item.quantidade),
                "unidade": item.unidade,
            }
            for item in consumiveis
        ],
    }


def listar_checklists_os(os_id):
    os_id = _id_positivo(os_id, "OS")
    return (
        GeradorChecklistExecucao.query
        .join(GeradorOSVinculo, GeradorChecklistExecucao.vinculo_id == GeradorOSVinculo.id)
        .filter(
            GeradorOSVinculo.ordem_servico_id == os_id,
            GeradorOSVinculo.ativo.is_(True),
            GeradorChecklistExecucao.ativo.is_(True),
        )
        .order_by(GeradorChecklistExecucao.id.asc())
        .all()
    )


def criar_checklist(vinculo_id, tipo, *, usuario_id):
    vinculo_id = _id_positivo(vinculo_id, "Vínculo")
    usuario_id = _id_positivo(usuario_id, "Usuário")
    modelo = obter_modelo(tipo)
    vinculo = (
        GeradorOSVinculo.query
        .filter_by(id=vinculo_id, ativo=True)
        .with_for_update()
        .first()
    )
    os, gerador = _ativo_e_consistente(vinculo)
    anterior = GeradorChecklistExecucao.query.filter_by(
        vinculo_id=vinculo.id, tipo_plano=modelo["tipo"]
    ).first()
    if anterior:
        if not anterior.ativo:
            raise ExecucaoChecklistError("Checklist histórico inativo: revisão necessária.")
        return anterior, False

    vazio = validar_respostas(modelo["tipo"], {})
    execucao = GeradorChecklistExecucao(
        vinculo_id=vinculo.id,
        tipo_plano=modelo["tipo"],
        versao_catalogo=VERSAO_CATALOGO,
        estado=GeradorChecklistExecucao.ESTADO_RASCUNHO,
        modelo_snapshot=modelo,
        identificacao_snapshot=_snapshot_identificacao(vinculo, os, gerador),
        respostas_snapshot=vazio,
        data_servico=date.today(),
        criado_por_id=usuario_id,
        atualizado_por_id=usuario_id,
    )
    db.session.add(execucao)
    db.session.flush()
    return execucao, True


def obter_checklist(execucao_id, *, bloquear=False, leitura_historica=False):
    """Documentos concluídos podem ser consultados mesmo após inativação.

    Uma mudança posterior no equipamento/OS não apaga evidências do passado.
    Edição/criação continuam exigindo vínculo, OS e gerador ativos e consistentes.
    """
    execucao_id = _id_positivo(execucao_id, "Checklist")
    query = GeradorChecklistExecucao.query.filter_by(id=execucao_id, ativo=True)
    if bloquear:
        query = query.with_for_update()
    execucao = query.first()
    if execucao is None:
        raise ExecucaoChecklistError("Checklist não encontrado.")
    if not (leitura_historica and
            execucao.estado == GeradorChecklistExecucao.ESTADO_CONCLUIDO):
        _ativo_e_consistente(execucao.vinculo)
    return execucao


def salvar_checklist(
    execucao_id, respostas, *, usuario_id, concluir=False,
    observacoes_gerais="", data_servico=None,
):
    usuario_id = _id_positivo(usuario_id, "Usuário")
    execucao = obter_checklist(execucao_id, bloquear=True)
    if execucao.estado != GeradorChecklistExecucao.ESTADO_RASCUNHO:
        raise ExecucaoChecklistError("Checklist concluído é imutável.")
    if execucao.versao_catalogo != VERSAO_CATALOGO:
        raise ExecucaoChecklistError(
            "Versão antiga do catálogo: necessária revisão técnica antes de editar."
        )
    if execucao.modelo_snapshot != obter_modelo(execucao.tipo_plano):
        raise ExecucaoChecklistError(
            "O catálogo deste checklist não corresponde à versão original."
        )

    if not isinstance(observacoes_gerais, str) or len(observacoes_gerais) > 4000:
        raise ExecucaoChecklistError("Observações gerais inválidas ou extensas.")

    data_valida = execucao.data_servico
    if data_servico is not None:
        try:
            data_valida = date.fromisoformat(data_servico)
        except (ValueError, TypeError):
            raise ExecucaoChecklistError("Data de execução inválida.") from None
        if data_valida > date.today():
            raise ExecucaoChecklistError("Data futura não permitida.")

    try:
        validado = validar_respostas(
            execucao.tipo_plano, respostas, encerrar=concluir,
        )
    except ChecklistDominioError as e:
        raise ExecucaoChecklistError(str(e)) from e

    execucao.respostas_snapshot = validado
    execucao.observacoes_gerais = observacoes_gerais.strip() or None
    execucao.data_servico = data_valida
    execucao.atualizado_por_id = usuario_id
    if concluir:
        execucao.estado = GeradorChecklistExecucao.ESTADO_CONCLUIDO
        execucao.concluido_por_id = usuario_id
        execucao.concluido_em = datetime.utcnow()
    db.session.flush()
    return execucao
