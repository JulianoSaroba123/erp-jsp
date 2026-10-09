# -*- coding: utf-8 -*-
"""Rotas iniciais do modulo GERADORES."""

from decimal import Decimal, InvalidOperation

from sqlalchemy.orm import selectinload

from flask import (
    Blueprint, current_app, flash, redirect,
    render_template, request, url_for,
)

from app.extensoes import db
from app.cliente.cliente_model import Cliente
from app.equipamento.equipamento_model import Equipamento
from app.geradores.gerador_model import ClienteUnidade, Gerador
from app.geradores.gerador_service import (
    GeradorDominioError,
    criar_gerador,
)
from app.geradores.gerador_horimetro_model import GeradorHorimetro
from app.geradores.gerador_componente_service import (
    GeradorG2DominioError,
    criar_motor,
    atualizar_motor,
    criar_alternador,
    atualizar_alternador,
    criar_controladora,
    atualizar_controladora,
    criar_qta,
    atualizar_qta,
    desativar_qta,
)

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

from app.geradores.gerador_plano_model import GeradorPlanoManutencao
from app.geradores.gerador_plano_service import calcular_programacao


geradores_bp = Blueprint(
    "geradores",
    __name__,
    template_folder="templates",
    url_prefix="/geradores",
)




def _texto_form(nome):
    """Retorna texto limpo do formulario ou None."""
    valor = request.form.get(nome)

    if valor is None:
        return None

    valor = str(valor).strip()

    return valor or None


def _inteiro_opcional(nome):
    """Converte campo inteiro opcional."""
    valor = _texto_form(nome)

    if valor is None:
        return None

    try:
        return int(valor)
    except (TypeError, ValueError) as exc:
        raise GeradorDominioError(
            f"Valor invalido para {nome}."
        ) from exc


def _decimal_opcional(nome):
    """Converte decimal opcional aceitando virgula brasileira."""
    valor = _texto_form(nome)

    if valor is None:
        return None

    valor = valor.replace(",", ".")

    try:
        return Decimal(valor)
    except (InvalidOperation, ValueError) as exc:
        raise GeradorDominioError(
            f"Valor invalido para {nome}."
        ) from exc


def _booleano_opcional(valor):
    if valor in (None, ""):
        return None

    if valor == "1":
        return True

    if valor == "0":
        return False

    raise ValueError("Valor booleano inv?lido.")


def _motor_para_form(motor):
    return {
        "fabricante": motor.fabricante or "",
        "modelo": motor.modelo or "",
        "variante": motor.variante or "",
        "numero_serie": motor.numero_serie or "",
        "quantidade_cilindros": motor.quantidade_cilindros or "",
        "cilindrada_l": motor.cilindrada_l or "",
        "aspiracao": motor.aspiracao or "",
        "turbo": (
            "1" if motor.turbo is True
            else "0" if motor.turbo is False
            else ""
        ),
        "intercooler": (
            "1" if motor.intercooler is True
            else "0" if motor.intercooler is False
            else ""
        ),
        "potencia": motor.potencia or "",
        "potencia_unidade": motor.potencia_unidade or "",
        "rpm": motor.rpm or "",
        "combustivel": motor.combustivel or "",
        "capacidade_oleo_l": motor.capacidade_oleo_l or "",
        "especificacao_oleo": motor.especificacao_oleo or "",
        "pressao_normal_oleo": motor.pressao_normal_oleo or "",
        "temperatura_normal": motor.temperatura_normal or "",
        "observacoes": motor.observacoes or "",
    }


def _dados_motor_form():
    return {
        "fabricante": _texto_form("fabricante"),
        "modelo": _texto_form("modelo"),
        "variante": _texto_form("variante"),
        "numero_serie": _texto_form("numero_serie"),
        "quantidade_cilindros": _inteiro_opcional("quantidade_cilindros"),
        "cilindrada_l": _decimal_opcional("cilindrada_l"),
        "aspiracao": _texto_form("aspiracao"),
        "turbo": _booleano_opcional(_texto_form("turbo")),
        "intercooler": _booleano_opcional(_texto_form("intercooler")),
        "potencia": _decimal_opcional("potencia"),
        "potencia_unidade": _texto_form("potencia_unidade"),
        "rpm": _inteiro_opcional("rpm"),
        "combustivel": _texto_form("combustivel"),
        "capacidade_oleo_l": _decimal_opcional("capacidade_oleo_l"),
        "especificacao_oleo": _texto_form("especificacao_oleo"),
        "pressao_normal_oleo": _texto_form("pressao_normal_oleo"),
        "temperatura_normal": _texto_form("temperatura_normal"),
        "observacoes": _texto_form("observacoes"),
    }


def _alternador_para_form(alternador):
    return {
        "fabricante": alternador.fabricante or "",
        "modelo": alternador.modelo or "",
        "numero_serie": alternador.numero_serie or "",
        "potencia_kva": "" if alternador.potencia_kva is None else alternador.potencia_kva,
        "tensao": alternador.tensao or "",
        "corrente_a": "" if alternador.corrente_a is None else alternador.corrente_a,
        "frequencia_hz": "" if alternador.frequencia_hz is None else alternador.frequencia_hz,
        "rpm": "" if alternador.rpm is None else alternador.rpm,
        "numero_polos": "" if alternador.numero_polos is None else alternador.numero_polos,
        "fator_potencia": "" if alternador.fator_potencia is None else alternador.fator_potencia,
        "classe_isolacao": alternador.classe_isolacao or "",
        "grau_protecao": alternador.grau_protecao or "",
        "sistema_excitacao": alternador.sistema_excitacao or "",
        "possui_avr": (
            "1" if alternador.possui_avr is True
            else "0" if alternador.possui_avr is False
            else ""
        ),
        "avr_fabricante": alternador.avr_fabricante or "",
        "avr_modelo": alternador.avr_modelo or "",
        "ligacao": alternador.ligacao or "",
        "observacoes": alternador.observacoes or "",
    }

def _dados_alternador_form():
    return {
        "fabricante": _texto_form("fabricante"),
        "modelo": _texto_form("modelo"),
        "numero_serie": _texto_form("numero_serie"),
        "potencia_kva": _texto_form("potencia_kva"),
        "tensao": _texto_form("tensao"),
        "corrente_a": _texto_form("corrente_a"),
        "frequencia_hz": _decimal_opcional("frequencia_hz"),
        "rpm": _inteiro_opcional("rpm"),
        "numero_polos": _inteiro_opcional("numero_polos"),
        "fator_potencia": _decimal_opcional("fator_potencia"),
        "classe_isolacao": _texto_form("classe_isolacao"),
        "grau_protecao": _texto_form("grau_protecao"),
        "sistema_excitacao": _texto_form("sistema_excitacao"),
        "possui_avr": _booleano_opcional(_texto_form("possui_avr")),
        "avr_fabricante": _texto_form("avr_fabricante"),
        "avr_modelo": _texto_form("avr_modelo"),
        "ligacao": _texto_form("ligacao"),
        "observacoes": _texto_form("observacoes"),
    }

def _contexto_form_gerador():
    """Dados auxiliares para o formulario de cadastro."""

    clientes = (
        Cliente.query
        .filter(Cliente.ativo.is_(True))
        .order_by(Cliente.nome.asc())
        .all()
    )

    unidades = (
        ClienteUnidade.query
        .filter(ClienteUnidade.ativo.is_(True))
        .order_by(
            ClienteUnidade.cliente_id.asc(),
            ClienteUnidade.nome.asc(),
        )
        .all()
    )

    equipamentos = (
        Equipamento.query
        .filter(Equipamento.ativo.is_(True))
        .order_by(
            Equipamento.cliente_id.asc(),
            Equipamento.nome.asc(),
        )
        .all()
    )

    return {
        "clientes": clientes,
        "unidades": unidades,
        "equipamentos": equipamentos,
        "status_validos": Gerador.STATUS_VALIDOS,
    }




def _dados_controladora_form():
    return {
        "fabricante": _texto_form("fabricante"),
        "modelo": _texto_form("modelo"),
        "versao": _texto_form("versao"),
        "firmware": _texto_form("firmware"),
        "tensao_alimentacao": _texto_form("tensao_alimentacao"),
        "comunicacao": _texto_form("comunicacao"),
        "configuracao_relevante": _texto_form("configuracao_relevante"),
        "manual_referencia": _texto_form("manual_referencia"),
        "observacoes": _texto_form("observacoes"),
    }


def _controladora_para_form(controladora):
    return {
        "fabricante": controladora.fabricante or "",
        "modelo": controladora.modelo or "",
        "versao": controladora.versao or "",
        "firmware": controladora.firmware or "",
        "tensao_alimentacao": controladora.tensao_alimentacao or "",
        "comunicacao": controladora.comunicacao or "",
        "configuracao_relevante": controladora.configuracao_relevante or "",
        "manual_referencia": controladora.manual_referencia or "",
        "observacoes": controladora.observacoes or "",
    }


def _dados_qta_form():
    return {
        "fabricante": _texto_form("fabricante"),
        "modelo": _texto_form("modelo"),
        "corrente_a": _decimal_opcional("corrente_a"),
        "numero_polos": _inteiro_opcional("numero_polos"),
        "tensao": _texto_form("tensao"),
        "transferencia": _texto_form("transferencia"),
        "tipo": _texto_form("tipo"),
        "controle": _texto_form("controle"),
        "intertravamento": _texto_form("intertravamento"),
        "posicao_normal": _texto_form("posicao_normal"),
        "observacoes": _texto_form("observacoes"),
    }


def _qta_para_form(qta):
    return {
        "fabricante": qta.fabricante or "",
        "modelo": qta.modelo or "",
        "corrente_a": "" if qta.corrente_a is None else qta.corrente_a,
        "numero_polos": "" if qta.numero_polos is None else qta.numero_polos,
        "tensao": qta.tensao or "",
        "transferencia": qta.transferencia or "",
        "tipo": qta.tipo or "",
        "controle": qta.controle or "",
        "intertravamento": qta.intertravamento or "",
        "posicao_normal": qta.posicao_normal or "",
        "observacoes": qta.observacoes or "",
    }


from app.geradores.gerador_partida_model import GeradorBateria, GeradorCarregador

from app.geradores.gerador_componente_service import (
    criar_bateria,
    atualizar_bateria,
    desativar_bateria,
    criar_carregador,
    atualizar_carregador,
    desativar_carregador,
)

from app.geradores.gerador_componente_service import (
    criar_consumivel,
    atualizar_consumivel,
    desativar_consumivel,
    criar_equivalente,
    atualizar_equivalente,
    desativar_equivalente,
)
def _data_opcional(nome):
    valor = _texto_form(nome)
    if not valor:
        return None
    return __import__("datetime").date.fromisoformat(valor)


def _dados_bateria_form():
    return {
        "quantidade": _inteiro_opcional("quantidade"),
        "tensao_nominal_v": _decimal_opcional("tensao_nominal_v"),
        "capacidade_ah": _decimal_opcional("capacidade_ah"),
        "fabricante": _texto_form("fabricante"),
        "modelo": _texto_form("modelo"),
        "data_instalacao": _data_opcional("data_instalacao"),
        "tensao_repouso_v": _decimal_opcional("tensao_repouso_v"),
        "tensao_partida_v": _decimal_opcional("tensao_partida_v"),
        "observacoes": _texto_form("observacoes"),
    }


def _bateria_para_form(x):
    return {
        "quantidade": "" if x.quantidade is None else x.quantidade,
        "tensao_nominal_v": "" if x.tensao_nominal_v is None else x.tensao_nominal_v,
        "capacidade_ah": "" if x.capacidade_ah is None else x.capacidade_ah,
        "fabricante": x.fabricante or "",
        "modelo": x.modelo or "",
        "data_instalacao": x.data_instalacao.isoformat() if x.data_instalacao else "",
        "tensao_repouso_v": "" if x.tensao_repouso_v is None else x.tensao_repouso_v,
        "tensao_partida_v": "" if x.tensao_partida_v is None else x.tensao_partida_v,
        "observacoes": x.observacoes or "",
    }


def _dados_carregador_form():
    return {
        "fabricante": _texto_form("fabricante"),
        "modelo": _texto_form("modelo"),
        "tensao_nominal_v": _texto_form("tensao_nominal_v"),
        "corrente_nominal_a": _decimal_opcional("corrente_nominal_a"),
        "tensao_medida_v": _decimal_opcional("tensao_medida_v"),
        "observacoes": _texto_form("observacoes"),
    }


def _carregador_para_form(x):
    return {
        "fabricante": x.fabricante or "",
        "modelo": x.modelo or "",
        "tensao_nominal_v": "" if x.tensao_nominal_v is None else x.tensao_nominal_v,
        "corrente_nominal_a": "" if x.corrente_nominal_a is None else x.corrente_nominal_a,
        "tensao_medida_v": "" if x.tensao_medida_v is None else x.tensao_medida_v,
        "observacoes": x.observacoes or "",
    }


@geradores_bp.route("/novo", methods=["GET", "POST"])
def novo():
    """Cadastro do prontuario principal de grupo gerador."""

    contexto = _contexto_form_gerador()

    if request.method == "POST":
        form_data = request.form.to_dict(flat=True)

        try:
            cliente_id = _inteiro_opcional("cliente_id")

            if cliente_id is None:
                raise GeradorDominioError(
                    "Cliente e obrigatorio."
                )

            gerador = criar_gerador(
                cliente_id,
                unidade_id=_inteiro_opcional("unidade_id"),
                equipamento_id=_inteiro_opcional("equipamento_id"),

                descricao=_texto_form("descricao"),
                fabricante_grupo=_texto_form("fabricante_grupo"),
                modelo=_texto_form("modelo"),
                numero_serie=_texto_form("numero_serie"),
                ano=_inteiro_opcional("ano"),
                fabricante_integrador=_texto_form("fabricante_integrador"),
                local_instalado=_texto_form("local_instalado"),
                aplicacao=_texto_form("aplicacao"),
                regime_operacao=_texto_form("regime_operacao"),

                potencia_standby_kva=_decimal_opcional("potencia_standby_kva"),
                potencia_standby_kw=_decimal_opcional("potencia_standby_kw"),
                potencia_prime_kva=_decimal_opcional("potencia_prime_kva"),
                potencia_prime_kw=_decimal_opcional("potencia_prime_kw"),
                tensao=_texto_form("tensao"),
                numero_fases=_texto_form("numero_fases"),
                frequencia_hz=_decimal_opcional("frequencia_hz"),
                fator_potencia=_decimal_opcional("fator_potencia"),
                corrente_nominal_a=_decimal_opcional("corrente_nominal_a"),
                rpm=_inteiro_opcional("rpm"),
                ligacao=_texto_form("ligacao"),
                neutro=_texto_form("neutro"),
                sistema_aterramento=_texto_form("sistema_aterramento"),

                disjuntor_descricao=_texto_form("disjuntor_descricao"),
                disjuntor_corrente_a=_decimal_opcional("disjuntor_corrente_a"),
                disjuntor_capacidade_interrupcao_ka=_decimal_opcional(
                    "disjuntor_capacidade_interrupcao_ka"
                ),
                disjuntor_numero_polos=_inteiro_opcional(
                    "disjuntor_numero_polos"
                ),
                protecao_diferencial=_texto_form("protecao_diferencial"),

                status=(
                    _texto_form("status")
                    or Gerador.STATUS_ATIVO
                ),
                observacoes=_texto_form("observacoes"),
            )

            db.session.commit()

            flash(
                f"Gerador {gerador.codigo} cadastrado com sucesso.",
                "success",
            )

            return redirect(
                url_for(
                    "geradores.ficha",
                    gerador_id=gerador.id,
                )
            )

        except GeradorDominioError as exc:
            db.session.rollback()

            flash(
                str(exc),
                "warning",
            )

            contexto["form_data"] = form_data

        except Exception:
            db.session.rollback()

            current_app.logger.exception(
                "Erro inesperado ao cadastrar gerador."
            )

            flash(
                "Nao foi possivel cadastrar o gerador.",
                "danger",
            )

            contexto["form_data"] = form_data

    else:
        contexto["form_data"] = {}

    return render_template(
        "geradores/form.html",
        **contexto,
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


def _ultimo_componente_ativo(modelo, gerador_id):
    return (
        modelo.query
        .filter_by(
            gerador_id=gerador_id,
            ativo=True,
        )
        .order_by(modelo.id.desc())
        .first()
    )


@geradores_bp.route("/<int:gerador_id>/ficha")
def ficha(gerador_id):
    """Ficha tecnica central do grupo gerador."""

    gerador = (
        Gerador.query
        .filter(
            Gerador.id == gerador_id,
            Gerador.ativo.is_(True),
        )
        .first_or_404()
    )

    consumiveis = (
        GeradorConsumivel.query
        .options(
            selectinload(GeradorConsumivel.produto)
        )
        .filter_by(
            gerador_id=gerador.id,
            ativo=True,
        )
        .order_by(
            GeradorConsumivel.tipo.asc(),
            GeradorConsumivel.id.desc(),
        )
        .all()
    )

    equivalentes_por_consumivel = {
        item.id: [] for item in consumiveis
    }

    if equivalentes_por_consumivel:
        equivalentes = (
            GeradorConsumivelEquivalente.query
            .filter(
                GeradorConsumivelEquivalente.consumivel_id.in_(
                    equivalentes_por_consumivel.keys()
                ),
                GeradorConsumivelEquivalente.ativo.is_(True),
            )
            .order_by(
                GeradorConsumivelEquivalente.consumivel_id.asc(),
                GeradorConsumivelEquivalente.id.asc(),
            )
            .all()
        )

        for equivalente in equivalentes:
            equivalentes_por_consumivel[
                equivalente.consumivel_id
            ].append(equivalente)

    vinculos_plano = (
        GeradorPlanoManutencao.query
        .filter_by(
            gerador_id=gerador.id,
            ativo=True,
        )
        .order_by(GeradorPlanoManutencao.id.desc())
        .all()
    )

    planos_programados = [
        {
            "vinculo": vinculo,
            "programacao": calcular_programacao(
                vinculo_id=vinculo.id
            ),
        }
        for vinculo in vinculos_plano
    ]

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

    return render_template(
        "geradores/ficha.html",
        gerador=gerador,
        motor=_ultimo_componente_ativo(
            GeradorMotor, gerador.id
        ),
        alternador=_ultimo_componente_ativo(
            GeradorAlternador, gerador.id
        ),
        controladora=_ultimo_componente_ativo(
            GeradorControladora, gerador.id
        ),
        qta=_ultimo_componente_ativo(
            GeradorQTA, gerador.id
        ),
        bateria=_ultimo_componente_ativo(
            GeradorBateria, gerador.id
        ),
        carregador=_ultimo_componente_ativo(
            GeradorCarregador, gerador.id
        ),
        consumiveis=consumiveis,
        equivalentes_por_consumivel=equivalentes_por_consumivel,
        planos_programados=planos_programados,
        ultimo_horimetro=ultimo_horimetro,
    )


@geradores_bp.route(
    "/<int:gerador_id>/motor/novo",
    methods=["GET", "POST"],
)
def novo_motor(gerador_id):
    gerador = (
        Gerador.query
        .filter(
            Gerador.id == gerador_id,
            Gerador.ativo.is_(True),
        )
        .first_or_404()
    )

    motor_existente = (
        GeradorMotor.query
        .filter_by(
            gerador_id=gerador.id,
            ativo=True,
        )
        .order_by(GeradorMotor.id.desc())
        .first()
    )

    if motor_existente is not None:
        flash(
            "Este gerador j? possui um motor ativo cadastrado.",
            "warning",
        )
        return redirect(
            url_for(
                "geradores.ficha",
                gerador_id=gerador.id,
            ) + "#motor"
        )

    form_data = {}

    if request.method == "POST":
        form_data = request.form.to_dict(flat=True)

        try:
            criar_motor(
                gerador_id=gerador.id,
                **_dados_motor_form(),
            )
            db.session.commit()

        except (
            GeradorDominioError,
            GeradorG2DominioError,
            ValueError,
        ) as exc:
            db.session.rollback()
            flash(str(exc), "danger")

        except Exception:
            db.session.rollback()
            raise

        else:
            flash(
                "Motor cadastrado com sucesso.",
                "success",
            )
            return redirect(
                url_for(
                    "geradores.ficha",
                    gerador_id=gerador.id,
                ) + "#motor"
            )

    return render_template(
        "geradores/motor_form.html",
        gerador=gerador,
        form_data=form_data,
    )


@geradores_bp.route(
    "/<int:gerador_id>/motor/<int:motor_id>/editar",
    methods=["GET", "POST"],
)
def editar_motor(gerador_id, motor_id):
    gerador = (
        Gerador.query
        .filter(
            Gerador.id == gerador_id,
            Gerador.ativo.is_(True),
        )
        .first_or_404()
    )

    motor = (
        GeradorMotor.query
        .filter_by(
            id=motor_id,
            gerador_id=gerador.id,
            ativo=True,
        )
        .first_or_404()
    )

    form_data = _motor_para_form(motor)

    if request.method == "POST":
        form_data = request.form.to_dict(flat=True)

        try:
            atualizar_motor(
                motor_id=motor.id,
                gerador_id=gerador.id,
                **_dados_motor_form(),
            )
            db.session.commit()

        except (
            GeradorDominioError,
            GeradorG2DominioError,
            ValueError,
        ) as exc:
            db.session.rollback()
            flash(str(exc), "danger")

        except Exception:
            db.session.rollback()
            raise

        else:
            flash(
                "Motor atualizado com sucesso.",
                "success",
            )
            return redirect(
                url_for(
                    "geradores.ficha",
                    gerador_id=gerador.id,
                ) + "#motor"
            )

    return render_template(
        "geradores/motor_form.html",
        gerador=gerador,
        form_data=form_data,
    )

@geradores_bp.route(
    "/<int:gerador_id>/alternador/novo",
    methods=["GET", "POST"],
)
def novo_alternador(gerador_id):
    gerador = (
        Gerador.query
        .filter(
            Gerador.id == gerador_id,
            Gerador.ativo.is_(True),
        )
        .first_or_404()
    )

    alternador_existente = (
        GeradorAlternador.query
        .filter_by(
            gerador_id=gerador.id,
            ativo=True,
        )
        .order_by(GeradorAlternador.id.desc())
        .first()
    )

    if alternador_existente is not None:
        flash(
            "Este gerador ja possui um alternador ativo cadastrado.",
            "warning",
        )
        return redirect(
            url_for(
                "geradores.ficha",
                gerador_id=gerador.id,
            ) + "#alternador"
        )

    form_data = {}

    if request.method == "POST":
        form_data = request.form.to_dict(flat=True)

        try:
            criar_alternador(
                gerador_id=gerador.id,
                **_dados_alternador_form(),
            )
            db.session.commit()

        except (
            GeradorDominioError,
            GeradorG2DominioError,
            ValueError,
        ) as exc:
            db.session.rollback()
            flash(str(exc), "danger")

        except Exception:
            db.session.rollback()
            raise

        else:
            flash(
                "Alternador cadastrado com sucesso.",
                "success",
            )
            return redirect(
                url_for(
                    "geradores.ficha",
                    gerador_id=gerador.id,
                ) + "#alternador"
            )

    return render_template(
        "geradores/alternador_form.html",
        gerador=gerador,
        form_data=form_data,
    )

@geradores_bp.route(
    "/<int:gerador_id>/alternador/<int:alternador_id>/editar",
    methods=["GET", "POST"],
)
def editar_alternador(gerador_id, alternador_id):
    gerador = (
        Gerador.query
        .filter(
            Gerador.id == gerador_id,
            Gerador.ativo.is_(True),
        )
        .first_or_404()
    )

    alternador = (
        GeradorAlternador.query
        .filter_by(
            id=alternador_id,
            gerador_id=gerador.id,
            ativo=True,
        )
        .first_or_404()
    )

    form_data = _alternador_para_form(alternador)

    if request.method == "POST":
        form_data = request.form.to_dict(flat=True)

        try:
            atualizar_alternador(
                alternador_id=alternador.id,
                gerador_id=gerador.id,
                **_dados_alternador_form(),
            )
            db.session.commit()

        except (
            GeradorDominioError,
            GeradorG2DominioError,
            ValueError,
        ) as exc:
            db.session.rollback()
            flash(str(exc), "danger")

        except Exception:
            db.session.rollback()
            raise

        else:
            flash(
                "Alternador atualizado com sucesso.",
                "success",
            )
            return redirect(
                url_for(
                    "geradores.ficha",
                    gerador_id=gerador.id,
                ) + "#alternador"
            )

    return render_template(
        "geradores/alternador_form.html",
        gerador=gerador,
        form_data=form_data,
    )

@geradores_bp.route(
    "/<int:gerador_id>/controladora/novo",
    methods=["GET", "POST"],
)
def nova_controladora(gerador_id):
    gerador = (
        Gerador.query
        .filter(
            Gerador.id == gerador_id,
            Gerador.ativo.is_(True),
        )
        .first_or_404()
    )

    existente = (
        GeradorControladora.query
        .filter_by(
            gerador_id=gerador.id,
            ativo=True,
        )
        .order_by(GeradorControladora.id.desc())
        .first()
    )

    if existente:
        flash(
            "Este gerador ja possui uma controladora ativa cadastrada.",
            "warning",
        )
        return redirect(
            url_for(
                "geradores.ficha",
                gerador_id=gerador.id,
            ) + "#controladora"
        )

    form_data = {}

    if request.method == "POST":
        form_data = request.form.to_dict(flat=True)

        try:
            criar_controladora(
                gerador_id=gerador.id,
                **_dados_controladora_form(),
            )
            db.session.commit()

        except (
            GeradorDominioError,
            GeradorG2DominioError,
            ValueError,
        ) as exc:
            db.session.rollback()
            flash(str(exc), "danger")

        except Exception:
            db.session.rollback()
            raise

        else:
            flash(
                "Controladora cadastrada com sucesso.",
                "success",
            )
            return redirect(
                url_for(
                    "geradores.ficha",
                    gerador_id=gerador.id,
                ) + "#controladora"
            )

    return render_template(
        "geradores/controladora_form.html",
        gerador=gerador,
        form_data=form_data,
    )


@geradores_bp.route(
    "/<int:gerador_id>/controladora/<int:controladora_id>/editar",
    methods=["GET", "POST"],
)
def editar_controladora(gerador_id, controladora_id):
    gerador = (
        Gerador.query
        .filter(
            Gerador.id == gerador_id,
            Gerador.ativo.is_(True),
        )
        .first_or_404()
    )

    controladora = (
        GeradorControladora.query
        .filter_by(
            id=controladora_id,
            gerador_id=gerador.id,
            ativo=True,
        )
        .first_or_404()
    )

    form_data = _controladora_para_form(controladora)

    if request.method == "POST":
        form_data = request.form.to_dict(flat=True)

        try:
            atualizar_controladora(
                controladora_id=controladora.id,
                gerador_id=gerador.id,
                **_dados_controladora_form(),
            )
            db.session.commit()

        except (
            GeradorDominioError,
            GeradorG2DominioError,
            ValueError,
        ) as exc:
            db.session.rollback()
            flash(str(exc), "danger")

        except Exception:
            db.session.rollback()
            raise

        else:
            flash(
                "Controladora atualizada com sucesso.",
                "success",
            )
            return redirect(
                url_for(
                    "geradores.ficha",
                    gerador_id=gerador.id,
                ) + "#controladora"
            )

    return render_template(
        "geradores/controladora_form.html",
        gerador=gerador,
        form_data=form_data,
    )

@geradores_bp.route(
    "/<int:gerador_id>/qta/novo",
    methods=["GET", "POST"],
)
def novo_qta(gerador_id):
    gerador = (
        Gerador.query
        .filter(
            Gerador.id == gerador_id,
            Gerador.ativo.is_(True),
        )
        .first_or_404()
    )

    existente = (
        GeradorQTA.query
        .filter_by(
            gerador_id=gerador.id,
            ativo=True,
        )
        .order_by(GeradorQTA.id.desc())
        .first()
    )

    if existente:
        flash(
            "Este gerador ja possui um QTA/ATS ativo cadastrado.",
            "warning",
        )
        return redirect(
            url_for(
                "geradores.ficha",
                gerador_id=gerador.id,
            ) + "#qta"
        )

    form_data = {}

    if request.method == "POST":
        form_data = request.form.to_dict(flat=True)

        try:
            criar_qta(
                gerador_id=gerador.id,
                **_dados_qta_form(),
            )
            db.session.commit()

        except (
            GeradorDominioError,
            GeradorG2DominioError,
            ValueError,
        ) as exc:
            db.session.rollback()
            flash(str(exc), "danger")

        except Exception:
            db.session.rollback()
            raise

        else:
            flash(
                "QTA/ATS cadastrado com sucesso.",
                "success",
            )
            return redirect(
                url_for(
                    "geradores.ficha",
                    gerador_id=gerador.id,
                ) + "#qta"
            )

    return render_template(
        "geradores/qta_form.html",
        gerador=gerador,
        form_data=form_data,
    )


@geradores_bp.route(
    "/<int:gerador_id>/qta/<int:qta_id>/editar",
    methods=["GET", "POST"],
)
def editar_qta(gerador_id, qta_id):
    gerador = (
        Gerador.query
        .filter(
            Gerador.id == gerador_id,
            Gerador.ativo.is_(True),
        )
        .first_or_404()
    )

    qta = (
        GeradorQTA.query
        .filter_by(
            id=qta_id,
            gerador_id=gerador.id,
            ativo=True,
        )
        .first_or_404()
    )

    form_data = _qta_para_form(qta)

    if request.method == "POST":
        form_data = request.form.to_dict(flat=True)

        try:
            atualizar_qta(
                qta_id=qta.id,
                gerador_id=gerador.id,
                **_dados_qta_form(),
            )
            db.session.commit()

        except (
            GeradorDominioError,
            GeradorG2DominioError,
            ValueError,
        ) as exc:
            db.session.rollback()
            flash(str(exc), "danger")

        except Exception:
            db.session.rollback()
            raise

        else:
            flash(
                "QTA/ATS atualizado com sucesso.",
                "success",
            )
            return redirect(
                url_for(
                    "geradores.ficha",
                    gerador_id=gerador.id,
                ) + "#qta"
            )

    return render_template(
        "geradores/qta_form.html",
        gerador=gerador,
        form_data=form_data,
    )

@geradores_bp.route(
    "/<int:gerador_id>/qta/<int:qta_id>/excluir",
    methods=["POST"],
)
def excluir_qta(gerador_id, qta_id):
    try:
        desativar_qta(
            qta_id=qta_id,
            gerador_id=gerador_id,
        )
        db.session.commit()

    except (
        GeradorDominioError,
        GeradorG2DominioError,
        ValueError,
    ) as exc:
        db.session.rollback()
        flash(str(exc), "danger")

    except Exception:
        db.session.rollback()
        raise

    else:
        flash(
            "QTA/ATS desativado com sucesso.",
            "success",
        )

    return redirect(
        url_for(
            "geradores.ficha",
            gerador_id=gerador_id,
        ) + "#qta"
    )



@geradores_bp.route(
    "/<int:gerador_id>/bateria/novo",
    methods=["GET", "POST"],
)
def nova_bateria(gerador_id):
    gerador = Gerador.query.filter(
        Gerador.id == gerador_id,
        Gerador.ativo.is_(True),
    ).first_or_404()

    existente = GeradorBateria.query.filter_by(
        gerador_id=gerador.id,
        ativo=True,
    ).first()

    if existente:
        flash("Este gerador ja possui bateria ativa.", "warning")
        return redirect(
            url_for("geradores.ficha", gerador_id=gerador.id)
            + "#partida"
        )

    form_data = {}

    if request.method == "POST":
        form_data = request.form.to_dict(flat=True)

        try:
            criar_bateria(
                gerador_id=gerador.id,
                **_dados_bateria_form(),
            )
            db.session.commit()
        except (
            GeradorDominioError,
            GeradorG2DominioError,
            ValueError,
        ) as exc:
            db.session.rollback()
            flash(str(exc), "danger")
        except Exception:
            db.session.rollback()
            raise
        else:
            flash("Bateria cadastrada com sucesso.", "success")
            return redirect(
                url_for("geradores.ficha", gerador_id=gerador.id)
                + "#partida"
            )

    return render_template(
        "geradores/bateria_form.html",
        gerador=gerador,
        form_data=form_data,
    )


@geradores_bp.route(
    "/<int:gerador_id>/bateria/<int:bateria_id>/editar",
    methods=["GET", "POST"],
)
def editar_bateria(gerador_id, bateria_id):
    gerador = Gerador.query.filter(
        Gerador.id == gerador_id,
        Gerador.ativo.is_(True),
    ).first_or_404()

    bateria = GeradorBateria.query.filter_by(
        id=bateria_id,
        gerador_id=gerador.id,
        ativo=True,
    ).first_or_404()

    form_data = _bateria_para_form(bateria)

    if request.method == "POST":
        form_data = request.form.to_dict(flat=True)

        try:
            atualizar_bateria(
                bateria_id=bateria.id,
                gerador_id=gerador.id,
                **_dados_bateria_form(),
            )
            db.session.commit()
        except (
            GeradorDominioError,
            GeradorG2DominioError,
            ValueError,
        ) as exc:
            db.session.rollback()
            flash(str(exc), "danger")
        except Exception:
            db.session.rollback()
            raise
        else:
            flash("Bateria atualizada com sucesso.", "success")
            return redirect(
                url_for("geradores.ficha", gerador_id=gerador.id)
                + "#partida"
            )

    return render_template(
        "geradores/bateria_form.html",
        gerador=gerador,
        form_data=form_data,
    )


@geradores_bp.route(
    "/<int:gerador_id>/bateria/<int:bateria_id>/excluir",
    methods=["POST"],
)
def excluir_bateria(gerador_id, bateria_id):
    try:
        desativar_bateria(
            bateria_id=bateria_id,
            gerador_id=gerador_id,
        )
        db.session.commit()
        flash("Bateria desativada com sucesso.", "success")
    except Exception:
        db.session.rollback()
        raise

    return redirect(
        url_for("geradores.ficha", gerador_id=gerador_id)
        + "#partida"
    )


@geradores_bp.route(
    "/<int:gerador_id>/carregador/novo",
    methods=["GET", "POST"],
)
def novo_carregador(gerador_id):
    gerador = Gerador.query.filter(
        Gerador.id == gerador_id,
        Gerador.ativo.is_(True),
    ).first_or_404()

    existente = GeradorCarregador.query.filter_by(
        gerador_id=gerador.id,
        ativo=True,
    ).first()

    if existente:
        flash("Este gerador ja possui carregador ativo.", "warning")
        return redirect(
            url_for("geradores.ficha", gerador_id=gerador.id)
            + "#partida"
        )

    form_data = {}

    if request.method == "POST":
        form_data = request.form.to_dict(flat=True)

        try:
            criar_carregador(
                gerador_id=gerador.id,
                **_dados_carregador_form(),
            )
            db.session.commit()
        except (
            GeradorDominioError,
            GeradorG2DominioError,
            ValueError,
        ) as exc:
            db.session.rollback()
            flash(str(exc), "danger")
        except Exception:
            db.session.rollback()
            raise
        else:
            flash("Carregador cadastrado com sucesso.", "success")
            return redirect(
                url_for("geradores.ficha", gerador_id=gerador.id)
                + "#partida"
            )

    return render_template(
        "geradores/carregador_form.html",
        gerador=gerador,
        form_data=form_data,
    )


@geradores_bp.route(
    "/<int:gerador_id>/carregador/<int:carregador_id>/editar",
    methods=["GET", "POST"],
)
def editar_carregador(gerador_id, carregador_id):
    gerador = Gerador.query.filter(
        Gerador.id == gerador_id,
        Gerador.ativo.is_(True),
    ).first_or_404()

    carregador = GeradorCarregador.query.filter_by(
        id=carregador_id,
        gerador_id=gerador.id,
        ativo=True,
    ).first_or_404()

    form_data = _carregador_para_form(carregador)

    if request.method == "POST":
        form_data = request.form.to_dict(flat=True)

        try:
            atualizar_carregador(
                carregador_id=carregador.id,
                gerador_id=gerador.id,
                **_dados_carregador_form(),
            )
            db.session.commit()
        except (
            GeradorDominioError,
            GeradorG2DominioError,
            ValueError,
        ) as exc:
            db.session.rollback()
            flash(str(exc), "danger")
        except Exception:
            db.session.rollback()
            raise
        else:
            flash("Carregador atualizado com sucesso.", "success")
            return redirect(
                url_for("geradores.ficha", gerador_id=gerador.id)
                + "#partida"
            )

    return render_template(
        "geradores/carregador_form.html",
        gerador=gerador,
        form_data=form_data,
    )


@geradores_bp.route(
    "/<int:gerador_id>/carregador/<int:carregador_id>/excluir",
    methods=["POST"],
)
def excluir_carregador(gerador_id, carregador_id):
    try:
        desativar_carregador(
            carregador_id=carregador_id,
            gerador_id=gerador_id,
        )
        db.session.commit()
        flash("Carregador desativado com sucesso.", "success")
    except Exception:
        db.session.rollback()
        raise

    return redirect(
        url_for("geradores.ficha", gerador_id=gerador_id)
        + "#partida"
    )


def _dados_consumivel_form():
    return {
        "fabricante_original": _texto_form("fabricante_original"),
        "referencia_original": _texto_form("referencia_original"),
        "descricao": _texto_form("descricao"),
        "quantidade": _decimal_opcional("quantidade"),
        "unidade": _texto_form("unidade"),
        "observacoes": _texto_form("observacoes"),
    }


def _consumivel_para_form(item):
    return {
        "tipo": item.tipo or "",
        "fabricante_original": item.fabricante_original or "",
        "referencia_original": item.referencia_original or "",
        "descricao": item.descricao or "",
        "quantidade": "" if item.quantidade is None else item.quantidade,
        "unidade": item.unidade or "",
        "observacoes": item.observacoes or "",
    }


@geradores_bp.route(
    "/<int:gerador_id>/consumivel/novo",
    methods=["GET", "POST"],
)
def novo_consumivel(gerador_id):
    gerador = Gerador.query.filter(
        Gerador.id == gerador_id,
        Gerador.ativo.is_(True),
    ).first_or_404()

    form_data = {}

    if request.method == "POST":
        form_data = request.form.to_dict(flat=True)

        try:
            criar_consumivel(
                gerador_id=gerador.id,
                tipo=_texto_form("tipo"),
                produto_id=None,
                **_dados_consumivel_form(),
            )
            db.session.commit()
            flash("Consumivel cadastrado com sucesso.", "success")

            return redirect(
                url_for("geradores.ficha", gerador_id=gerador.id)
                + "#consumiveis"
            )

        except (
            GeradorDominioError,
            GeradorG2DominioError,
            ValueError,
        ) as exc:
            db.session.rollback()
            flash(str(exc), "danger")

    return render_template(
        "geradores/consumivel_form.html",
        gerador=gerador,
        form_data=form_data,
        tipos=GeradorConsumivel.TIPOS_VALIDOS,
        modo="novo",
    )


@geradores_bp.route(
    "/<int:gerador_id>/consumivel/<int:consumivel_id>/editar",
    methods=["GET", "POST"],
)
def editar_consumivel(gerador_id, consumivel_id):
    gerador = Gerador.query.filter(
        Gerador.id == gerador_id,
        Gerador.ativo.is_(True),
    ).first_or_404()

    consumivel = GeradorConsumivel.query.filter_by(
        id=consumivel_id,
        gerador_id=gerador.id,
        ativo=True,
    ).first_or_404()

    form_data = _consumivel_para_form(consumivel)

    if request.method == "POST":
        form_data = request.form.to_dict(flat=True)

        try:
            atualizar_consumivel(
                consumivel_id=consumivel.id,
                gerador_id=gerador.id,
                tipo=_texto_form("tipo"),
                **_dados_consumivel_form(),
            )
            db.session.commit()
            flash("Consumivel atualizado com sucesso.", "success")

            return redirect(
                url_for("geradores.ficha", gerador_id=gerador.id)
                + "#consumiveis"
            )

        except (
            GeradorDominioError,
            GeradorG2DominioError,
            ValueError,
        ) as exc:
            db.session.rollback()
            flash(str(exc), "danger")

    return render_template(
        "geradores/consumivel_form.html",
        gerador=gerador,
        consumivel=consumivel,
        form_data=form_data,
        tipos=GeradorConsumivel.TIPOS_VALIDOS,
        modo="editar",
    )


@geradores_bp.route(
    "/<int:gerador_id>/consumivel/<int:consumivel_id>/excluir",
    methods=["POST"],
)
def excluir_consumivel(gerador_id, consumivel_id):
    try:
        desativar_consumivel(
            consumivel_id=consumivel_id,
            gerador_id=gerador_id,
        )
        db.session.commit()
        flash("Consumivel desativado com sucesso.", "success")

    except (
        GeradorDominioError,
        GeradorG2DominioError,
        ValueError,
    ) as exc:
        db.session.rollback()
        flash(str(exc), "danger")

    return redirect(
        url_for("geradores.ficha", gerador_id=gerador_id)
        + "#consumiveis"
    )

def _dados_equivalente_form():
    return {
        "fabricante": _texto_form("fabricante"),
        "descricao": _texto_form("descricao"),
        "observacoes": _texto_form("observacoes"),
    }


def _equivalente_para_form(item):
    return {
        "fabricante": item.fabricante or "",
        "referencia": item.referencia or "",
        "descricao": item.descricao or "",
        "observacoes": item.observacoes or "",
    }


@geradores_bp.route(
    "/<int:gerador_id>/consumivel/<int:consumivel_id>/equivalente/novo",
    methods=["GET", "POST"],
)
def novo_equivalente(gerador_id, consumivel_id):
    gerador = Gerador.query.filter(
        Gerador.id == gerador_id,
        Gerador.ativo.is_(True),
    ).first_or_404()

    consumivel = GeradorConsumivel.query.filter_by(
        id=consumivel_id,
        gerador_id=gerador.id,
        ativo=True,
    ).first_or_404()

    form_data = {}

    if request.method == "POST":
        form_data = request.form.to_dict(flat=True)

        try:
            criar_equivalente(
                consumivel_id=consumivel.id,
                referencia=_texto_form("referencia"),
                **_dados_equivalente_form(),
            )
            db.session.commit()
            flash("Equivalente cadastrado com sucesso.", "success")

            return redirect(
                url_for("geradores.ficha", gerador_id=gerador.id)
                + "#consumiveis"
            )

        except (
            GeradorDominioError,
            GeradorG2DominioError,
            ValueError,
        ) as exc:
            db.session.rollback()
            flash(str(exc), "danger")

    return render_template(
        "geradores/equivalente_form.html",
        gerador=gerador,
        consumivel=consumivel,
        form_data=form_data,
        modo="novo",
    )


@geradores_bp.route(
    "/<int:gerador_id>/consumivel/<int:consumivel_id>/equivalente/<int:equivalente_id>/editar",
    methods=["GET", "POST"],
)
def editar_equivalente(
    gerador_id,
    consumivel_id,
    equivalente_id,
):
    gerador = Gerador.query.filter(
        Gerador.id == gerador_id,
        Gerador.ativo.is_(True),
    ).first_or_404()

    consumivel = GeradorConsumivel.query.filter_by(
        id=consumivel_id,
        gerador_id=gerador.id,
        ativo=True,
    ).first_or_404()

    equivalente = GeradorConsumivelEquivalente.query.filter_by(
        id=equivalente_id,
        consumivel_id=consumivel.id,
        ativo=True,
    ).first_or_404()

    form_data = _equivalente_para_form(equivalente)

    if request.method == "POST":
        form_data = request.form.to_dict(flat=True)

        try:
            atualizar_equivalente(
                equivalente_id=equivalente.id,
                consumivel_id=consumivel.id,
                referencia=_texto_form("referencia"),
                **_dados_equivalente_form(),
            )
            db.session.commit()
            flash("Equivalente atualizado com sucesso.", "success")

            return redirect(
                url_for("geradores.ficha", gerador_id=gerador.id)
                + "#consumiveis"
            )

        except (
            GeradorDominioError,
            GeradorG2DominioError,
            ValueError,
        ) as exc:
            db.session.rollback()
            flash(str(exc), "danger")

    return render_template(
        "geradores/equivalente_form.html",
        gerador=gerador,
        consumivel=consumivel,
        equivalente=equivalente,
        form_data=form_data,
        modo="editar",
    )


@geradores_bp.route(
    "/<int:gerador_id>/consumivel/<int:consumivel_id>/equivalente/<int:equivalente_id>/excluir",
    methods=["POST"],
)
def excluir_equivalente(
    gerador_id,
    consumivel_id,
    equivalente_id,
):
    try:
        desativar_equivalente(
            equivalente_id=equivalente_id,
            consumivel_id=consumivel_id,
        )
        db.session.commit()
        flash("Equivalente desativado com sucesso.", "success")

    except (
        GeradorDominioError,
        GeradorG2DominioError,
        ValueError,
    ) as exc:
        db.session.rollback()
        flash(str(exc), "danger")

    return redirect(
        url_for("geradores.ficha", gerador_id=gerador_id)
        + "#consumiveis"
    )