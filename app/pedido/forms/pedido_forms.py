# -*- coding: utf-8 -*-
"""Helpers de validacao e parsing do formulario de Pedidos."""

from __future__ import annotations

from decimal import Decimal, InvalidOperation


STATUS_VALIDOS = {
    "RASCUNHO",
    "AGUARDANDO_CONFIRMACAO",
    "CONFIRMADO",
    "EM_EXECUCAO",
    "CONCLUIDO",
    "CANCELADO",
}


def parse_int(valor, default=None):
    if valor is None:
        return default
    texto = str(valor).strip()
    if not texto:
        return default
    try:
        return int(texto)
    except (TypeError, ValueError):
        return default


def parse_decimal_br(valor, default="0"):
    if valor is None:
        return Decimal(str(default))

    texto = str(valor).strip()
    if not texto:
        return Decimal(str(default))

    texto = texto.replace("R$", "").replace(" ", "")
    if "," in texto:
        texto = texto.replace(".", "").replace(",", ".")

    try:
        return Decimal(texto)
    except (InvalidOperation, ValueError):
        return Decimal(str(default))


def normalizar_status(valor):
    status = str(valor or "RASCUNHO").strip().upper()
    if status not in STATUS_VALIDOS:
        return "RASCUNHO"
    return status


def extrair_itens_form(form_data):
    tipos = form_data.getlist("item_tipo[]")
    referencias = form_data.getlist("item_referencia_id[]")
    descricoes = form_data.getlist("item_descricao[]")
    quantidades = form_data.getlist("item_quantidade[]")
    valores = form_data.getlist("item_valor_unitario[]")
    descontos = form_data.getlist("item_desconto[]")

    itens = []
    tamanho = max(
        len(tipos),
        len(referencias),
        len(descricoes),
        len(quantidades),
        len(valores),
        len(descontos),
    )

    for idx in range(tamanho):
        referencia_raw = referencias[idx] if idx < len(referencias) else ""
        referencia_raw = str(referencia_raw or "").strip()
        referencia_tipo = ""
        referencia_id = None

        if ":" in referencia_raw:
            prefixo, sufixo = referencia_raw.split(":", 1)
            referencia_tipo = prefixo.strip().upper()
            referencia_id = parse_int(sufixo, default=None)
        else:
            referencia_id = parse_int(referencia_raw, default=None)

        item = {
            "tipo_item": (tipos[idx] if idx < len(tipos) else "").strip().upper(),
            "referencia_tipo": referencia_tipo,
            "referencia_id": referencia_id,
            "descricao": (descricoes[idx] if idx < len(descricoes) else "").strip(),
            "quantidade": parse_decimal_br(quantidades[idx], default="1") if idx < len(quantidades) else Decimal("1"),
            "valor_unitario": parse_decimal_br(valores[idx], default="0") if idx < len(valores) else Decimal("0"),
            "desconto": parse_decimal_br(descontos[idx], default="0") if idx < len(descontos) else Decimal("0"),
        }
        itens.append(item)

    return itens


def validar_payload_pedido(form_data):
    erros = []

    if not form_data.get("cliente_id"):
        erros.append("Cliente e obrigatorio.")

    desconto = parse_decimal_br(form_data.get("desconto", "0"), default="0")
    if desconto < Decimal("0"):
        erros.append("Desconto nao pode ser negativo.")

    itens = extrair_itens_form(form_data)
    itens_validos = 0

    for idx, item in enumerate(itens, start=1):
        tipo_item = item["tipo_item"]
        if item.get("referencia_tipo") == "P":
            tipo_item = "PRODUTO"
        elif item.get("referencia_tipo") == "S":
            tipo_item = "SERVICO"

        if tipo_item not in {"PRODUTO", "SERVICO"}:
            continue

        if item["quantidade"] <= Decimal("0"):
            erros.append(f"Item {idx}: quantidade deve ser maior que zero.")

        if item["valor_unitario"] < Decimal("0"):
            erros.append(f"Item {idx}: valor unitario nao pode ser negativo.")

        if item["desconto"] < Decimal("0"):
            erros.append(f"Item {idx}: desconto nao pode ser negativo.")

        if item["referencia_id"] is None:
            erros.append(f"Item {idx}: selecione produto/servico vinculado.")

        itens_validos += 1

    if itens_validos == 0:
        erros.append("Adicione ao menos um item de produto ou servico.")

    return erros
