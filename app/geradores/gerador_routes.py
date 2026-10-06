# -*- coding: utf-8 -*-
"""Rotas iniciais do modulo GERADORES."""

from flask import Blueprint, render_template, request

from app.extensoes import db
from app.geradores.gerador_model import Gerador
from app.geradores.gerador_horimetro_model import GeradorHorimetro
from app.geradores.gerador_plano_model import GeradorPlanoManutencao
from app.geradores.gerador_plano_service import calcular_programacao


geradores_bp = Blueprint(
    "geradores",
    __name__,
    template_folder="templates",
    url_prefix="/geradores",
)


@geradores_bp.route("/")
@geradores_bp.route("/listar")
def listar():
    """Tela principal do prontuario de grupos geradores."""

    busca = request.args.get("busca", "").strip()

    query = Gerador.query.filter(
        Gerador.ativo.is_(True)
    )

    if busca:
        termo = f"%{busca}%"

        query = query.filter(
            db.or_(
                Gerador.codigo.ilike(termo),
                Gerador.descricao.ilike(termo),
                Gerador.fabricante_grupo.ilike(termo),
                Gerador.modelo.ilike(termo),
                Gerador.numero_serie.ilike(termo),
            )
        )

    geradores = query.order_by(
        Gerador.codigo.asc()
    ).all()

    registros = []

    for gerador in geradores:

        ultimo_horimetro = (
            GeradorHorimetro.query
            .filter_by(
                gerador_id=gerador.id,
                ativo=True,
            )
            .order_by(
                GeradorHorimetro.data_leitura.desc(),
                GeradorHorimetro.id.desc(),
            )
            .first()
        )

        vinculo_plano = (
            GeradorPlanoManutencao.query
            .filter_by(
                gerador_id=gerador.id,
                ativo=True,
            )
            .order_by(
                GeradorPlanoManutencao.id.desc()
            )
            .first()
        )

        programacao = None

        if vinculo_plano:
            try:
                programacao = calcular_programacao(
                    vinculo_plano.id
                )
            except Exception:
                programacao = None

        registros.append(
            {
                "gerador": gerador,
                "ultimo_horimetro": ultimo_horimetro,
                "vinculo_plano": vinculo_plano,
                "programacao": programacao,
            }
        )

    return render_template(
        "geradores/listar.html",
        registros=registros,
        busca=busca,
    )
