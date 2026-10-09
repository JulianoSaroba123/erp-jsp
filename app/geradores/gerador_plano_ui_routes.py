import secrets
import hmac
from flask import session, abort
from flask import (
    Blueprint, render_template,
    request, redirect, url_for, flash,
)
from sqlalchemy.exc import SQLAlchemyError
from flask_login import login_required

from app.extensoes import db
from app.geradores.gerador_plano_model import PlanoManutencao
from app.geradores.gerador_plano_service import (
    criar_plano_manutencao,
    GeradorG3DominioError,
)

gerador_plano_ui_bp = Blueprint(
    "gerador_plano_ui",
    __name__,
    url_prefix="/geradores/planos",
)


def _csrf_token_g4():
    token = session.get("_csrf_geradores_g4")
    if not token:
        token = secrets.token_urlsafe(32)
        session["_csrf_geradores_g4"] = token
    return token


@gerador_plano_ui_bp.route("/", methods=["GET", "POST"])
@login_required
def listar_planos():
    if request.method == "POST":
        recebido = request.form.get("csrf_token_g4", "")
        esperado = session.get("_csrf_geradores_g4", "")

        if not esperado or not hmac.compare_digest(
            recebido, esperado
        ):
            abort(400, description="Token CSRF invalido.")

        try:
            criar_plano_manutencao(
                codigo=request.form.get("codigo"),
                nome=request.form.get("nome"),
                tipo=request.form.get("tipo"),
                intervalo_horas=(
                    request.form.get("intervalo_horas") or None
                ),
                intervalo_meses=(
                    request.form.get("intervalo_meses") or None
                ),
                plano_pai_id=(
                    request.form.get("plano_pai_id") or None
                ),
                descricao=request.form.get("descricao"),
                observacoes=request.form.get("observacoes"),
            )
            db.session.commit()
            flash("Plano cadastrado com sucesso.", "success")
            return redirect(
                url_for("gerador_plano_ui.listar_planos")
            )
        except GeradorG3DominioError as erro:
            db.session.rollback()
            flash(str(erro), "danger")
        except SQLAlchemyError:
            db.session.rollback()
            flash("Falha ao salvar plano.", "danger")

    planos = (
        PlanoManutencao.query
        .filter_by(ativo=True)
        .order_by(PlanoManutencao.nome.asc())
        .all()
    )

    return render_template(
        "geradores/planos.html",
        planos=planos,
        tipos=PlanoManutencao.TIPOS_VALIDOS,
        csrf_token_g4=_csrf_token_g4(),
    )


@gerador_plano_ui_bp.route("/vincular", methods=["GET", "POST"])
@login_required
def vincular_plano_g4():
    from datetime import date
    from app.geradores.gerador_model import Gerador
    from app.geradores.gerador_plano_model import (
        GeradorPlanoManutencao,
    )
    from app.geradores.gerador_plano_service import (
        vincular_plano_gerador,
    )

    if request.method == "POST":
        recebido = request.form.get("csrf_token_g4", "")
        esperado = session.get("_csrf_geradores_g4", "")

        if not esperado or not hmac.compare_digest(
            recebido, esperado
        ):
            abort(400, description="Token CSRF invalido.")

        try:
            data_texto = (
                request.form.get("data_base_programacao") or ""
            ).strip()

            data_base = (
                date.fromisoformat(data_texto)
                if data_texto else None
            )

            vincular_plano_gerador(
                gerador_id=request.form.get("gerador_id"),
                plano_id=request.form.get("plano_id"),
                data_base_programacao=data_base,
                horimetro_base_programacao=(
                    request.form.get(
                        "horimetro_base_programacao"
                    ) or None
                ),
                observacoes=request.form.get("observacoes"),
            )

            db.session.commit()
            flash("Plano vinculado com sucesso.", "success")
            return redirect(
                url_for("gerador_plano_ui.vincular_plano_g4")
            )

        except ValueError as erro:
            db.session.rollback()
            flash(str(erro), "danger")

        except SQLAlchemyError:
            db.session.rollback()
            flash("Erro ao salvar vinculo.", "danger")

    geradores = (
        Gerador.query
        .filter_by(ativo=True)
        .order_by(Gerador.id.asc())
        .all()
    )

    planos = (
        PlanoManutencao.query
        .filter_by(ativo=True)
        .order_by(PlanoManutencao.nome.asc())
        .all()
    )

    vinculos = (
        GeradorPlanoManutencao.query
        .filter_by(ativo=True)
        .order_by(GeradorPlanoManutencao.id.desc())
        .all()
    )

    return render_template(
        "geradores/vincular_plano.html",
        geradores=geradores,
        planos=planos,
        vinculos=vinculos,
        csrf_token_g4=_csrf_token_g4(),
    )



@gerador_plano_ui_bp.route("/horimetro", methods=["GET", "POST"])
@login_required
def horimetro_g4():
    from app.geradores.gerador_model import Gerador
    from app.geradores.gerador_horimetro_model import GeradorHorimetro
    from app.geradores.gerador_plano_service import registrar_horimetro

    geradores = (
        Gerador.query
        .filter_by(ativo=True)
        .order_by(Gerador.id.asc())
        .all()
    )

    identificador = (
        request.form.get("gerador_id")
        if request.method == "POST"
        else request.args.get("gerador_id")
    )

    gerador = next(
        (
            g for g in geradores
            if str(g.id) == str(identificador)
        ),
        None,
    )

    if request.method == "POST":
        recebido = request.form.get("csrf_token_g4", "")
        esperado = session.get("_csrf_geradores_g4", "")

        if not esperado or not hmac.compare_digest(
            recebido, esperado
        ):
            abort(400, description="Token CSRF invalido.")

        if gerador is None:
            abort(404)

        try:
            registrar_horimetro(
                gerador_id=gerador.id,
                leitura_atual=request.form.get("leitura_atual"),
                responsavel=request.form.get("responsavel"),
                observacoes=request.form.get("observacoes"),
            )

            db.session.commit()
            flash("Leitura registrada com sucesso.", "success")

            return redirect(
                url_for(
                    "gerador_plano_ui.horimetro_g4",
                    gerador_id=gerador.id,
                )
            )

        except ValueError as erro:
            db.session.rollback()
            flash(str(erro), "danger")

        except SQLAlchemyError:
            db.session.rollback()
            flash("Erro ao registrar horimetro.", "danger")

    leituras = []

    if gerador is not None:
        leituras = (
            GeradorHorimetro.query
            .filter_by(
                gerador_id=gerador.id,
                ativo=True,
            )
            .order_by(
                GeradorHorimetro.data_leitura.desc(),
                GeradorHorimetro.id.desc(),
            )
            .all()
        )

    return render_template(
        "geradores/horimetro.html",
        geradores=geradores,
        gerador=gerador,
        leituras=leituras,
        csrf_token_g4=_csrf_token_g4(),
    )


# G4 | Edicao controlada de planos
@gerador_plano_ui_bp.route(
    "/<int:plano_id>/editar",
    methods=["GET", "POST"]
)
@login_required
def editar_plano_g4(plano_id):
    from app.geradores.gerador_plano_model import (
        GeradorPlanoManutencao,
    )
    from app.geradores.gerador_plano_service import (
        _texto_obrigatorio,
        _decimal_opcional,
        _inteiro_opcional_positivo,
    )

    plano = PlanoManutencao.query.filter_by(
        id=plano_id,
        ativo=True,
    ).first_or_404()

    if request.method == "POST":
        _validar_csrf_edicao_g4()

        try:
            nome = _texto_obrigatorio(
                request.form.get("nome"), "nome"
            )

            if len(nome) > 150:
                raise GeradorG3DominioError(
                    "Nome excede 150 caracteres."
                )

            horas = _decimal_opcional(
                request.form.get("intervalo_horas") or None,
                "intervalo_horas",
                positivo=True,
            )

            meses = _inteiro_opcional_positivo(
                request.form.get("intervalo_meses") or None,
                "intervalo_meses",
            )

            if horas is None and meses is None:
                raise GeradorG3DominioError(
                    "Informe horas, meses ou ambos."
                )

            vinculos = (
                GeradorPlanoManutencao.query
                .filter_by(plano_id=plano.id, ativo=True)
                .all()
            )

            if horas is not None and any(
                v.horimetro_base_programacao is None
                for v in vinculos
            ):
                raise GeradorG3DominioError(
                    "Existe vinculo sem horimetro-base."
                )

            if meses is not None and any(
                v.data_base_programacao is None
                for v in vinculos
            ):
                raise GeradorG3DominioError(
                    "Existe vinculo sem data-base."
                )

            plano.nome = nome
            plano.intervalo_horas = horas
            plano.intervalo_meses = meses
            plano.descricao = (
                request.form.get("descricao") or None
            )
            plano.observacoes = (
                request.form.get("observacoes") or None
            )

            db.session.commit()

            flash(
                "Plano atualizado. Os geradores vinculados "
                "podem ser afetados.",
                "success",
            )

            return redirect(
                url_for("gerador_plano_ui.listar_planos")
            )

        except (ValueError, SQLAlchemyError) as erro:
            db.session.rollback()
            flash(
                str(erro)
                if isinstance(erro, ValueError)
                else "Falha ao editar plano.",
                "danger",
            )

    return render_template(
        "geradores/editar_manutencao.html",
        modo="plano",
        plano=plano,
        vinculo=None,
        csrf_token_g4=_csrf_token_g4(),
    )


def _validar_csrf_edicao_g4():
    import hmac
    from flask import abort, session

    token = request.form.get("csrf_token_g4", "")
    esperado = session.get("_csrf_geradores_g4", "")

    if not esperado or not hmac.compare_digest(
        token, esperado
    ):
        abort(400, description="Token CSRF invalido.")


# G4 | Edicao da programacao por gerador
@gerador_plano_ui_bp.route(
    "/vinculos/<int:vinculo_id>/editar",
    methods=["GET", "POST"]
)
@login_required
def editar_programacao_g4(vinculo_id):
    from datetime import date
    from decimal import Decimal
    from flask import abort
    from app.geradores.gerador_plano_model import (
        GeradorPlanoManutencao,
    )
    from app.geradores.gerador_plano_service import (
        _decimal_opcional,
        _ultimo_horimetro,
    )

    vinculo = GeradorPlanoManutencao.query.filter_by(
        id=vinculo_id,
        ativo=True,
    ).first_or_404()

    if not vinculo.plano.ativo or not vinculo.gerador.ativo:
        abort(404)

    if request.method == "POST":
        _validar_csrf_edicao_g4()

        try:
            texto_data = (
                request.form.get("data_base_programacao")
                or ""
            ).strip()

            data_base = (
                date.fromisoformat(texto_data)
                if texto_data else None
            )

            horas = _decimal_opcional(
                request.form.get(
                    "horimetro_base_programacao"
                ) or None,
                "horimetro_base_programacao",
            )

            if horas is not None and (
                not horas.is_finite() or horas < 0
            ):
                raise GeradorG3DominioError(
                    "Horimetro-base invalido."
                )

            if (
                vinculo.plano.intervalo_meses is not None
                and data_base is None
            ):
                raise GeradorG3DominioError(
                    "Plano por meses exige data-base."
                )

            if (
                vinculo.plano.intervalo_horas is not None
                and horas is None
            ):
                raise GeradorG3DominioError(
                    "Plano por horas exige horimetro-base."
                )

            ultimo = _ultimo_horimetro(
                vinculo.gerador_id
            )

            if (
                ultimo is not None
                and horas is not None
                and horas > Decimal(
                    str(ultimo.horas_acumuladas)
                )
            ):
                raise GeradorG3DominioError(
                    "Horimetro-base supera horas "
                    "acumuladas atuais."
                )

            vinculo.data_base_programacao = data_base
            vinculo.horimetro_base_programacao = horas
            vinculo.observacoes = (
                request.form.get("observacoes") or None
            )

            db.session.commit()

            flash(
                "Programacao atualizada.",
                "success",
            )

            return redirect(
                url_for(
                    "geradores.ficha",
                    gerador_id=vinculo.gerador_id,
                )
            )

        except (ValueError, SQLAlchemyError) as erro:
            db.session.rollback()
            flash(
                str(erro)
                if isinstance(erro, ValueError)
                else "Falha ao editar programacao.",
                "danger",
            )

    return render_template(
        "geradores/editar_manutencao.html",
        modo="programacao",
        vinculo=vinculo,
        plano=vinculo.plano,
        csrf_token_g4=_csrf_token_g4(),
    )



# G4-A9-RELATORIOS
@gerador_plano_ui_bp.route(
    "/relatorios/<int:gerador_id>",
    methods=["GET"],
)
@login_required
def relatorio_gerador_g4(gerador_id):
    from datetime import date, datetime
    from decimal import Decimal
    from flask import abort, request
    from sqlalchemy.inspection import inspect as sa_inspect

    from app.geradores import gerador_routes as modelos
    from app.geradores.gerador_plano_service import (
        calcular_programacao,
        GeradorG3DominioError,
    )

    opcoes = [
        ("geral", "Cadastro geral"),
        ("cliente", "Cliente"),
        ("unidade", "Unidade do cliente"),
        ("motor", "Motor"),
        ("alternador", "Alternador"),
        ("controladora", "Controladora"),
        ("qta", "QTA / ATS"),
        ("bateria", "Bateria"),
        ("carregador", "Carregador"),
        ("consumiveis", "Filtros e consumiveis"),
        ("equivalentes", "Equivalentes"),
        ("planos", "Planos e programacao"),
        ("horimetro", "Historico de horimetro"),
    ]

    selecionado = request.args.get(
        "secao", "todas"
    ).strip().lower()

    validos = {"todas"} | {
        codigo for codigo, _ in opcoes
    }

    if selecionado not in validos:
        abort(400, description="Secao invalida.")

    gerador = (
        modelos.Gerador.query
        .filter_by(id=gerador_id, ativo=True)
        .first_or_404()
    )

    def formatar(valor):
        if valor is None:
            return "-"
        if isinstance(valor, bool):
            return "Sim" if valor else "Nao"
        if isinstance(valor, datetime):
            return valor.strftime("%d/%m/%Y %H:%M:%S")
        if isinstance(valor, date):
            return valor.strftime("%d/%m/%Y")
        if isinstance(valor, Decimal):
            return format(valor, "f")
        if isinstance(valor, (bytes, bytearray)):
            return (
                f"Conteudo binario: {len(valor)} bytes"
            )
        return str(valor)

    def campos_objeto(objeto, prefixo=""):
        resultado = []

        mapper = sa_inspect(type(objeto))

        for atributo in mapper.column_attrs:
            nome = atributo.key
            valor = getattr(objeto, nome, None)

            rotulo = (
                prefixo
                + nome.replace("_", " ").capitalize()
            )

            resultado.append(
                (rotulo, formatar(valor))
            )

        return resultado

    def novo_registro(campos):
        return {"campos": campos}

    def adicionar(codigo, titulo, objetos):
        secao = {
            "codigo": codigo,
            "titulo": titulo,
            "registros": [
                novo_registro(campos_objeto(obj))
                for obj in objetos
            ],
            "aviso": None,
        }
        secoes.append(secao)

    def buscar_componentes(nome_modelo):
        classe = getattr(
            modelos, nome_modelo, None
        )

        if classe is None:
            return None

        return (
            classe.query
            .filter(classe.gerador_id == gerador.id)
            .order_by(classe.id.desc())
            .all()
        )

    def buscar_relacao(palavra, excluir=None):
        relacoes = sa_inspect(
            type(gerador)
        ).relationships

        for relacao in relacoes:
            nome = relacao.key.lower()

            if palavra not in nome or relacao.uselist:
                continue

            if excluir and excluir in nome:
                continue

            objeto = getattr(
                gerador, relacao.key, None
            )

            if objeto is not None:
                return [objeto]

        return []

    secoes = []

    mapa = {
        "motor": ("Motor", "GeradorMotor"),
        "alternador": (
            "Alternador", "GeradorAlternador"
        ),
        "controladora": (
            "Controladora", "GeradorControladora"
        ),
        "qta": ("QTA / ATS", "GeradorQTA"),
        "bateria": (
            "Bateria", "GeradorBateria"
        ),
        "carregador": (
            "Carregador", "GeradorCarregador"
        ),
        "consumiveis": (
            "Filtros e consumiveis",
            "GeradorConsumivel",
        ),
        "horimetro": (
            "Historico de horimetro",
            "GeradorHorimetro",
        ),
    }

    for codigo, titulo in opcoes:
        if selecionado not in ("todas", codigo):
            continue

        if codigo == "geral":
            adicionar(codigo, titulo, [gerador])

        elif codigo == "cliente":
            adicionar(
                codigo, titulo,
                buscar_relacao(
                    "cliente", excluir="unidade"
                ),
            )

        elif codigo == "unidade":
            adicionar(
                codigo, titulo,
                buscar_relacao("unidade"),
            )

        elif codigo in mapa:
            titulo_secao, classe = mapa[codigo]
            objetos = buscar_componentes(classe)

            if objetos is None:
                secoes.append({
                    "codigo": codigo,
                    "titulo": titulo_secao,
                    "registros": [],
                    "aviso": (
                        "Modelo nao localizado: " + classe
                    ),
                })
            else:
                adicionar(
                    codigo, titulo_secao, objetos
                )

        elif codigo == "equivalentes":
            consumiveis = buscar_componentes(
                "GeradorConsumivel"
            )
            classe = getattr(
                modelos,
                "GeradorConsumivelEquivalente",
                None,
            )

            if consumiveis is None or classe is None:
                secoes.append({
                    "codigo": codigo,
                    "titulo": titulo,
                    "registros": [],
                    "aviso": "Modelo nao localizado.",
                })
            else:
                ids = [item.id for item in consumiveis]

                objetos = (
                    classe.query
                    .filter(
                        classe.consumivel_id.in_(ids)
                    )
                    .order_by(classe.id.desc())
                    .all()
                    if ids else []
                )

                adicionar(codigo, titulo, objetos)

        elif codigo == "planos":
            classe = getattr(
                modelos,
                "GeradorPlanoManutencao",
                None,
            )

            if classe is None:
                secoes.append({
                    "codigo": codigo,
                    "titulo": titulo,
                    "registros": [],
                    "aviso": "Modelo de vinculo ausente.",
                })
                continue

            vinculos = (
                classe.query
                .filter_by(gerador_id=gerador.id)
                .order_by(classe.id.desc())
                .all()
            )

            registros = []

            for vinculo in vinculos:
                campos = campos_objeto(
                    vinculo, "Vinculo / "
                )

                if vinculo.plano is not None:
                    campos += campos_objeto(
                        vinculo.plano, "Plano / "
                    )

                if (
                    vinculo.ativo
                    and vinculo.plano is not None
                    and vinculo.plano.ativo
                ):
                    try:
                        programacao = calcular_programacao(
                            vinculo_id=vinculo.id
                        )
                    except GeradorG3DominioError as erro:
                        programacao = {
                            "situacao": str(erro)
                        }

                    if isinstance(programacao, dict):
                        for chave, valor in programacao.items():
                            campos.append((
                                "Programacao / "
                                + chave.replace("_", " "),
                                formatar(valor),
                            ))

                registros.append(novo_registro(campos))

            secoes.append({
                "codigo": codigo,
                "titulo": titulo,
                "registros": registros,
                "aviso": None,
            })

    return render_template(
        "geradores/relatorio_tecnico.html",
        gerador=gerador,
        opcoes=opcoes,
        secao_atual=selecionado,
        secoes=secoes,
        gerado_em=datetime.now(),
    )
