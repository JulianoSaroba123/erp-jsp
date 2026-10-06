# -*- coding: utf-8 -*-
"""
ERP JSP - Modulo GERADORES
Services de dominio da Fase G2.

Responsabilidades:
- validar gerador;
- validar produto opcional;
- criar componentes tecnicos;
- criar bateria e carregador;
- criar consumiveis;
- criar equivalentes;
- nunca executar commit;
- nunca movimentar estoque.
"""

from app.extensoes import db
from app.produto.produto_model import Produto

from app.geradores.gerador_model import Gerador
from app.geradores.gerador_componente_model import (
    GeradorMotor,
    GeradorAlternador,
    GeradorControladora,
    GeradorQTA,
)
from app.geradores.gerador_partida_model import (
    GeradorBateria,
    GeradorCarregador,
)
from app.geradores.gerador_consumivel_model import (
    GeradorConsumivel,
    GeradorConsumivelEquivalente,
)


class GeradorG2DominioError(ValueError):
    """Erro de regra de negocio da Fase G2."""


def _id_inteiro_positivo(valor, campo):
    try:
        valor_int = int(valor)
    except (TypeError, ValueError) as exc:
        raise GeradorG2DominioError(
            f"{campo} invalido."
        ) from exc

    if valor_int <= 0:
        raise GeradorG2DominioError(
            f"{campo} invalido."
        )

    return valor_int


def _validar_campos(dados, permitidos):
    desconhecidos = set(dados) - set(permitidos)

    if desconhecidos:
        lista = ", ".join(sorted(desconhecidos))

        raise GeradorG2DominioError(
            f"Campos nao permitidos: {lista}."
        )


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
        raise GeradorG2DominioError(
            "Gerador nao encontrado ou inativo."
        )

    return gerador


def _carregar_produto_opcional(produto_id):
    if produto_id in (None, ""):
        return None

    produto_id = _id_inteiro_positivo(
        produto_id,
        "produto_id",
    )

    produto = db.session.get(
        Produto,
        produto_id,
    )

    if produto is None or not produto.ativo:
        raise GeradorG2DominioError(
            "Produto nao encontrado ou inativo."
        )

    return produto

CAMPOS_MOTOR = {
    "fabricante",
    "modelo",
    "variante",
    "numero_serie",
    "quantidade_cilindros",
    "cilindrada_l",
    "aspiracao",
    "turbo",
    "intercooler",
    "potencia",
    "potencia_unidade",
    "rpm",
    "combustivel",
    "capacidade_oleo_l",
    "especificacao_oleo",
    "pressao_normal_oleo",
    "temperatura_normal",
    "observacoes",
}

CAMPOS_ALTERNADOR = {
    "fabricante",
    "modelo",
    "numero_serie",
    "potencia_kva",
    "tensao",
    "corrente_a",
    "frequencia_hz",
    "rpm",
    "numero_polos",
    "fator_potencia",
    "classe_isolacao",
    "grau_protecao",
    "sistema_excitacao",
    "possui_avr",
    "avr_fabricante",
    "avr_modelo",
    "ligacao",
    "observacoes",
}

CAMPOS_CONTROLADORA = {
    "fabricante",
    "modelo",
    "versao",
    "firmware",
    "tensao_alimentacao",
    "comunicacao",
    "configuracao_relevante",
    "manual_referencia",
    "observacoes",
}

CAMPOS_QTA = {
    "fabricante",
    "modelo",
    "corrente_a",
    "numero_polos",
    "tensao",
    "transferencia",
    "tipo",
    "controle",
    "intertravamento",
    "posicao_normal",
    "observacoes",
}

CAMPOS_BATERIA = {
    "quantidade",
    "tensao_nominal_v",
    "capacidade_ah",
    "fabricante",
    "modelo",
    "data_instalacao",
    "tensao_repouso_v",
    "tensao_partida_v",
    "observacoes",
}

CAMPOS_CARREGADOR = {
    "fabricante",
    "modelo",
    "tensao_nominal_v",
    "corrente_nominal_a",
    "tensao_medida_v",
    "observacoes",
}

CAMPOS_CONSUMIVEL = {
    "fabricante_original",
    "referencia_original",
    "descricao",
    "quantidade",
    "unidade",
    "observacoes",
}

CAMPOS_EQUIVALENTE = {
    "fabricante",
    "descricao",
    "observacoes",
}

def _criar_componente(
    modelo,
    permitidos,
    gerador_id,
    dados,
):
    gerador = _carregar_gerador_ativo(
        gerador_id
    )

    _validar_campos(
        dados,
        permitidos,
    )

    registro = modelo(
        gerador_id=gerador.id,
        **dados,
    )

    db.session.add(registro)
    db.session.flush()

    return registro


def criar_motor(*, gerador_id, **dados):
    return _criar_componente(
        GeradorMotor,
        CAMPOS_MOTOR,
        gerador_id,
        dados,
    )


def criar_alternador(*, gerador_id, **dados):
    return _criar_componente(
        GeradorAlternador,
        CAMPOS_ALTERNADOR,
        gerador_id,
        dados,
    )


def criar_controladora(*, gerador_id, **dados):
    return _criar_componente(
        GeradorControladora,
        CAMPOS_CONTROLADORA,
        gerador_id,
        dados,
    )


def criar_qta(*, gerador_id, **dados):
    tipo = dados.get("tipo")

    if (
        tipo is not None
        and tipo not in GeradorQTA.TIPOS_VALIDOS
    ):
        raise GeradorG2DominioError(
            "Tipo de QTA invalido."
        )

    return _criar_componente(
        GeradorQTA,
        CAMPOS_QTA,
        gerador_id,
        dados,
    )


def criar_bateria(*, gerador_id, **dados):
    return _criar_componente(
        GeradorBateria,
        CAMPOS_BATERIA,
        gerador_id,
        dados,
    )


def criar_carregador(*, gerador_id, **dados):
    return _criar_componente(
        GeradorCarregador,
        CAMPOS_CARREGADOR,
        gerador_id,
        dados,
    )

def criar_consumivel(
    *,
    gerador_id,
    tipo,
    produto_id=None,
    **dados,
):
    gerador = _carregar_gerador_ativo(
        gerador_id
    )

    _validar_campos(
        dados,
        CAMPOS_CONSUMIVEL,
    )

    if tipo not in GeradorConsumivel.TIPOS_VALIDOS:
        raise GeradorG2DominioError(
            "Tipo de consumivel invalido."
        )

    produto = _carregar_produto_opcional(
        produto_id
    )

    consumivel = GeradorConsumivel(
        gerador_id=gerador.id,
        produto_id=(
            produto.id
            if produto is not None
            else None
        ),
        tipo=tipo,
        **dados,
    )

    db.session.add(consumivel)
    db.session.flush()

    return consumivel


def criar_equivalente(
    *,
    consumivel_id,
    referencia,
    **dados,
):
    consumivel_id = _id_inteiro_positivo(
        consumivel_id,
        "consumivel_id",
    )

    _validar_campos(
        dados,
        CAMPOS_EQUIVALENTE,
    )

    consumivel = db.session.get(
        GeradorConsumivel,
        consumivel_id,
    )

    if consumivel is None or not consumivel.ativo:
        raise GeradorG2DominioError(
            "Consumivel nao encontrado ou inativo."
        )

    referencia = str(
        referencia or ""
    ).strip()

    if not referencia:
        raise GeradorG2DominioError(
            "Referencia equivalente e obrigatoria."
        )

    equivalente = GeradorConsumivelEquivalente(
        consumivel_id=consumivel.id,
        referencia=referencia,
        **dados,
    )

    db.session.add(equivalente)
    db.session.flush()

    return equivalente
