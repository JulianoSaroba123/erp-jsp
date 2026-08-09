# -*- coding: utf-8 -*-

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from functools import wraps

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from sqlalchemy.orm import joinedload

from app.extensoes import db
from app.fornecedor.fornecedor_model import Fornecedor
from app.ordem_servico.ordem_servico_model import OrdemServico
from app.pedido.pedido_model import Pedido
from app.pedido_compra.forms import (
    extrair_itens_form,
    normalizar_finalidade,
    normalizar_status,
    parse_decimal_br,
    parse_int,
    validar_payload_pedido_compra,
)
from app.pedido_compra.pedido_compra_financeiro_service import sincronizar_obrigacao_financeira_pedido_compra
from app.pedido_compra.pedido_compra_model import PedidoCompra, PedidoCompraItem
from app.produto.produto_model import Produto
from app.servico.servico_model import Servico

pedido_compra_bp = Blueprint("pedido_compra", __name__, template_folder="templates")


def _status_recebimento(status):
    return status in {PedidoCompra.STATUS_RECEBIDO_PARCIAL, PedidoCompra.STATUS_RECEBIDO}


def _status_form_valido(status_form, status_atual=None):
    if _status_recebimento(status_form):
        return status_atual if status_atual and _status_recebimento(status_atual) else PedidoCompra.STATUS_RASCUNHO
    return status_form


def _pode_cancelar(pedido_compra):
    return pedido_compra.status not in {PedidoCompra.STATUS_CANCELADO, PedidoCompra.STATUS_RECEBIDO}


def pedido_compra_permission_required(permissao):
    def decorator(f):
        @wraps(f)
        @login_required
        def decorated_function(*args, **kwargs):
            if not current_user.tem_permissao(permissao):
                flash("Acesso negado. Voce nao tem permissao para esta operacao.", "error")
                return redirect(url_for("painel.dashboard"))
            return f(*args, **kwargs)

        return decorated_function

    return decorator


def _parse_data(valor):
    texto = (valor or "").strip()
    if not texto:
        return None
    try:
        return datetime.strptime(texto, "%Y-%m-%d").date()
    except ValueError:
        return None


def _usuario_auditoria() -> str | None:
    if hasattr(current_user, "is_authenticated") and current_user.is_authenticated:
        return getattr(current_user, "usuario", None) or getattr(current_user, "email", None)
    return None


def _query_base_pedidos_compra():
    return (
        PedidoCompra.query.options(
            joinedload(PedidoCompra.fornecedor),
            joinedload(PedidoCompra.ordem_servico),
            joinedload(PedidoCompra.pedido_venda),
        )
        .filter(PedidoCompra.ativo.is_(True))
    )


def _carregar_form_context(pedido_compra=None):
    status_editaveis = [
        item
        for item in PedidoCompra.STATUS_CHOICES
        if item[0] not in {PedidoCompra.STATUS_CANCELADO, PedidoCompra.STATUS_RECEBIDO_PARCIAL, PedidoCompra.STATUS_RECEBIDO}
    ]
    return {
        "fornecedores": Fornecedor.query.filter(Fornecedor.ativo.is_(True)).order_by(Fornecedor.nome.asc()).all(),
        "produtos": Produto.query.filter(Produto.ativo.is_(True)).order_by(Produto.nome.asc()).all(),
        "servicos": Servico.query.filter(Servico.ativo.is_(True)).order_by(Servico.nome.asc()).all(),
        "ordens_servico": OrdemServico.query.filter(OrdemServico.ativo.is_(True)).order_by(OrdemServico.id.desc()).all(),
        "pedidos_venda": Pedido.query.filter(Pedido.ativo.is_(True)).order_by(Pedido.id.desc()).all(),
        "status_choices": status_editaveis,
        "finalidade_choices": PedidoCompra.FINALIDADE_CHOICES,
        "today": date.today(),
        "pedido_compra": pedido_compra,
    }


def _aplicar_itens_no_pedido_compra(pedido_compra, itens_form, modo_edicao=False):
    existentes = {item.id: item for item in pedido_compra.itens.order_by(PedidoCompraItem.ordem.asc(), PedidoCompraItem.id.asc()).all()}
    utilizados = set()
    ordem = 1
    for item_form in itens_form:
        tipo_item = item_form["tipo_item"]
        if tipo_item not in {PedidoCompraItem.TIPO_PRODUTO, PedidoCompraItem.TIPO_SERVICO}:
            continue

        item_id = item_form.get("item_id")
        item_existente = existentes.get(item_id) if modo_edicao and item_id else None

        produto_id = item_form["referencia_id"] if tipo_item == PedidoCompraItem.TIPO_PRODUTO else None
        servico_id = item_form["referencia_id"] if tipo_item == PedidoCompraItem.TIPO_SERVICO else None
        descricao = item_form["descricao"]
        unidade = item_form["unidade"]
        quantidade_comprada = item_form["quantidade_comprada"]

        if tipo_item == PedidoCompraItem.TIPO_PRODUTO and produto_id and not descricao:
            produto = Produto.query.filter_by(id=produto_id, ativo=True).first()
            if produto:
                descricao = produto.nome
                unidade = unidade or produto.unidade_medida
        if tipo_item == PedidoCompraItem.TIPO_SERVICO and servico_id and not descricao:
            servico = Servico.query.filter_by(id=servico_id, ativo=True).first()
            if servico:
                descricao = servico.nome
                unidade = unidade or "SV"

        if item_existente:
            quantidade_recebida_atual = Decimal(str(item_existente.quantidade_recebida or 0))
            if Decimal(str(quantidade_comprada or 0)) < quantidade_recebida_atual:
                raise ValueError("Quantidade comprada nao pode ser menor que a quantidade ja recebida.")

            if quantidade_recebida_atual > Decimal("0"):
                if tipo_item != item_existente.tipo_item:
                    raise ValueError("Nao e permitido alterar o tipo de item que ja possui recebimento.")
                if item_existente.tipo_item == PedidoCompraItem.TIPO_PRODUTO and produto_id != item_existente.produto_id:
                    raise ValueError("Nao e permitido alterar o produto de item que ja possui recebimento.")
                if item_existente.tipo_item == PedidoCompraItem.TIPO_SERVICO and servico_id != item_existente.servico_id:
                    raise ValueError("Nao e permitido alterar o servico de item que ja possui recebimento.")

                item_existente.descricao = descricao or "Item sem descricao"
                item_existente.unidade = unidade or ("UN" if item_existente.tipo_item == PedidoCompraItem.TIPO_PRODUTO else "SV")
                item_existente.quantidade_comprada = quantidade_comprada
                item_existente.valor_unitario = item_form["valor_unitario"]
                item_existente.desconto = item_form["desconto"]
                item_existente.ordem = ordem
                utilizados.add(item_existente.id)
                ordem += 1
                continue

            item_existente.tipo_item = tipo_item
            item_existente.produto_id = produto_id
            item_existente.servico_id = servico_id
            item_existente.descricao = descricao or "Item sem descricao"
            item_existente.unidade = unidade or ("UN" if tipo_item == PedidoCompraItem.TIPO_PRODUTO else "SV")
            item_existente.quantidade_comprada = quantidade_comprada
            item_existente.valor_unitario = item_form["valor_unitario"]
            item_existente.desconto = item_form["desconto"]
            item_existente.ordem = ordem
            utilizados.add(item_existente.id)
            ordem += 1
            continue

        db.session.add(
            PedidoCompraItem(
                pedido_compra_id=pedido_compra.id,
                tipo_item=tipo_item,
                produto_id=produto_id,
                servico_id=servico_id,
                descricao=descricao or "Item sem descricao",
                unidade=unidade or ("UN" if tipo_item == PedidoCompraItem.TIPO_PRODUTO else "SV"),
                quantidade_comprada=quantidade_comprada,
                quantidade_recebida=Decimal("0"),
                valor_unitario=item_form["valor_unitario"],
                desconto=item_form["desconto"],
                ordem=ordem,
            )
        )
        ordem += 1

    if modo_edicao:
        for item_existente in existentes.values():
            if item_existente.id in utilizados:
                continue
            if Decimal(str(item_existente.quantidade_recebida or 0)) > Decimal("0"):
                raise ValueError("Nao e permitido excluir item que ja possui recebimento.")
            db.session.delete(item_existente)


@pedido_compra_bp.route("/")
@pedido_compra_permission_required("visualizar_pedidos_compra")
def listar():
    status_filtro = (request.args.get("status") or "").strip().upper()
    fornecedor_filtro = parse_int(request.args.get("fornecedor_id"), default=None)
    finalidade_filtro = (request.args.get("finalidade") or "").strip().upper()
    busca = (request.args.get("busca") or "").strip()

    query = _query_base_pedidos_compra()
    if status_filtro:
        query = query.filter(PedidoCompra.status == status_filtro)
    if fornecedor_filtro:
        query = query.filter(PedidoCompra.fornecedor_id == fornecedor_filtro)
    if finalidade_filtro:
        query = query.filter(PedidoCompra.finalidade == finalidade_filtro)
    if busca:
        query = query.filter(
            db.or_(
                PedidoCompra.numero.ilike(f"%{busca}%"),
                PedidoCompra.solicitante.ilike(f"%{busca}%"),
                PedidoCompra.responsavel_compra.ilike(f"%{busca}%"),
            )
        )

    pedidos_compra = query.order_by(PedidoCompra.data_emissao.desc(), PedidoCompra.id.desc()).all()
    return render_template(
        "pedido_compra/listar.html",
        pedidos_compra=pedidos_compra,
        fornecedores=Fornecedor.query.filter(Fornecedor.ativo.is_(True)).order_by(Fornecedor.nome.asc()).all(),
        status_choices=PedidoCompra.STATUS_CHOICES,
        finalidade_choices=PedidoCompra.FINALIDADE_CHOICES,
        filtros={
            "status": status_filtro,
            "fornecedor_id": fornecedor_filtro,
            "finalidade": finalidade_filtro,
            "busca": busca,
        },
    )


@pedido_compra_bp.route("/novo", methods=["GET", "POST"])
@pedido_compra_permission_required("criar_pedidos_compra")
def novo():
    context = _carregar_form_context()
    if request.method == "POST":
        erros = validar_payload_pedido_compra(request.form)
        itens_form = extrair_itens_form(request.form)
        if erros:
            for erro in erros:
                flash(erro, "error")
            return render_template("pedido_compra/form.html", itens_preview=itens_form, **context)

        pedido_compra = PedidoCompra(
            fornecedor_id=parse_int(request.form.get("fornecedor_id"), default=None),
            ordem_servico_id=parse_int(request.form.get("ordem_servico_id"), default=None),
            pedido_venda_id=parse_int(request.form.get("pedido_venda_id"), default=None),
            data_emissao=_parse_data(request.form.get("data_emissao")) or date.today(),
            previsao_entrega=_parse_data(request.form.get("previsao_entrega")),
            solicitante=(request.form.get("solicitante") or "").strip(),
            responsavel_compra=(request.form.get("responsavel_compra") or "").strip(),
            condicao_pagamento=(request.form.get("condicao_pagamento") or "").strip(),
            observacoes=(request.form.get("observacoes") or "").strip(),
            finalidade=normalizar_finalidade(request.form.get("finalidade")),
            status=_status_form_valido(normalizar_status(request.form.get("status"))),
            desconto=parse_decimal_br(request.form.get("desconto") or 0),
        )
        db.session.add(pedido_compra)
        db.session.flush()

        try:
            _aplicar_itens_no_pedido_compra(pedido_compra, itens_form, modo_edicao=False)
            pedido_compra.recalcular_totais()
            pedido_compra.atualizar_status_recebimento()
            sincronizar_obrigacao_financeira_pedido_compra(pedido_compra, usuario=_usuario_auditoria())
        except ValueError as exc:
            db.session.rollback()
            flash(str(exc), "error")
            return render_template("pedido_compra/form.html", itens_preview=itens_form, **context)

        try:
            db.session.commit()
            flash(f"Pedido de compra {pedido_compra.numero} criado com sucesso.", "success")
            return redirect(url_for("pedido_compra.visualizar", id=pedido_compra.id))
        except Exception as exc:
            db.session.rollback()
            flash(f"Erro ao criar pedido de compra: {exc}", "error")
            return render_template("pedido_compra/form.html", itens_preview=itens_form, **context)

    return render_template("pedido_compra/form.html", itens_preview=[], **context)


@pedido_compra_bp.route("/<int:id>")
@pedido_compra_permission_required("visualizar_pedidos_compra")
def visualizar(id):
    pedido_compra = _query_base_pedidos_compra().filter(PedidoCompra.id == id).first()
    if not pedido_compra:
        flash("Pedido de compra nao encontrado.", "error")
        return redirect(url_for("pedido_compra.listar"))

    itens = pedido_compra.itens.order_by(PedidoCompraItem.ordem.asc(), PedidoCompraItem.id.asc()).all()
    return render_template("pedido_compra/visualizar.html", pedido_compra=pedido_compra, itens=itens)


@pedido_compra_bp.route("/<int:id>/editar", methods=["GET", "POST"])
@pedido_compra_permission_required("editar_pedidos_compra")
def editar(id):
    pedido_compra = _query_base_pedidos_compra().filter(PedidoCompra.id == id).first()
    if not pedido_compra:
        flash("Pedido de compra nao encontrado.", "error")
        return redirect(url_for("pedido_compra.listar"))

    if pedido_compra.status == PedidoCompra.STATUS_CANCELADO:
        flash("Pedido cancelado nao pode ser editado ou reativado.", "error")
        return redirect(url_for("pedido_compra.visualizar", id=pedido_compra.id))

    context = _carregar_form_context(pedido_compra=pedido_compra)
    if request.method == "POST":
        erros = validar_payload_pedido_compra(request.form)
        itens_form = extrair_itens_form(request.form)
        if erros:
            for erro in erros:
                flash(erro, "error")
            return render_template("pedido_compra/form.html", itens_preview=itens_form, **context)

        pedido_compra.fornecedor_id = parse_int(request.form.get("fornecedor_id"), default=pedido_compra.fornecedor_id)
        pedido_compra.ordem_servico_id = parse_int(request.form.get("ordem_servico_id"), default=None)
        pedido_compra.pedido_venda_id = parse_int(request.form.get("pedido_venda_id"), default=None)
        pedido_compra.data_emissao = _parse_data(request.form.get("data_emissao")) or pedido_compra.data_emissao
        pedido_compra.previsao_entrega = _parse_data(request.form.get("previsao_entrega"))
        pedido_compra.solicitante = (request.form.get("solicitante") or "").strip()
        pedido_compra.responsavel_compra = (request.form.get("responsavel_compra") or "").strip()
        pedido_compra.condicao_pagamento = (request.form.get("condicao_pagamento") or "").strip()
        pedido_compra.observacoes = (request.form.get("observacoes") or "").strip()
        pedido_compra.finalidade = normalizar_finalidade(request.form.get("finalidade"))
        pedido_compra.status = _status_form_valido(
            normalizar_status(request.form.get("status")),
            status_atual=pedido_compra.status,
        )
        pedido_compra.desconto = parse_decimal_br(request.form.get("desconto") or 0)

        try:
            _aplicar_itens_no_pedido_compra(pedido_compra, itens_form, modo_edicao=True)
            pedido_compra.recalcular_totais()
            pedido_compra.atualizar_status_recebimento()
            sincronizar_obrigacao_financeira_pedido_compra(pedido_compra, usuario=_usuario_auditoria())
        except ValueError as exc:
            db.session.rollback()
            flash(str(exc), "error")
            return render_template("pedido_compra/form.html", itens_preview=itens_form, **context)

        try:
            db.session.commit()
            flash(f"Pedido de compra {pedido_compra.numero} atualizado com sucesso.", "success")
            return redirect(url_for("pedido_compra.visualizar", id=pedido_compra.id))
        except Exception as exc:
            db.session.rollback()
            flash(f"Erro ao atualizar pedido de compra: {exc}", "error")
            return render_template("pedido_compra/form.html", itens_preview=itens_form, **context)

    itens_preview = [
        {
            "tipo_item": item.tipo_item,
            "item_id": item.id,
            "referencia_tipo": "P" if item.tipo_item == PedidoCompraItem.TIPO_PRODUTO else "S",
            "referencia_id": item.produto_id if item.tipo_item == PedidoCompraItem.TIPO_PRODUTO else item.servico_id,
            "descricao": item.descricao,
            "unidade": item.unidade,
            "quantidade_comprada": Decimal(str(item.quantidade_comprada or 0)),
            "quantidade_recebida": Decimal(str(item.quantidade_recebida or 0)),
            "valor_unitario": Decimal(str(item.valor_unitario or 0)),
            "desconto": Decimal(str(item.desconto or 0)),
        }
        for item in pedido_compra.itens.order_by(PedidoCompraItem.ordem.asc(), PedidoCompraItem.id.asc()).all()
    ]
    return render_template("pedido_compra/form.html", itens_preview=itens_preview, **context)


@pedido_compra_bp.route("/<int:id>/cancelar", methods=["GET", "POST"])
@pedido_compra_permission_required("cancelar_pedidos_compra")
def cancelar(id):
    pedido_compra = _query_base_pedidos_compra().filter(PedidoCompra.id == id).first()
    if not pedido_compra:
        flash("Pedido de compra nao encontrado.", "error")
        return redirect(url_for("pedido_compra.listar"))

    if not _pode_cancelar(pedido_compra):
        flash("Pedido de compra nao pode ser cancelado neste status.", "error")
        return redirect(url_for("pedido_compra.visualizar", id=pedido_compra.id))

    if request.method == "GET":
        return render_template("pedido_compra/confirmar_cancelamento.html", pedido_compra=pedido_compra)

    try:
        pedido_compra.status = PedidoCompra.STATUS_CANCELADO
        sincronizar_obrigacao_financeira_pedido_compra(pedido_compra, usuario=_usuario_auditoria())
        db.session.commit()
        flash(f"Pedido de compra {pedido_compra.numero} cancelado com sucesso.", "success")
    except Exception as exc:
        db.session.rollback()
        flash(f"Erro ao cancelar pedido de compra: {exc}", "error")
    return redirect(url_for("pedido_compra.listar"))


@pedido_compra_bp.route("/<int:id>/recebimento", methods=["GET", "POST"])
@pedido_compra_permission_required("receber_pedidos_compra")
def recebimento(id):
    pedido_compra = _query_base_pedidos_compra().filter(PedidoCompra.id == id).first()
    if not pedido_compra:
        flash("Pedido de compra nao encontrado.", "error")
        return redirect(url_for("pedido_compra.listar"))

    itens = pedido_compra.itens.order_by(PedidoCompraItem.ordem.asc(), PedidoCompraItem.id.asc()).all()
    if request.method == "POST":
        if pedido_compra.status == PedidoCompra.STATUS_CANCELADO:
            flash("Pedido cancelado nao pode receber itens.", "error")
            return render_template("pedido_compra/recebimento.html", pedido_compra=pedido_compra, itens=itens)
        if not pedido_compra.pode_receber():
            flash("Recebimento permitido apenas para pedidos aprovados, enviados ou parcialmente recebidos.", "error")
            return render_template("pedido_compra/recebimento.html", pedido_compra=pedido_compra, itens=itens)

        incrementos = request.form.getlist("item_quantidade_receber[]")
        try:
            for item, incremento in zip(itens, incrementos):
                item.registrar_recebimento(parse_decimal_br(incremento, default="0"))
            pedido_compra.atualizar_status_recebimento()
            sincronizar_obrigacao_financeira_pedido_compra(pedido_compra, usuario=_usuario_auditoria())
            db.session.commit()
            flash(f"Recebimento do pedido de compra {pedido_compra.numero} registrado.", "success")
            return redirect(url_for("pedido_compra.visualizar", id=pedido_compra.id))
        except Exception as exc:
            db.session.rollback()
            flash(f"Erro ao registrar recebimento: {exc}", "error")

    return render_template("pedido_compra/recebimento.html", pedido_compra=pedido_compra, itens=itens)


@pedido_compra_bp.route("/<int:id>/imprimir")
@pedido_compra_permission_required("visualizar_pedidos_compra")
def imprimir(id):
    pedido_compra = _query_base_pedidos_compra().filter(PedidoCompra.id == id).first()
    if not pedido_compra:
        flash("Pedido de compra nao encontrado.", "error")
        return redirect(url_for("pedido_compra.listar"))

    itens = pedido_compra.itens.order_by(PedidoCompraItem.ordem.asc(), PedidoCompraItem.id.asc()).all()
    return render_template("pedido_compra/imprimir.html", pedido_compra=pedido_compra, itens=itens)
