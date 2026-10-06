# -*- coding: utf-8 -*-
"""
ERP JSP - Modulo GERADORES
Servicos de dominio da Fase G1.

Responsabilidades atuais:
- validar Cliente;
- validar Unidade x Cliente;
- validar Equipamento x Cliente;
- impedir dois prontuarios para o mesmo Equipamento;
- gerar codigo JSP concorrente via sequence PostgreSQL;
- criar Unidade;
- criar Gerador;
- nao realizar commit proprio.

A sequence geradores_codigo_seq sera criada pela migration da Fase G1.
"""

from sqlalchemy import text

from app.cliente.cliente_model import Cliente
from app.equipamento.equipamento_model import Equipamento
from app.extensoes import db

from app.geradores.gerador_model import ClienteUnidade, Gerador


class GeradorDominioError(ValueError):
    """Erro de regra de negocio do modulo Geradores."""


CAMPOS_UNIDADE_CRIACAO = {
    "descricao",
    "cep",
    "endereco",
    "numero",
    "complemento",
    "bairro",
    "cidade",
    "estado",
    "contato_nome",
    "contato_telefone",
    "contato_email",
    "observacoes",
}


CAMPOS_GERADOR_CRIACAO = {
    "descricao",
    "fabricante_grupo",
    "modelo",
    "numero_serie",
    "ano",
    "fabricante_integrador",
    "local_instalado",
    "aplicacao",
    "regime_operacao",

    "potencia_standby_kva",
    "potencia_standby_kw",
    "potencia_prime_kva",
    "potencia_prime_kw",
    "tensao",
    "numero_fases",
    "frequencia_hz",
    "fator_potencia",
    "corrente_nominal_a",
    "rpm",
    "ligacao",
    "neutro",
    "sistema_aterramento",

    "disjuntor_descricao",
    "disjuntor_corrente_a",
    "disjuntor_capacidade_interrupcao_ka",
    "disjuntor_numero_polos",
    "protecao_diferencial",

    "status",
    "observacoes",
}


def _id_inteiro_positivo(valor, campo):
    try:
        valor_int = int(valor)
    except (TypeError, ValueError) as exc:
        raise GeradorDominioError(
            f"{campo} invalido."
        ) from exc

    if valor_int <= 0:
        raise GeradorDominioError(
            f"{campo} invalido."
        )

    return valor_int


def _validar_campos(dados, permitidos):
    desconhecidos = (
        set(dados.keys())
        - set(permitidos)
    )

    if desconhecidos:
        lista = ", ".join(
            sorted(desconhecidos)
        )

        raise GeradorDominioError(
            "Campos nao permitidos: "
            f"{lista}."
        )


def criar_unidade(cliente_id, nome, **dados):
    """Cria unidade operacional para um cliente ativo.

    O service adiciona e executa flush, mas nao realiza commit.
    A fronteira transacional pertence ao chamador.
    """

    cliente_id = _id_inteiro_positivo(
        cliente_id,
        "cliente_id",
    )

    _validar_campos(
        dados,
        CAMPOS_UNIDADE_CRIACAO,
    )

    _carregar_cliente_ativo(
        cliente_id,
    )

    if nome is None:
        raise GeradorDominioError(
            "Nome da unidade e obrigatorio."
        )

    nome = str(nome).strip()

    if not nome:
        raise GeradorDominioError(
            "Nome da unidade e obrigatorio."
        )

    unidade = ClienteUnidade(
        cliente_id=cliente_id,
        nome=nome,
        **dados,
    )

    db.session.add(unidade)
    db.session.flush()

    return unidade


def _carregar_cliente_ativo(cliente_id):
    cliente_id = _id_inteiro_positivo(
        cliente_id,
        "cliente_id",
    )

    cliente = db.session.get(
        Cliente,
        cliente_id,
    )

    if (
        cliente is None
        or not cliente.ativo
    ):
        raise GeradorDominioError(
            "Cliente nao encontrado "
            "ou inativo."
        )

    return cliente


def _carregar_unidade_do_cliente(
    unidade_id,
    cliente_id,
):
    if unidade_id in (
        None,
        "",
    ):
        return None

    unidade_id = _id_inteiro_positivo(
        unidade_id,
        "unidade_id",
    )

    unidade = db.session.get(
        ClienteUnidade,
        unidade_id,
    )

    if (
        unidade is None
        or not unidade.ativo
    ):
        raise GeradorDominioError(
            "Unidade nao encontrada "
            "ou inativa."
        )

    if unidade.cliente_id != cliente_id:
        raise GeradorDominioError(
            "A unidade informada nao pertence "
            "ao cliente do gerador."
        )

    return unidade


def _carregar_equipamento_para_vinculo(
    equipamento_id,
    cliente_id,
):
    if equipamento_id in (
        None,
        "",
    ):
        return None

    equipamento_id = _id_inteiro_positivo(
        equipamento_id,
        "equipamento_id",
    )

    # Lock no equipamento evita duas criacoes concorrentes
    # vincularem o mesmo equipamento a prontuarios distintos.
    equipamento = (
        Equipamento.query
        .filter(
            Equipamento.id == equipamento_id,
        )
        .with_for_update()
        .one_or_none()
    )

    if (
        equipamento is None
        or not equipamento.ativo
    ):
        raise GeradorDominioError(
            "Equipamento nao encontrado "
            "ou inativo."
        )

    if equipamento.cliente_id != cliente_id:
        raise GeradorDominioError(
            "O equipamento informado nao pertence "
            "ao cliente do gerador."
        )

    prontuario_existente = (
        Gerador.query
        .filter(
            Gerador.equipamento_id
            == equipamento_id,
        )
        .first()
    )

    if prontuario_existente is not None:
        raise GeradorDominioError(
            "Este equipamento ja possui "
            "prontuario de gerador: "
            f"{prontuario_existente.codigo}."
        )

    return equipamento


def _proximo_codigo_gerador():
    """
    Reserva numero no PostgreSQL.

    Sequence e concorrente e nao sofre MAX()+1.
    Valores consumidos em rollback podem gerar lacunas,
    mas nunca devem ser reutilizados.
    """

    numero = db.session.execute(
        text(
            "SELECT nextval("
            "'geradores_codigo_seq'"
            ")"
        )
    ).scalar_one()

    return f"GER-{int(numero):06d}"


def criar_unidade_cliente(
    *,
    cliente_id,
    nome,
    **dados,
):
    """
    Cria unidade operacional de um cliente.

    Nao executa commit.
    """

    cliente = _carregar_cliente_ativo(
        cliente_id
    )

    nome = str(
        nome or ""
    ).strip()

    if not nome:
        raise GeradorDominioError(
            "Nome da unidade e obrigatorio."
        )

    _validar_campos(
        dados,
        CAMPOS_UNIDADE_CRIACAO,
    )

    unidade = ClienteUnidade(
        cliente_id=cliente.id,
        nome=nome,
        **dados,
    )

    db.session.add(
        unidade
    )

    db.session.flush()

    return unidade


def criar_gerador(
    cliente_id,
    *,
    unidade_id=None,
    equipamento_id=None,
    **dados,
):
    """
    Cria o prontuario principal de um gerador.

    Nao executa commit.
    """

    cliente = _carregar_cliente_ativo(
        cliente_id
    )

    unidade = _carregar_unidade_do_cliente(
        unidade_id,
        cliente.id,
    )

    equipamento = (
        _carregar_equipamento_para_vinculo(
            equipamento_id,
            cliente.id,
        )
    )

    _validar_campos(
        dados,
        CAMPOS_GERADOR_CRIACAO,
    )

    status = dados.get(
        "status",
        Gerador.STATUS_ATIVO,
    )

    if status not in Gerador.STATUS_VALIDOS:
        raise GeradorDominioError(
            "Status de gerador invalido."
        )

    dados["status"] = status

    codigo = _proximo_codigo_gerador()

    gerador = Gerador(
        codigo=codigo,
        cliente_id=cliente.id,
        unidade_id=(
            unidade.id
            if unidade is not None
            else None
        ),
        equipamento_id=(
            equipamento.id
            if equipamento is not None
            else None
        ),
        **dados,
    )

    db.session.add(
        gerador
    )

    db.session.flush()

    return gerador
