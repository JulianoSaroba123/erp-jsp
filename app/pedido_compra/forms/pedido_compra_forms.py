# -*- coding: utf-8 -*-

from __future__ import annotations

from decimal import Decimal, InvalidOperation


STATUS_VALIDOS = {
    "RASCUNHO",
    "AGUARDANDO_APROVACAO",
    "APROVADO",
    "ENVIADO_FORNECEDOR",
    "RECEBIDO_PARCIAL",
    "RECEBIDO",
    "CANCELADO",
}

FINALIDADES_VALIDAS = {
    "ESTOQUE",
    "ORDEM_SERVICO",
    "PEDIDO_VENDA",
    "ADMINISTRATIVO",
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


def normalizar_finalidade(valor):
    finalidade = str(valor or "ESTOQUE").strip().upper()
    if finalidade not in FINALIDADES_VALIDAS:
        return "ESTOQUE"
    return finalidade


def extrair_itens_form(form_data):
    item_ids = form_data.getlist("item_id[]")
    tipos = form_data.getlist("item_tipo[]")
    referencias = form_data.getlist("item_referencia_id[]")
    descricoes = form_data.getlist("item_descricao[]")
    unidades = form_data.getlist("item_unidade[]")
    quantidades = form_data.getlist("item_quantidade[]")
    valores = form_data.getlist("item_valor_unitario[]")
    descontos = form_data.getlist("item_desconto[]")

    tamanho = max(
        len(item_ids),
        len(tipos),
        len(referencias),
        len(descricoes),
        len(unidades),
        len(quantidades),
        len(valores),
        len(descontos),
    )

    itens = []
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

        tipo_item = (tipos[idx] if idx < len(tipos) else "").strip().upper()
        if referencia_tipo == "P":
            tipo_item = "PRODUTO"
        elif referencia_tipo == "S":
            tipo_item = "SERVICO"

        itens.append(
            {
                "item_id": parse_int(item_ids[idx], default=None) if idx < len(item_ids) else None,
                "tipo_item": tipo_item,
                "referencia_tipo": referencia_tipo,
                "referencia_id": referencia_id,
                "descricao": (descricoes[idx] if idx < len(descricoes) else "").strip(),
                "unidade": (unidades[idx] if idx < len(unidades) else "").strip(),
                "quantidade_comprada": parse_decimal_br(quantidades[idx], default="1") if idx < len(quantidades) else Decimal("1"),
                "valor_unitario": parse_decimal_br(valores[idx], default="0") if idx < len(valores) else Decimal("0"),
                "desconto": parse_decimal_br(descontos[idx], default="0") if idx < len(descontos) else Decimal("0"),
            }
        )

    return itens


def validar_payload_pedido_compra(form_data):
    erros = []

    status = normalizar_status(form_data.get("status"))
    if status in {"RECEBIDO_PARCIAL", "RECEBIDO"}:
        erros.append("Status de recebimento e definido apenas pela tela de recebimento.")

    if not form_data.get("fornecedor_id"):
        erros.append("Fornecedor e obrigatorio.")

    desconto = parse_decimal_br(form_data.get("desconto", "0"), default="0")
    if desconto < Decimal("0"):
        erros.append("Desconto nao pode ser negativo.")

    finalidade = normalizar_finalidade(form_data.get("finalidade"))
    if finalidade not in FINALIDADES_VALIDAS:
        erros.append("Finalidade invalida.")

    itens = extrair_itens_form(form_data)
    itens_validos = 0
    for idx, item in enumerate(itens, start=1):
        if item["tipo_item"] not in {"PRODUTO", "SERVICO"}:
            continue

        if item["referencia_id"] is None:
            erros.append(f"Item {idx}: selecione produto/servico vinculado.")
        if item["quantidade_comprada"] <= Decimal("0"):
            erros.append(f"Item {idx}: quantidade comprada deve ser maior que zero.")
        if item["valor_unitario"] < Decimal("0"):
            erros.append(f"Item {idx}: valor unitario nao pode ser negativo.")
        if item["desconto"] < Decimal("0"):
            erros.append(f"Item {idx}: desconto nao pode ser negativo.")
        itens_validos += 1

    if itens_validos == 0:
        erros.append("Adicione ao menos um item de produto ou servico.")

    return erros
