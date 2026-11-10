# -*- coding: utf-8 -*-
"""Projeção conservadora de caixa: títulos pendentes + contas mensais virtuais.

NÃO faz INSERT/UPDATE e NÃO gera pagamentos. A cobrança do custo fixo só é
simulada quando não existe título da mesma competência ou possível duplicata
manual identificável. O valor cadastrado é ESTIMATIVA, nunca compromisso
documental confirmado para contas de consumo variáveis.
"""
from calendar import monthrange
from collections import defaultdict
from datetime import date, timedelta
from decimal import Decimal
from types import SimpleNamespace
import re
import unicodedata


CENT = Decimal("0.01")
TIPOS_ENTRADA = {"receita", "conta_receber"}
TIPOS_SAIDA = {"despesa", "conta_pagar"}
STATUS_QUITADOS = {"pago", "recebido"}
STATUS_PENDENTES = {"pendente", "vencido", "atrasado"}
# Exigir revisão antes de considerar como obrigação gerencial automática.
REVISAR = {"Cartão de Crédito", "Auxiliar de Manutenção", "Prolabore"}


def dinheiro(value):
    return Decimal(str(value or 0)).quantize(CENT)


def chave_mes(data):
    return (data.year, data.month)


def meses_no_intervalo(inicio, fim):
    ano, mes = inicio.year, inicio.month
    while (ano, mes) <= (fim.year, fim.month):
        yield ano, mes
        if mes == 12:
            ano, mes = ano + 1, 1
        else:
            mes += 1


def dia_vencimento(custo, ano, mes):
    dia = int(getattr(custo, "dia_vencimento", 0) or 0)
    if dia < 1 or dia > 31:
        raise ValueError("Custo fixo com dia de vencimento inválido")
    return date(ano, mes, min(dia, monthrange(ano, mes)[1]))


def _texto(value):
    raw = unicodedata.normalize("NFD", str(value or "").strip().lower())
    sem_acento = "".join(char for char in raw if unicodedata.category(char) != "Mn")
    return re.sub(r"[^a-z0-9]+", " ", sem_acento).strip()


def _mesmo_item_manual(custo, lanc):
    """Sinal forte, não inferência por valor isolado. Pode omitir custo se houver dúvida."""
    descricao = _texto(getattr(lanc, "descricao", ""))
    nome = _texto(custo.nome)
    categoria = _texto(custo.categoria)
    if nome and len(nome) >= 5 and nome in descricao:
        return True
    aliases = {
        "aluguel": ("aluguel",),
        "energia": ("energia eletrica", "conta de luz", "cpfl"),
        "agua": ("samae", "conta de agua"),
        "contabilidade": ("contador", "contabilidade", "honorarios contabeis"),
        "internet": ("internet", "tvac"),
    }
    return any(palavra in descricao for palavra in aliases.get(categoria, ()))


def gerar_previsao(*, hoje, dias, saldo_inicial, conta_id, custos, lancamentos):
    """Calcula 30/60/90 dias sem gravar linhas financeiras.

    - títulos efetivamente quitados não são novamente projetados;
    - títulos a pagar/receber pendentes entram pelo valor correto;
    - custo fixo gera previsão virtual somente se não há vínculo ou evidência
      de título manual do mesmo item na competência;
    - se o vencimento do custo já passou no mês atual, mostra pendência na
      data atual (e sinaliza atraso), sem presumir quitação;
    - custos cadastrais de revisão obrigatória aparecem como alertas e
      NÃO são automaticamente descontados da projeção principal;
    - saldo inicial representa extrato importado; NÃO é lucro nem banco em tempo real.
    """
    if dias not in (30, 60, 90):
        raise ValueError("Horizonte deve ser 30, 60 ou 90 dias")
    fim = hoje + timedelta(days=dias)
    primeiro_mes = date(hoje.year, hoje.month, 1)
    inicio_mes = chave_mes(primeiro_mes)

    todos = [l for l in lancamentos if getattr(l, "ativo", True)]
    coberturas = defaultdict(list)
    for l in todos:
        venc = getattr(l, "data_vencimento", None)
        pago = getattr(l, "data_pagamento", None)
        competencia = venc or pago or getattr(l, "data_lancamento", None)
        if not competencia:
            continue
        if getattr(l, "custo_fixo_id", None):
            coberturas[(l.custo_fixo_id, chave_mes(competencia))].append(l)

    previstos = defaultdict(list)
    alertas = []
    # 1. Contas existentes são verdade operacional. Apenas pendentes afetam futuro.
    for l in todos:
        if conta_id is not None and getattr(l, "conta_bancaria_id", None) not in (None, conta_id):
            continue
        tipo = str(getattr(l, "tipo", "") or "").strip().lower()
        status = str(getattr(l, "status", "") or "").strip().lower()
        if tipo not in TIPOS_ENTRADA | TIPOS_SAIDA:
            continue
        if status in STATUS_QUITADOS:
            continue
        if status not in STATUS_PENDENTES:
            continue
        venc = getattr(l, "data_vencimento", None)
        if not venc or venc > fim:
            continue
        dia = max(venc, hoje)
        previstos[dia].append(SimpleNamespace(
            descricao=getattr(l, "descricao", "") or "Título financeiro pendente",
            tipo=tipo,
            valor=float(dinheiro(getattr(l, "valor", 0))),
            categoria=getattr(l, "categoria", ""),
            origem="LANCAMENTO_EXISTENTE",
            id=getattr(l, "id", None),
            vencimento_original=venc,
        ))
        if venc < hoje:
            alertas.append(f"Título vencido: {getattr(l,'descricao','')} (vencia em {venc:%d/%m/%Y})")

    # 2. Estimativas de recorrência, sem gerar títulos fictícios no ERP.
    qtd_virtuais = 0
    for custo in custos:
        if not bool(getattr(custo, "ativo", True)):
            continue
        if not bool(getattr(custo, "gerar_automaticamente", True)):
            continue
        if str(getattr(custo, "tipo", "")).strip().lower() != "despesa":
            continue
        if conta_id is not None and getattr(custo, "conta_bancaria_id", None) not in (None, conta_id):
            continue
        for ano, mes in meses_no_intervalo(hoje, fim):
            venc = dia_vencimento(custo, ano, mes)
            data_inicio = getattr(custo, "data_inicio", None)
            data_fim = getattr(custo, "data_fim", None)
            if (data_inicio and venc < data_inicio) or (data_fim and venc > data_fim):
                continue
            if venc > fim:
                continue
            if coberturas.get((getattr(custo,"id",None), (ano,mes))):
                continue

            # Duplicidade provável: usuário já pode ter pago/lancado manualmente.
            evidencias = []
            for l in todos:
                if getattr(l, "custo_fixo_id", None):
                    continue
                tp = str(getattr(l, "tipo", "") or "").strip().lower()
                if tp not in TIPOS_SAIDA:
                    continue
                if conta_id is not None and getattr(l, "conta_bancaria_id", None) not in (None, conta_id):
                    continue
                data_ref = getattr(l, "data_vencimento", None) or getattr(l, "data_pagamento", None) or getattr(l, "data_lancamento", None)
                if data_ref and chave_mes(data_ref) == (ano,mes) and _mesmo_item_manual(custo,l):
                    evidencias.append(l)
            if evidencias:
                alertas.append(f"{custo.nome} {mes:02d}/{ano}: há lançamento manual possivelmente correspondente; estimativa omitida até conferência.")
                continue

            if getattr(custo, "nome", "") in REVISAR:
                alertas.append(f"{custo.nome} {mes:02d}/{ano}: cadastro exige revisão (classificação, valor ou duplicidade). Não descontado automaticamente.")
                continue
            dia = max(venc, hoje)
            valor = dinheiro(getattr(custo, "valor_mensal", 0))
            if valor <= 0:
                alertas.append(f"{custo.nome}: valor mensal inválido; não projetado.")
                continue
            previstos[dia].append(SimpleNamespace(
                descricao=f"PREVISÃO CADASTRAL: {custo.nome} ({mes:02d}/{ano})",
                tipo="conta_pagar",
                categoria=custo.categoria,
                valor=float(valor),
                origem="PREVISAO_CUSTO_FIXO",
                id=None,
                vencimento_original=venc,
            ))
            qtd_virtuais += 1
            if venc < hoje:
                alertas.append(f"{custo.nome} {mes:02d}/{ano}: vencimento cadastrado anterior a hoje; confira se já foi pago.")

    saldo = dinheiro(saldo_inicial)
    detalhes = []
    total_entradas = Decimal("0.00")
    total_saidas = Decimal("0.00")
    dia = hoje
    while dia <= fim:
        itens = previstos[dia]
        entradas = sum((dinheiro(l.valor) for l in itens if l.tipo in TIPOS_ENTRADA), Decimal("0.00"))
        saidas = sum((dinheiro(l.valor) for l in itens if l.tipo in TIPOS_SAIDA), Decimal("0.00"))
        saldo += entradas - saidas
        total_entradas += entradas
        total_saidas += saidas
        detalhes.append({
            "data": dia,
            "receitas": float(entradas),
            "despesas": float(saidas),
            "saldo_dia": float(entradas - saidas),
            "saldo_acumulado": float(saldo),
            "lancamentos": itens,
        })
        dia += timedelta(days=1)

    return {
        "projecao": detalhes,
        "saldo_inicial": float(dinheiro(saldo_inicial)),
        "saldo_final": float(saldo),
        "total_receitas": float(total_entradas),
        "total_despesas": float(total_saidas),
        "alertas": alertas,
        "dias_saldo_negativo": [d for d in detalhes if d["saldo_acumulado"] < 0],
        "qtd_recorrencias_estimadas": qtd_virtuais,
        "data_fim": fim,
        "data_inicio": hoje,
    }
