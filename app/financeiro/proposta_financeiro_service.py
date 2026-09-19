# -*- coding: utf-8 -*-
"""Integracao financeira das propostas comerciais.

D25F03-A2

Responsabilidades:
- gerar recebiveis a partir das parcelas de proposta;
- manter rastreabilidade proposta/parcela;
- garantir idempotencia;
- preservar lancamentos ja quitados;
- nao decidir aprovacao da proposta;
- nao realizar commit proprio.
"""

from datetime import date, datetime
from decimal import Decimal, ROUND_HALF_UP

from app.extensoes import db
from app.financeiro.financeiro_model import LancamentoFinanceiro


CENTAVO = Decimal("0.01")
_STATUS_QUITADOS = {"pago", "recebido"}


def _decimal(valor):
    return Decimal(str(valor or 0)).quantize(
        CENTAVO,
        rounding=ROUND_HALF_UP,
    )


def _proposta_aprovada(proposta):
    return (
        str(getattr(proposta, "status", "") or "")
        .strip()
        .lower()
        == "aprovada"
    )


def _data_lancamento_proposta(proposta):
    aprovacao = getattr(
        proposta,
        "data_aprovacao",
        None,
    )

    if isinstance(aprovacao, datetime):
        return aprovacao.date()

    if isinstance(aprovacao, date):
        return aprovacao

    emissao = getattr(
        proposta,
        "data_emissao",
        None,
    )

    if isinstance(emissao, date):
        return emissao

    return date.today()


def _parcela_recebida(parcela):
    status = (
        str(getattr(parcela, "status", "") or "")
        .strip()
        .lower()
    )

    return (
        status in {"pago", "recebido"}
        or getattr(parcela, "data_pagamento", None)
        is not None
    )


def _descricao_parcela(
    proposta,
    parcela,
    total_normais,
):
    codigo = (
        getattr(proposta, "codigo", None)
        or f"PROP-{proposta.id}"
    )

    titulo = (
        getattr(proposta, "titulo", None)
        or "Proposta Comercial"
    )

    numero = int(
        getattr(parcela, "numero_parcela", 0)
        or 0
    )

    if numero == 0:
        prefixo = "Entrada"
    else:
        total = max(total_normais, numero)
        prefixo = f"Parcela {numero}/{total}"

    return f"{prefixo} {codigo} - {titulo}"


def _numero_parcela_exibicao(
    parcela,
    total_normais,
):
    numero = int(
        getattr(parcela, "numero_parcela", 0)
        or 0
    )

    if numero == 0:
        return "Entrada"

    return f"{numero}/{max(total_normais, numero)}"


def sincronizar_lancamentos_proposta(proposta):
    """Sincroniza parcelas ativas de uma proposta aprovada.

    A funcao deliberadamente NAO executa commit.
    O chamador controla a transacao.

    Propostas nao aprovadas nao geram recebiveis.
    """

    if not _proposta_aprovada(proposta):
        return []

    parcelas = sorted(
        [
            parcela
            for parcela in (
                getattr(
                    proposta,
                    "parcelas_pagamento",
                    [],
                )
                or []
            )
            if bool(
                getattr(
                    parcela,
                    "ativo",
                    True,
                )
            )
        ],
        key=lambda parcela: (
            int(
                getattr(
                    parcela,
                    "numero_parcela",
                    0,
                )
                or 0
            ),
            parcela.id or 0,
        ),
    )

    if not parcelas:
        return []

    ids_parcelas = [
        parcela.id
        for parcela in parcelas
        if parcela.id is not None
    ]

    existentes = (
        LancamentoFinanceiro.query
        .filter(
            LancamentoFinanceiro
            .proposta_parcela_id
            .in_(ids_parcelas)
        )
        .all()
    )

    existentes_por_parcela = {
        lancamento.proposta_parcela_id:
        lancamento
        for lancamento in existentes
    }

    total_normais = len(
        [
            parcela
            for parcela in parcelas
            if int(
                getattr(
                    parcela,
                    "numero_parcela",
                    0,
                )
                or 0
            ) > 0
        ]
    )

    resultado = []

    for parcela in parcelas:
        lancamento = existentes_por_parcela.get(
            parcela.id
        )

        if lancamento is None:
            lancamento = LancamentoFinanceiro(
                origem="PROPOSTA",
                proposta_id=proposta.id,
                proposta_parcela_id=parcela.id,
            )
            db.session.add(lancamento)

        # Recebimentos consolidados sao historico financeiro.
        # Uma edicao posterior da proposta nao pode reescrever
        # valor, vencimento ou baixa de um lancamento quitado.
        if (
            lancamento.id is not None
            and lancamento.status
            in _STATUS_QUITADOS
            and lancamento.data_pagamento
            is not None
        ):
            # Financeiro quitado e a fonte de verdade
            # para a parcela comercial correspondente.
            parcela.status = "recebido"
            parcela.data_pagamento = (
                lancamento.data_pagamento
            )

            resultado.append(lancamento)
            continue

        valor = _decimal(
            parcela.valor_parcela
        )

        recebida = _parcela_recebida(
            parcela
        )

        lancamento.descricao = (
            _descricao_parcela(
                proposta,
                parcela,
                total_normais,
            )
        )

        lancamento.valor = valor
        lancamento.valor_original = valor
        lancamento.tipo = "conta_receber"

        lancamento.status = (
            "recebido"
            if recebida
            else "pendente"
        )

        lancamento.categoria = "Servi?os"
        lancamento.subcategoria = (
            "Proposta Comercial"
        )

        lancamento.data_lancamento = (
            _data_lancamento_proposta(
                proposta
            )
        )

        lancamento.data_vencimento = (
            parcela.data_vencimento
        )

        lancamento.data_pagamento = (
            parcela.data_pagamento
            if recebida
            else None
        )

        lancamento.numero_documento = (
            proposta.codigo
        )

        lancamento.forma_pagamento = (
            proposta.forma_pagamento
        )

        lancamento.cliente_id = (
            proposta.cliente_id
        )

        lancamento.proposta_id = (
            proposta.id
        )

        lancamento.proposta_parcela_id = (
            parcela.id
        )

        lancamento.numero_parcela = (
            _numero_parcela_exibicao(
                parcela,
                total_normais,
            )
        )

        lancamento.observacoes = (
            "Lan?amento autom?tico da "
            f"{proposta.codigo}"
        )

        lancamento.origem = "PROPOSTA"
        lancamento.ativo = True

        resultado.append(lancamento)

    # Forca validacoes, FKs, unicidade e listeners,
    # mantendo o controle da transacao no chamador.
    db.session.flush()

    return resultado
