# -*- coding: utf-8 -*-
"""
ERP JSP - Modulo GERADORES
Services de dominio da Fase G3.

Responsabilidades:
- criar planos de manutencao;
- vincular planos aos geradores;
- registrar historico de horimetro;
- preservar horas acumuladas mesmo apos troca/reset do instrumento;
- calcular vencimento por data e/ou horas;
- nunca executar commit.
"""

import calendar
from datetime import date, datetime
from decimal import Decimal, InvalidOperation

from app.extensoes import db
from app.auth.usuario_model import Usuario

from app.geradores.gerador_model import Gerador
from app.geradores.gerador_plano_model import (
    PlanoManutencao,
    GeradorPlanoManutencao,
)
from app.geradores.gerador_horimetro_model import (
    GeradorHorimetro,
)


class GeradorG3DominioError(ValueError):
    """Erro de regra de negocio da Fase G3."""


def _id_inteiro_positivo(valor, campo):
    try:
        valor_int = int(valor)
    except (TypeError, ValueError) as exc:
        raise GeradorG3DominioError(
            f"{campo} invalido."
        ) from exc

    if valor_int <= 0:
        raise GeradorG3DominioError(
            f"{campo} invalido."
        )

    return valor_int


def _texto_obrigatorio(valor, campo):
    texto = str(valor or "").strip()

    if not texto:
        raise GeradorG3DominioError(
            f"{campo} e obrigatorio."
        )

    return texto


def _decimal_opcional(valor, campo, *, positivo=False):
    if valor in (None, ""):
        return None

    try:
        numero = Decimal(str(valor))
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise GeradorG3DominioError(
            f"{campo} invalido."
        ) from exc

    if positivo:
        invalido = numero <= 0
    else:
        invalido = numero < 0

    if invalido:
        operador = "maior que zero" if positivo else "nao negativo"

        raise GeradorG3DominioError(
            f"{campo} deve ser {operador}."
        )

    return numero


def _inteiro_opcional_positivo(valor, campo):
    if valor in (None, ""):
        return None

    try:
        numero = int(valor)
    except (TypeError, ValueError) as exc:
        raise GeradorG3DominioError(
            f"{campo} invalido."
        ) from exc

    if numero <= 0:
        raise GeradorG3DominioError(
            f"{campo} deve ser maior que zero."
        )

    return numero


def _carregar_gerador_ativo(gerador_id):
    gerador_id = _id_inteiro_positivo(
        gerador_id,
        "gerador_id",
    )

    gerador = db.session.get(
        Gerador,
        gerador_id,
    )

    if gerador is None or not gerador.ativo:
        raise GeradorG3DominioError(
            "Gerador nao encontrado ou inativo."
        )

    return gerador


def _carregar_plano_ativo(plano_id):
    plano_id = _id_inteiro_positivo(
        plano_id,
        "plano_id",
    )

    plano = db.session.get(
        PlanoManutencao,
        plano_id,
    )

    if plano is None or not plano.ativo:
        raise GeradorG3DominioError(
            "Plano de manutencao nao encontrado ou inativo."
        )

    return plano


def _carregar_usuario_opcional(usuario_id):
    if usuario_id in (None, ""):
        return None

    usuario_id = _id_inteiro_positivo(
        usuario_id,
        "usuario_id",
    )

    usuario = db.session.get(
        Usuario,
        usuario_id,
    )

    if usuario is None or not usuario.ativo:
        raise GeradorG3DominioError(
            "Usuario nao encontrado ou inativo."
        )

    return usuario


def _validar_heranca_plano(tipo, plano_pai):
    if tipo == PlanoManutencao.TIPO_BASICA:
        if plano_pai is not None:
            raise GeradorG3DominioError(
                "Plano BASICA nao deve possuir plano pai."
            )
        return

    if tipo == PlanoManutencao.TIPO_INTERMEDIARIA:
        if (
            plano_pai is None
            or plano_pai.tipo != PlanoManutencao.TIPO_BASICA
        ):
            raise GeradorG3DominioError(
                "Plano INTERMEDIARIA deve herdar de BASICA."
            )
        return

    if tipo == PlanoManutencao.TIPO_AVANCADA:
        if (
            plano_pai is None
            or plano_pai.tipo != PlanoManutencao.TIPO_INTERMEDIARIA
        ):
            raise GeradorG3DominioError(
                "Plano AVANCADA deve herdar de INTERMEDIARIA."
            )


def criar_plano_manutencao(
    *,
    codigo,
    nome,
    tipo,
    intervalo_horas=None,
    intervalo_meses=None,
    plano_pai_id=None,
    descricao=None,
    observacoes=None,
):
    codigo = _texto_obrigatorio(
        codigo,
        "codigo",
    ).upper()

    nome = _texto_obrigatorio(
        nome,
        "nome",
    )

    tipo = _texto_obrigatorio(
        tipo,
        "tipo",
    ).upper()

    if tipo not in PlanoManutencao.TIPOS_VALIDOS:
        raise GeradorG3DominioError(
            "Tipo de plano de manutencao invalido."
        )

    intervalo_horas = _decimal_opcional(
        intervalo_horas,
        "intervalo_horas",
        positivo=True,
    )

    intervalo_meses = _inteiro_opcional_positivo(
        intervalo_meses,
        "intervalo_meses",
    )

    if (
        intervalo_horas is None
        and intervalo_meses is None
    ):
        raise GeradorG3DominioError(
            "Informe intervalo em horas, meses ou ambos."
        )

    existente = db.session.execute(
        db.select(PlanoManutencao).where(
            PlanoManutencao.codigo == codigo
        )
    ).scalar_one_or_none()

    if existente is not None:
        raise GeradorG3DominioError(
            "Codigo de plano ja cadastrado."
        )

    plano_pai = None

    if plano_pai_id not in (None, ""):
        plano_pai = _carregar_plano_ativo(
            plano_pai_id
        )

    _validar_heranca_plano(
        tipo,
        plano_pai,
    )

    plano = PlanoManutencao(
        codigo=codigo,
        nome=nome,
        tipo=tipo,
        intervalo_horas=intervalo_horas,
        intervalo_meses=intervalo_meses,
        plano_pai_id=(
            plano_pai.id
            if plano_pai is not None
            else None
        ),
        descricao=descricao,
        observacoes=observacoes,
    )

    db.session.add(plano)
    db.session.flush()

    return plano


def _ultimo_horimetro(gerador_id):
    return db.session.execute(
        db.select(GeradorHorimetro)
        .where(
            GeradorHorimetro.gerador_id == gerador_id
        )
        .order_by(
            GeradorHorimetro.data_leitura.desc(),
            GeradorHorimetro.id.desc(),
        )
        .limit(1)
    ).scalar_one_or_none()


def vincular_plano_gerador(
    *,
    gerador_id,
    plano_id,
    data_base_programacao=None,
    horimetro_base_programacao=None,
    observacoes=None,
):
    gerador = _carregar_gerador_ativo(
        gerador_id
    )

    plano = _carregar_plano_ativo(
        plano_id
    )

    existente = db.session.execute(
        db.select(GeradorPlanoManutencao).where(
            GeradorPlanoManutencao.gerador_id == gerador.id,
            GeradorPlanoManutencao.plano_id == plano.id,
            GeradorPlanoManutencao.ativo.is_(True),
        )
    ).scalar_one_or_none()

    if existente is not None:
        raise GeradorG3DominioError(
            "Gerador ja possui este plano ativo."
        )

    if isinstance(data_base_programacao, datetime):
        data_base_programacao = data_base_programacao.date()

    if (
        data_base_programacao is not None
        and not isinstance(data_base_programacao, date)
    ):
        raise GeradorG3DominioError(
            "data_base_programacao invalida."
        )

    horimetro_base_programacao = _decimal_opcional(
        horimetro_base_programacao,
        "horimetro_base_programacao",
    )

    if (
        plano.intervalo_meses is not None
        and data_base_programacao is None
    ):
        raise GeradorG3DominioError(
            "Plano por meses exige data base."
        )

    if (
        plano.intervalo_horas is not None
        and horimetro_base_programacao is None
    ):
        raise GeradorG3DominioError(
            "Plano por horas exige horimetro base."
        )

    ultimo = _ultimo_horimetro(
        gerador.id
    )

    if (
        ultimo is not None
        and horimetro_base_programacao is not None
        and horimetro_base_programacao
        > Decimal(str(ultimo.horas_acumuladas))
    ):
        raise GeradorG3DominioError(
            "Horimetro base nao pode superar "
            "as horas acumuladas atuais."
        )

    vinculo = GeradorPlanoManutencao(
        gerador_id=gerador.id,
        plano_id=plano.id,
        data_base_programacao=data_base_programacao,
        horimetro_base_programacao=horimetro_base_programacao,
        observacoes=observacoes,
    )

    db.session.add(vinculo)
    db.session.flush()

    return vinculo


def registrar_horimetro(
    *,
    gerador_id,
    leitura_atual,
    responsavel,
    data_leitura=None,
    tipo_evento=GeradorHorimetro.EVENTO_NORMAL,
    justificativa=None,
    usuario_id=None,
    observacoes=None,
):
    gerador = _carregar_gerador_ativo(
        gerador_id
    )

    leitura_atual = _decimal_opcional(
        leitura_atual,
        "leitura_atual",
    )

    if leitura_atual is None:
        raise GeradorG3DominioError(
            "leitura_atual e obrigatoria."
        )

    responsavel = _texto_obrigatorio(
        responsavel,
        "responsavel",
    )

    tipo_evento = _texto_obrigatorio(
        tipo_evento,
        "tipo_evento",
    ).upper()

    if tipo_evento not in GeradorHorimetro.EVENTOS_VALIDOS:
        raise GeradorG3DominioError(
            "Tipo de evento do horimetro invalido."
        )

    justificativa_limpa = (
        str(justificativa).strip()
        if justificativa is not None
        else ""
    )

    if (
        tipo_evento != GeradorHorimetro.EVENTO_NORMAL
        and not justificativa_limpa
    ):
        raise GeradorG3DominioError(
            "Evento excepcional exige justificativa."
        )

    if data_leitura is None:
        data_leitura = datetime.now()

    if not isinstance(data_leitura, datetime):
        raise GeradorG3DominioError(
            "data_leitura deve ser datetime."
        )

    usuario = _carregar_usuario_opcional(
        usuario_id
    )

    ultimo = _ultimo_horimetro(
        gerador.id
    )

    leitura_anterior = None

    if ultimo is None:
        horas_acumuladas = leitura_atual

    else:
        if data_leitura < ultimo.data_leitura:
            raise GeradorG3DominioError(
                "Data da leitura nao pode ser anterior "
                "ao ultimo registro."
            )

        leitura_anterior = Decimal(
            str(ultimo.leitura_atual)
        )

        acumulado_anterior = Decimal(
            str(ultimo.horas_acumuladas)
        )

        if tipo_evento == GeradorHorimetro.EVENTO_NORMAL:
            if leitura_atual < leitura_anterior:
                raise GeradorG3DominioError(
                    "Horimetro atual menor que o anterior. "
                    "Informe evento excepcional e justificativa."
                )

            horas_acumuladas = (
                acumulado_anterior
                + leitura_atual
                - leitura_anterior
            )

        else:
            horas_acumuladas = acumulado_anterior

    registro = GeradorHorimetro(
        gerador_id=gerador.id,
        leitura_anterior=leitura_anterior,
        leitura_atual=leitura_atual,
        horas_acumuladas=horas_acumuladas,
        data_leitura=data_leitura,
        responsavel=responsavel,
        usuario_id=(
            usuario.id
            if usuario is not None
            else None
        ),
        tipo_evento=tipo_evento,
        justificativa=(
            justificativa_limpa or None
        ),
        observacoes=observacoes,
    )

    db.session.add(registro)
    db.session.flush()

    return registro


def _somar_meses(data_base, meses):
    indice_mes = (
        data_base.month - 1 + meses
    )

    ano = (
        data_base.year
        + indice_mes // 12
    )

    mes = (
        indice_mes % 12
        + 1
    )

    ultimo_dia = calendar.monthrange(
        ano,
        mes,
    )[1]

    dia = min(
        data_base.day,
        ultimo_dia,
    )

    return date(
        ano,
        mes,
        dia,
    )


def calcular_programacao(
    *,
    vinculo_id,
    data_referencia=None,
):
    vinculo_id = _id_inteiro_positivo(
        vinculo_id,
        "vinculo_id",
    )

    vinculo = db.session.get(
        GeradorPlanoManutencao,
        vinculo_id,
    )

    if vinculo is None or not vinculo.ativo:
        raise GeradorG3DominioError(
            "Vinculo de manutencao nao encontrado ou inativo."
        )

    plano = vinculo.plano

    if plano is None or not plano.ativo:
        raise GeradorG3DominioError(
            "Plano de manutencao nao encontrado ou inativo."
        )

    if data_referencia is None:
        data_referencia = date.today()

    if isinstance(data_referencia, datetime):
        data_referencia = data_referencia.date()

    if not isinstance(data_referencia, date):
        raise GeradorG3DominioError(
            "data_referencia invalida."
        )

    data_limite = None

    if plano.intervalo_meses is not None:
        if vinculo.data_base_programacao is None:
            raise GeradorG3DominioError(
                "Vinculo sem data base para plano por meses."
            )

        data_limite = _somar_meses(
            vinculo.data_base_programacao,
            plano.intervalo_meses,
        )

    horas_limite = None

    if plano.intervalo_horas is not None:
        if vinculo.horimetro_base_programacao is None:
            raise GeradorG3DominioError(
                "Vinculo sem horimetro base "
                "para plano por horas."
            )

        horas_limite = (
            Decimal(
                str(vinculo.horimetro_base_programacao)
            )
            + Decimal(
                str(plano.intervalo_horas)
            )
        )

    ultimo = _ultimo_horimetro(
        vinculo.gerador_id
    )

    horas_atuais = (
        Decimal(str(ultimo.horas_acumuladas))
        if ultimo is not None
        else (
            Decimal(
                str(vinculo.horimetro_base_programacao)
            )
            if vinculo.horimetro_base_programacao is not None
            else None
        )
    )

    vencida_por_data = (
        data_limite is not None
        and data_referencia >= data_limite
    )

    vencida_por_horas = (
        horas_limite is not None
        and horas_atuais is not None
        and horas_atuais >= horas_limite
    )

    return {
        "vinculo_id": vinculo.id,
        "gerador_id": vinculo.gerador_id,
        "plano_id": plano.id,
        "data_referencia": data_referencia,
        "data_limite": data_limite,
        "horas_atuais": horas_atuais,
        "horas_limite": horas_limite,
        "vencida_por_data": vencida_por_data,
        "vencida_por_horas": vencida_por_horas,
        "manutencao_necessaria": (
            vencida_por_data
            or vencida_por_horas
        ),
    }
