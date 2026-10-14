# -*- coding: utf-8 -*-
"""G5-F2: associação de OS a gerador com isolamento por cliente.

Funções de domínio não fazem commit, não geram receitas e não movem estoque.
Chamador controla transação; índice UNIQUE protege concorrência.
"""
from sqlalchemy.orm import joinedload

from app.extensoes import db
from app.geradores.gerador_model import Gerador
from app.geradores.gerador_os_vinculo_model import GeradorOSVinculo
from app.ordem_servico.ordem_servico_model import OrdemServico


class GeradorOSVinculoError(ValueError):
    pass


def _id_positivo(valor, campo):
    if isinstance(valor, bool):
        raise GeradorOSVinculoError(f"{campo} inválido.")
    try:
        numero = int(valor)
    except (TypeError, ValueError, OverflowError):
        raise GeradorOSVinculoError(f"{campo} inválido.") from None
    if numero < 1 or str(valor).strip() != str(numero):
        raise GeradorOSVinculoError(f"{campo} inválido.")
    return numero


def obter_os_ativa(os_id, *, bloquear=False):
    os_id = _id_positivo(os_id, "OS")
    consulta = OrdemServico.query.filter_by(id=os_id, ativo=True)
    if bloquear:
        consulta = consulta.with_for_update()
    return consulta.first()


def listar_vinculos_os(os_id):
    """Consulta sem alteração, mantém vínculo histórico por par."""
    ordem = obter_os_ativa(os_id)
    if ordem is None:
        raise GeradorOSVinculoError("OS não encontrada.")
    return (
        GeradorOSVinculo.query
        .options(joinedload(GeradorOSVinculo.gerador))
        .filter_by(ordem_servico_id=ordem.id, ativo=True)
        .order_by(GeradorOSVinculo.id.asc())
        .all()
    )


def candidatos_da_os(os_id):
    """Somente geradores ativos cadastrados para o mesmo cliente."""
    ordem = obter_os_ativa(os_id)
    if ordem is None:
        raise GeradorOSVinculoError("OS não encontrada.")
    return (
        Gerador.query
        .filter_by(cliente_id=ordem.cliente_id, ativo=True)
        .order_by(Gerador.codigo.asc())
        .all()
    )


def vincular_gerador_os(os_id, gerador_id, *, usuario_id):
    """Vincula uma única vez; nenhuma alteração no status da OS.

    O travamento da OS serializa novas associações da mesma OS.
    A UNIQUE do banco também rejeita corridas externas.
    """
    os_id = _id_positivo(os_id, "OS")
    gerador_id = _id_positivo(gerador_id, "Gerador")
    usuario_id = _id_positivo(usuario_id, "Usuário")

    ordem = obter_os_ativa(os_id, bloquear=True)
    if ordem is None:
        raise GeradorOSVinculoError("OS não encontrada ou inativa.")
    if str(ordem.status or "").strip().lower() in {"cancelada", "cancelado"}:
        raise GeradorOSVinculoError("OS cancelada não pode receber vínculos.")

    gerador = (
        Gerador.query
        .filter_by(id=gerador_id, ativo=True)
        .first()
    )
    if gerador is None:
        raise GeradorOSVinculoError("Gerador não encontrado ou inativo.")
    if gerador.cliente_id != ordem.cliente_id:
        raise GeradorOSVinculoError(
            "Gerador pertence a outro cliente. Vínculo bloqueado."
        )

    vinculo = (
        GeradorOSVinculo.query
        .filter_by(ordem_servico_id=ordem.id, gerador_id=gerador.id)
        .first()
    )
    if vinculo is not None:
        if vinculo.ativo:
            return vinculo, False
        raise GeradorOSVinculoError(
            "Vínculo histórico desativado: reativação exige revisão."
        )

    vinculo = GeradorOSVinculo(
        ordem_servico_id=ordem.id,
        gerador_id=gerador.id,
        criado_por_id=usuario_id,
    )
    db.session.add(vinculo)
    db.session.flush()
    return vinculo, True
