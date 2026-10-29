"""Visibilidade das sugestões no cockpit de conciliação bancária.

Apenas apresentação da lista: nunca altera lançamentos financeiros, status,
competências contábeis, contas a pagar, extratos ou vínculos N:N.

Exceção solicitada pelo responsável em 29/10/2026:
na conta Cora (ID 1), ao conciliar movimentos bancários de outubro/2026,
não sugerir automaticamente os quatro lançamentos legados IDs 94, 96,
100 e 101. Eles continuam intactos e consultáveis no Financeiro; o
operador pode revelá-los temporariamente com "Mostrar sugestões ocultas".

A seleção é por competência DO EXTRATO, não pela data de lançamento
ou vencimento do título: uma dívida de setembro legitimamente paga em
outubro continua elegível se não estiver explicitamente nesta exceção.
"""

# (conta bancária, mês da movimentação bancária) -> ids excluídos da sugestão
_OCULTACOES_POR_COMPETENCIA = {
    (1, "2026-10"): frozenset({94, 96, 100, 101}),
}


def sugestoes_ocultas_por_lancamento(conta_id, lancamentos):
    """Retorna {id_financeiro: 'AAAA-MM[,AAAA-MM]'} somente para exibição.

    Não altera o resultado de conciliação no servidor e não bloqueia a
    seleção manual se o usuário optar por mostrar os registros.
    """
    ids_presentes = {int(l.id) for l in lancamentos}
    mapa = {}
    if conta_id is None:
        return mapa
    for (conta_oculta, competencia), ids in _OCULTACOES_POR_COMPETENCIA.items():
        if int(conta_id) != conta_oculta:
            continue
        for lancamento_id in sorted(ids & ids_presentes):
            mapa.setdefault(lancamento_id, []).append(competencia)
    return {
        lancamento_id: ",".join(sorted(competencias))
        for lancamento_id, competencias in mapa.items()
    }
