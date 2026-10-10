# -*- coding: utf-8 -*-
"""Conciliação documental comercial, exclusivamente leitura.

A presença de vínculo é evidência de rastreabilidade, não de quitação.
Ausência de vínculo não é prova de inadimplência e nunca autoriza cobrança.
Não executa flush, commit, rollback ou qualquer escrita.
"""
from collections import defaultdict
from decimal import Decimal, InvalidOperation
from math import ceil

LIMITE_DOCUMENTOS = 5000
SITUACOES = {"todas", "revisar", "vinculado", "em_andamento"}
TIPOS = {"todos", "proposta", "pedido", "os"}


def dinheiro(valor):
    try:
        numero = Decimal(str(valor or 0)).quantize(Decimal("0.01"))
    except (InvalidOperation, ValueError, TypeError):
        numero = Decimal("0.00")
    return numero


def formato_brl(valor):
    numero = dinheiro(valor)
    return ("R$ " + f"{numero:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))


def _ativo(registro):
    return getattr(registro, "ativo", True) is not False


def _nome_cliente(registro):
    cliente = getattr(registro, "cliente", None)
    return str(getattr(cliente, "nome", None) or getattr(cliente, "nome_exibicao", None) or "Cliente não identificado")


def _status(registro):
    return str(getattr(registro, "status", "") or "").strip().lower()


def _links_unicos(*colecoes):
    return list({l.id: l for colecao in colecoes for l in colecao if getattr(l, "id", None) is not None}.values())


def _resumo_vinculos(lancamentos):
    return {
        "ids": sorted(l.id for l in lancamentos),
        "total": sum((dinheiro(l.valor) for l in lancamentos), Decimal("0.00")),
        "recebido": sum(
            (dinheiro(l.valor) for l in lancamentos
             if _status(l) in {"recebido", "pago"} and getattr(l, "data_pagamento", None)),
            Decimal("0.00"),
        ),
        "status": sorted({_status(l) for l in lancamentos if _status(l)}),
    }


def _candidatos_manuais(codigo, cliente_id, lancamentos):
    """Sinal de conferência; nunca assume que um documento foi pago."""
    return [
        l.id for l in lancamentos
        if getattr(l, "pedido_id", None) is None
        and getattr(l, "proposta_id", None) is None
        and getattr(l, "ordem_servico_id", None) is None
        and str(getattr(l, "numero_documento", "") or "").strip().casefold()
           == str(codigo).strip().casefold()
        and getattr(l, "cliente_id", None) == cliente_id
    ]


def montar_conciliacao(propostas, pedidos, ordens, lancamentos, parcelas=(),
                       *, tipo="todos", situacao="todas", busca="", pagina=1,
                       por_pagina=25):
    """Processa objetos já consultados; função pura para teste sem banco."""
    tipo = tipo if tipo in TIPOS else "todos"
    situacao = situacao if situacao in SITUACOES else "todas"
    busca = str(busca or "").strip().casefold()[:100]
    try:
        pagina = max(1, int(pagina))
    except (ValueError, TypeError):
        pagina = 1
    por_pagina = 25  # tamanho fixo: bloqueia abusos por parâmetro

    propostas = [p for p in propostas if _ativo(p)]
    pedidos = [p for p in pedidos if _ativo(p)]
    ordens = [o for o in ordens if _ativo(o)]
    financeiros = [
        l for l in lancamentos if _ativo(l)
        and getattr(l, "tipo", None) == "conta_receber"
        and _status(l) != "cancelado"
    ]

    por_prop = defaultdict(list)
    por_pedido = defaultdict(list)
    por_os = defaultdict(list)
    ordens_da_prop = defaultdict(list)
    pedidos_da_prop = defaultdict(list)
    parcelas_da_prop = defaultdict(list)
    for parcela in parcelas:
        if _ativo(parcela):
            parcelas_da_prop[getattr(parcela, "proposta_id", None)].append(parcela)
    for os in ordens:
        if os.proposta_id is not None:
            ordens_da_prop[os.proposta_id].append(os)
    for ped in pedidos:
        if ped.proposta_id is not None:
            pedidos_da_prop[ped.proposta_id].append(ped)
    for l in financeiros:
        if l.proposta_id is not None:
            por_prop[l.proposta_id].append(l)
        if l.pedido_id is not None:
            por_pedido[l.pedido_id].append(l)
        if l.ordem_servico_id is not None:
            por_os[l.ordem_servico_id].append(l)

    proposta_index = {p.id: p for p in propostas}
    todos = []

    def acrescentar(tipo_doc, documento, *, vinculos, situacao_nome,
                    observacao, alerta, relacionados=None):
        identificador = (
            documento.codigo if tipo_doc == "proposta" else documento.numero
        )
        resumo = _resumo_vinculos(vinculos)
        cliente_id = getattr(documento, "cliente_id", None)
        todos.append({
            "tipo": tipo_doc,
            "id": documento.id,
            "codigo": identificador,
            "cliente": _nome_cliente(documento),
            "cliente_id": cliente_id,
            "status": _status(documento),
            "valor": dinheiro(getattr(documento, "valor_total", 0)),
            "financeiro": resumo,
            "situacao": situacao_nome,
            "observacao": observacao,
            "alerta": alerta,
            "relacionados": relacionados or [],
            "candidatos_manuais": _candidatos_manuais(
                identificador, cliente_id, financeiros
            ),
        })

    for p in propostas:
        os_associadas = ordens_da_prop[p.id]
        pedidos_associados = pedidos_da_prop[p.id]
        vinculos = _links_unicos(
            por_prop[p.id],
            *(por_os[o.id] for o in os_associadas),
        )
        aprovado = _status(p) == "aprovada"
        precisa = aprovado and dinheiro(p.valor_total) > 0
        sem = precisa and not vinculos
        obs = "Recebíveis diretamente vinculados à proposta ou à OS associada."
        if sem:
            obs = "Sem vínculo financeiro identificável. Conferir pagamentos manuais e histórico antes de lançar."
            if not parcelas_da_prop[p.id]:
                obs += " Também não há parcelas financeiras cadastradas."
        elif not aprovado:
            obs = "Proposta não aprovada: não exige recebível automático."
        acrescentar(
            "proposta", p, vinculos=vinculos,
            situacao_nome="revisar" if sem else ("vinculado" if vinculos else "em_andamento"),
            observacao=obs, alerta=sem,
            relacionados=(
                [("Pedido", x.numero, "pedido", x.id) for x in pedidos_associados]
                + [("OS", x.numero, "os", x.id) for x in os_associadas]
            ),
        )

    for ped in pedidos:
        vinculos_diretos = por_pedido[ped.id]
        if ped.proposta_id is not None:
            p = proposta_index.get(ped.proposta_id)
            da_proposta = por_prop[ped.proposta_id]
            das_os = _links_unicos(
                *(por_os[o.id] for o in ordens_da_prop[ped.proposta_id])
            )
            vinculos = _links_unicos(vinculos_diretos, da_proposta, das_os)
            dupla_origem = bool(vinculos_diretos and (da_proposta or das_os))
            nome = "revisar" if dupla_origem else (
                "vinculado" if vinculos else "em_andamento"
            )
            obs = (
                "Pedido vinculado à proposta; a origem do recebível é a proposta. "
                "Não gerar nova conta a receber pelo pedido."
            )
            if dupla_origem:
                obs = "Recebíveis tanto pelo pedido quanto pela proposta/OS. Conferir possível duplicidade."
            relacionados = [("Proposta", p.codigo, "proposta", p.id)] if p else []
        else:
            vinculos = list(vinculos_diretos)
            sem = _status(ped) == "concluido" and dinheiro(ped.valor_total) > 0 and not vinculos
            nome = "revisar" if sem else (
                "vinculado" if vinculos else "em_andamento"
            )
            obs = (
                "Pedido direto concluído sem recebível vinculado. Conferir antes de lançar."
                if sem else "Pedido direto: gera recebível ao concluir, não ao confirmar."
            )
            relacionados = []
        acrescentar(
            "pedido", ped, vinculos=vinculos, situacao_nome=nome,
            observacao=obs, alerta=(nome == "revisar"),
            relacionados=relacionados,
        )

    for os in ordens:
        vinculos_diretos = por_os[os.id]
        p = proposta_index.get(os.proposta_id)
        financeiros_proposta = por_prop[os.proposta_id] if p else []
        vinculos = _links_unicos(vinculos_diretos, financeiros_proposta)
        concluida = _status(os) in {"concluida", "finalizada"}
        comercial = str(getattr(os, "tipo_os", "comercial") or "comercial").lower() != "operacional"
        sem = concluida and comercial and dinheiro(os.valor_total) > 0 and not vinculos
        nome = "revisar" if sem else ("vinculado" if vinculos else "em_andamento")
        if not comercial:
            obs = "OS operacional: não tratar como cobrança automática."
        elif sem:
            obs = "OS comercial concluída sem recebível vinculado. Conferir histórico e lançamentos manuais."
        elif p:
            obs = "OS originada da proposta; conferir recebíveis na proposta e vínculo na OS."
        else:
            obs = "OS direta: o saldo pendente deve entrar no financeiro na conclusão."
        relacionados = [("Proposta", p.codigo, "proposta", p.id)] if p else []
        acrescentar(
            "os", os, vinculos=vinculos, situacao_nome=nome,
            observacao=obs, alerta=sem, relacionados=relacionados,
        )

    totais = {
        "propostas_revisar": sum(r["alerta"] for r in todos if r["tipo"] == "proposta"),
        "pedidos_revisar": sum(r["alerta"] for r in todos if r["tipo"] == "pedido"),
        "os_revisar": sum(r["alerta"] for r in todos if r["tipo"] == "os"),
        "documentos": len(todos),
    }

    filtrados = [
        r for r in todos
        if (tipo == "todos" or r["tipo"] == tipo)
        and (situacao == "todas" or r["situacao"] == situacao)
        and (
            not busca or busca in (
                r["codigo"] + " " + r["cliente"] + " " + r["status"]
            ).casefold()
        )
    ]
    # Documentos a conferir primeiro e ordem estável para paginação.
    filtrados.sort(key=lambda r: (
        0 if r["situacao"] == "revisar" else 1,
        {"proposta": 0, "pedido": 1, "os": 2}[r["tipo"]],
        -r["id"],
    ))
    paginas = max(1, ceil(len(filtrados) / por_pagina))
    pagina = min(pagina, paginas)
    inicio = (pagina - 1) * por_pagina
    return {
        "linhas": filtrados[inicio:inicio + por_pagina],
        "total_filtrado": len(filtrados),
        "pagina": pagina,
        "paginas": paginas,
        "tipo": tipo,
        "situacao": situacao,
        "busca": busca,
        "totais": totais,
    }


def consultar_conciliacao(*, tipo="todos", situacao="todas", busca="", pagina=1):
    """Acesso ORM somente leitura, sem transações de escrita."""
    from sqlalchemy.orm import joinedload
    from app.extensoes import db
    from app.proposta.proposta_model import Proposta, ParcelaProposta
    from app.pedido.pedido_model import Pedido
    from app.ordem_servico.ordem_servico_model import OrdemServico
    from app.financeiro.financeiro_model import LancamentoFinanceiro

    # O limite é de segurança; não publicar números parciais silenciosamente.
    documentos = [
        (Proposta, "propostas"),
        (Pedido, "pedidos"),
        (OrdemServico, "OS"),
    ]
    for model, nome in documentos:
        total = db.session.query(model.id).filter(model.ativo.is_(True)).count()
        if total > LIMITE_DOCUMENTOS:
            raise RuntimeError(
                f"Existem {total} {nome}; a versão atual do painel limita "
                f"a consulta a {LIMITE_DOCUMENTOS}. Não foram calculados "
                "totais incompletos."
            )

    propostas = (Proposta.query.options(joinedload(Proposta.cliente))
                 .filter(Proposta.ativo.is_(True)).all())
    pedidos = (Pedido.query.options(joinedload(Pedido.cliente))
               .filter(Pedido.ativo.is_(True)).all())
    ordens = (OrdemServico.query.options(joinedload(OrdemServico.cliente))
              .filter(OrdemServico.ativo.is_(True)).all())
    financeiros = (LancamentoFinanceiro.query
                   .filter(LancamentoFinanceiro.ativo.is_(True),
                           LancamentoFinanceiro.tipo == "conta_receber").all())
    parcelas = (ParcelaProposta.query
                .filter(ParcelaProposta.ativo.is_(True)).all())
    return montar_conciliacao(
        propostas, pedidos, ordens, financeiros, parcelas,
        tipo=tipo, situacao=situacao, busca=busca, pagina=pagina,
    )
