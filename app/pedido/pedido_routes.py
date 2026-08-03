# -*- coding: utf-8 -*-
"""Rotas web do modulo de Pedidos."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

from flask import Blueprint, flash, redirect, render_template, request, url_for
from sqlalchemy.orm import joinedload

from app.cliente.cliente_model import Cliente
from app.extensoes import db
from app.pedido.forms.pedido_forms import (
    extrair_itens_form,
    normalizar_status,
    parse_decimal_br,
    parse_int,
    validar_payload_pedido,
)
from app.pedido.pedido_model import Pedido, PedidoItem
from app.produto.produto_model import Produto
from app.proposta.proposta_model import Proposta
from app.servico.servico_model import Servico

pedido_bp = Blueprint("pedido", __name__, template_folder="templates")


def _parse_data(valor):
    texto = (valor or "").strip()
    if not texto:
        return None
    try:
        return datetime.strptime(texto, "%Y-%m-%d").date()
    except ValueError:
        return None


def _query_base_pedidos():
    return (
        Pedido.query.options(
            joinedload(Pedido.cliente),
            joinedload(Pedido.proposta),
        )
        .filter(Pedido.ativo.is_(True))
    )


def _carregar_form_context(pedido=None, proposta_id=None):
    clientes = Cliente.query.filter(Cliente.ativo.is_(True)).order_by(Cliente.nome.asc()).all()
    produtos = Produto.query.filter(Produto.ativo.is_(True)).order_by(Produto.nome.asc()).all()
    servicos = Servico.query.filter(Servico.ativo.is_(True)).order_by(Servico.nome.asc()).all()

    propostas_query = Proposta.query.filter(Proposta.ativo.is_(True))
    if pedido and pedido.proposta_id:
        propostas_query = propostas_query.filter(
            db.or_(Proposta.status.ilike("aprovada"), Proposta.id == pedido.proposta_id)
        )
    else:
        propostas_query = propostas_query.filter(Proposta.status.ilike("aprovada"))

    propostas = propostas_query.order_by(Proposta.data_emissao.desc()).all()

    proposta_preselecionada = None
    if proposta_id:
        proposta_preselecionada = Proposta.query.filter_by(id=proposta_id, ativo=True).first()

    return {
        "clientes": clientes,
        "produtos": produtos,
        "servicos": servicos,
        "propostas": propostas,
        "proposta_preselecionada": proposta_preselecionada,
        "status_choices": Pedido.STATUS_CHOICES,
        "today": date.today(),
    }


def _aplicar_itens_no_pedido(pedido, itens_form):
    for item_existente in list(pedido.itens.all()):
        db.session.delete(item_existente)

    ordem = 1
    for item_form in itens_form:
        tipo_item = item_form["tipo_item"]
        if item_form.get("referencia_tipo") == "P":
            tipo_item = PedidoItem.TIPO_PRODUTO
        elif item_form.get("referencia_tipo") == "S":
            tipo_item = PedidoItem.TIPO_SERVICO

        if tipo_item not in {PedidoItem.TIPO_PRODUTO, PedidoItem.TIPO_SERVICO}:
            continue

        referencia_id = item_form["referencia_id"]
        descricao = item_form["descricao"]

        produto_id = None
        servico_id = None

        if tipo_item == PedidoItem.TIPO_PRODUTO:
            produto_id = referencia_id
            if not descricao and produto_id:
                produto = Produto.query.filter_by(id=produto_id, ativo=True).first()
                if produto:
                    descricao = produto.nome
        else:
            servico_id = referencia_id
            if not descricao and servico_id:
                servico = Servico.query.filter_by(id=servico_id, ativo=True).first()
                if servico:
                    descricao = servico.nome

        if not descricao:
            descricao = "Item sem descricao"

        pedido_item = PedidoItem(
            pedido_id=pedido.id,
            tipo_item=tipo_item,
            produto_id=produto_id,
            servico_id=servico_id,
            descricao=descricao,
            quantidade=item_form["quantidade"],
            valor_unitario=item_form["valor_unitario"],
            desconto=item_form["desconto"],
            ordem=ordem,
        )
        db.session.add(pedido_item)
        ordem += 1


def _popular_itens_da_proposta(proposta):
    itens = []

    for item_produto in proposta.itens_produto:
        if not item_produto.ativo:
            continue
        itens.append(
            {
                "tipo_item": PedidoItem.TIPO_PRODUTO,
                "referencia_tipo": "P",
                "referencia_id": item_produto.produto_id,
                "descricao": item_produto.descricao,
                "quantidade": Decimal(str(item_produto.quantidade or 0)),
                "valor_unitario": Decimal(str(item_produto.valor_unitario or 0)),
                "desconto": Decimal("0.00"),
            }
        )

    for item_servico in proposta.itens_servico:
        if not item_servico.ativo:
            continue
        if not (item_servico.descricao or "").strip():
            continue
        servico_relacionado = Servico.query.filter(
            Servico.ativo.is_(True),
            Servico.nome.ilike(item_servico.descricao or ""),
        ).first()
        if not servico_relacionado:
            continue
        itens.append(
            {
                "tipo_item": PedidoItem.TIPO_SERVICO,
                "referencia_tipo": "S",
                "referencia_id": servico_relacionado.id,
                "descricao": item_servico.descricao,
                "quantidade": Decimal(str(item_servico.quantidade or 0)),
                "valor_unitario": Decimal(str(item_servico.valor_unitario or 0)),
                "desconto": Decimal("0.00"),
            }
        )

    return itens


@pedido_bp.route("/")
def listar():
    status_filtro = (request.args.get("status") or "").strip().upper()
    cliente_filtro = parse_int(request.args.get("cliente_id"), default=None)
    busca = (request.args.get("busca") or "").strip()

    query = _query_base_pedidos()

    if status_filtro:
        query = query.filter(Pedido.status == status_filtro)

    if cliente_filtro:
        query = query.filter(Pedido.cliente_id == cliente_filtro)

    if busca:
        query = query.filter(
            db.or_(
                Pedido.numero.ilike(f"%{busca}%"),
                Pedido.responsavel.ilike(f"%{busca}%"),
                Pedido.solicitante.ilike(f"%{busca}%"),
            )
        )

    pedidos = query.order_by(Pedido.data_pedido.desc(), Pedido.id.desc()).all()

    return render_template(
        "pedido/listar.html",
        pedidos=pedidos,
        status_choices=Pedido.STATUS_CHOICES,
        clientes=Cliente.query.filter(Cliente.ativo.is_(True)).order_by(Cliente.nome.asc()).all(),
        filtros={
            "status": status_filtro,
            "cliente_id": cliente_filtro,
            "busca": busca,
        },
    )


@pedido_bp.route("/novo", methods=["GET", "POST"])
def novo():
    context = _carregar_form_context(proposta_id=parse_int(request.args.get("proposta_id"), default=None))

    if request.method == "POST":
        erros = validar_payload_pedido(request.form)
        if erros:
            for erro in erros:
                flash(erro, "error")
            return render_template("pedido/form.html", pedido=None, itens_preview=[], **context)

        proposta_id = parse_int(request.form.get("proposta_id"), default=None)
        cliente_id = parse_int(request.form.get("cliente_id"), default=None)

        if proposta_id:
            ja_vinculado = Pedido.query.filter(
                Pedido.proposta_id == proposta_id,
                Pedido.ativo.is_(True),
            ).first()
            if ja_vinculado:
                flash("Ja existe pedido ativo vinculado a esta proposta.", "error")
                return render_template("pedido/form.html", pedido=None, itens_preview=[], **context)

        pedido = Pedido(
            cliente_id=cliente_id,
            proposta_id=proposta_id,
            data_pedido=_parse_data(request.form.get("data_pedido")) or date.today(),
            status=normalizar_status(request.form.get("status")),
            responsavel=(request.form.get("responsavel") or "").strip(),
            solicitante=(request.form.get("solicitante") or "").strip(),
            telefone_contato=(request.form.get("telefone_contato") or "").strip(),
            email_contato=(request.form.get("email_contato") or "").strip(),
            prazo_previsto=_parse_data(request.form.get("prazo_previsto")),
            condicoes_pagamento=(request.form.get("condicoes_pagamento") or "").strip(),
            desconto=parse_decimal_br(request.form.get("desconto") or 0),
            observacoes=(request.form.get("observacoes") or "").strip(),
        )

        db.session.add(pedido)
        db.session.flush()

        itens_form = extrair_itens_form(request.form)
        _aplicar_itens_no_pedido(pedido, itens_form)
        pedido.recalcular_totais()

        try:
            db.session.commit()
            flash(f"Pedido {pedido.numero} criado com sucesso.", "success")
            return redirect(url_for("pedido.visualizar", id=pedido.id))
        except Exception as exc:
            db.session.rollback()
            flash(f"Erro ao criar pedido: {exc}", "error")
            return render_template("pedido/form.html", pedido=None, itens_preview=itens_form, **context)

    proposta_seed = context["proposta_preselecionada"]
    itens_seed = []
    if proposta_seed:
        itens_seed = _popular_itens_da_proposta(proposta_seed)

    return render_template("pedido/form.html", pedido=None, itens_preview=itens_seed, **context)


@pedido_bp.route("/<int:id>")
def visualizar(id):
    pedido = (
        _query_base_pedidos()
        .filter(Pedido.id == id)
        .first()
    )

    if not pedido:
        flash("Pedido nao encontrado.", "error")
        return redirect(url_for("pedido.listar"))

    itens = pedido.itens.order_by(PedidoItem.ordem.asc(), PedidoItem.id.asc()).all()
    return render_template("pedido/visualizar.html", pedido=pedido, itens=itens)


@pedido_bp.route("/<int:id>/editar", methods=["GET", "POST"])
def editar(id):
    pedido = _query_base_pedidos().filter(Pedido.id == id).first()

    if not pedido:
        flash("Pedido nao encontrado.", "error")
        return redirect(url_for("pedido.listar"))

    context = _carregar_form_context(pedido=pedido)

    if request.method == "POST":
        erros = validar_payload_pedido(request.form)
        if erros:
            for erro in erros:
                flash(erro, "error")
            return render_template(
                "pedido/form.html",
                pedido=pedido,
                itens_preview=extrair_itens_form(request.form),
                **context,
            )

        proposta_id = parse_int(request.form.get("proposta_id"), default=None)
        if proposta_id:
            ja_vinculado = Pedido.query.filter(
                Pedido.proposta_id == proposta_id,
                Pedido.id != pedido.id,
                Pedido.ativo.is_(True),
            ).first()
            if ja_vinculado:
                flash("Ja existe pedido ativo vinculado a esta proposta.", "error")
                return render_template(
                    "pedido/form.html",
                    pedido=pedido,
                    itens_preview=extrair_itens_form(request.form),
                    **context,
                )

        pedido.cliente_id = parse_int(request.form.get("cliente_id"), default=pedido.cliente_id)
        pedido.proposta_id = proposta_id
        pedido.data_pedido = _parse_data(request.form.get("data_pedido")) or pedido.data_pedido
        pedido.status = normalizar_status(request.form.get("status"))
        pedido.responsavel = (request.form.get("responsavel") or "").strip()
        pedido.solicitante = (request.form.get("solicitante") or "").strip()
        pedido.telefone_contato = (request.form.get("telefone_contato") or "").strip()
        pedido.email_contato = (request.form.get("email_contato") or "").strip()
        pedido.prazo_previsto = _parse_data(request.form.get("prazo_previsto"))
        pedido.condicoes_pagamento = (request.form.get("condicoes_pagamento") or "").strip()
        pedido.desconto = parse_decimal_br(request.form.get("desconto") or 0)
        pedido.observacoes = (request.form.get("observacoes") or "").strip()

        itens_form = extrair_itens_form(request.form)
        _aplicar_itens_no_pedido(pedido, itens_form)
        pedido.recalcular_totais()

        try:
            db.session.commit()
            flash(f"Pedido {pedido.numero} atualizado com sucesso.", "success")
            return redirect(url_for("pedido.visualizar", id=pedido.id))
        except Exception as exc:
            db.session.rollback()
            flash(f"Erro ao atualizar pedido: {exc}", "error")
            return render_template("pedido/form.html", pedido=pedido, itens_preview=itens_form, **context)

    itens = pedido.itens.order_by(PedidoItem.ordem.asc(), PedidoItem.id.asc()).all()
    itens_preview = [
        {
            "tipo_item": item.tipo_item,
            "referencia_tipo": "P" if item.tipo_item == PedidoItem.TIPO_PRODUTO else "S",
            "referencia_id": item.produto_id if item.tipo_item == PedidoItem.TIPO_PRODUTO else item.servico_id,
            "descricao": item.descricao,
            "quantidade": Decimal(str(item.quantidade or 0)),
            "valor_unitario": Decimal(str(item.valor_unitario or 0)),
            "desconto": Decimal(str(item.desconto or 0)),
        }
        for item in itens
    ]

    return render_template("pedido/form.html", pedido=pedido, itens_preview=itens_preview, **context)


@pedido_bp.route("/<int:id>/excluir", methods=["GET", "POST"])
def excluir(id):
    pedido = _query_base_pedidos().filter(Pedido.id == id).first()

    if not pedido:
        flash("Pedido nao encontrado.", "error")
        return redirect(url_for("pedido.listar"))

    if request.method == "GET":
        return render_template("pedido/confirmar_exclusao.html", pedido=pedido)

    try:
        pedido.ativo = False
        db.session.commit()
        flash(f"Pedido {pedido.numero} excluido com sucesso.", "success")
    except Exception as exc:
        db.session.rollback()
        flash(f"Erro ao excluir pedido: {exc}", "error")

    return redirect(url_for("pedido.listar"))
