"""Reparo auditado da parcela 36 da OS20260107 (Wolney MWM).

Revision ID: 20261107_01
Revises: 20261029_02

Autorização: responsável solicitou corrigir de modo definitivo em 07/11/2026.
Reparo pontual da parcela de R$3.550 recebida em 05/11 e já conciliada
no movimento Cora #223. Não cria recebimento nem altera extrato/N:N.
Falha fechada se qualquer identidade, valor ou vínculo divergir.
Em bases de teste/vazias sem OS 672: nenhuma mutação.
"""
from datetime import datetime, date
from decimal import Decimal
from alembic import op
import sqlalchemy as sa

revision = "20261107_01"
down_revision = "20261029_02"
branch_labels = None
depends_on = None

DATA = date(2026, 11, 5)
VALOR = Decimal("3550.00")
MOTIVO = (
    "OS20260107 parcela #36 (R$ 3.550,00) recebida em 05/11/2026 "
    "no financeiro #336, conciliada com o extrato Cora #223 por N:N #222. "
    "Regularização exclusiva do marcador da parcela da OS e de "
    "status_pagamento para parcial, preservando parcela #37, recebimento "
    "financeiro e conciliações bancárias sem gerar crédito adicional."
)


def _assert(ok, msg):
    if not ok:
        raise RuntimeError("Reparo OS20260107 parcela36 abortado: " + msg)


def _row(con, tabela, chave):
    return con.execute(
        sa.text(f"SELECT * FROM {tabela} WHERE id=:id FOR UPDATE"),
        {"id": chave},
    ).mappings().one_or_none()


def _money(x):
    return Decimal(str(x or 0)).quantize(Decimal("0.01"))


def upgrade():
    con = op.get_bind()
    os_ = _row(con, "ordem_servico", 672)
    if os_ is None:
        return  # banco vazio/isolado; não tocar outros registros

    _assert(os_["numero"] == "OS20260107" and os_["ativo"], "OS incorreta/inativa")
    _assert(_money(os_["valor_total"]) == Decimal("7100.00"), "total OS divergente")
    _assert(os_["status_pagamento"] in ("pendente", "parcial"), "estado financeiro da OS divergente")

    parcelas = con.execute(sa.text(
        "SELECT id,numero_parcela,valor,pago,data_pagamento,ativo "
        "FROM ordem_servico_parcelas WHERE ordem_servico_id=672 "
        "ORDER BY id FOR UPDATE"
    )).mappings().all()
    _assert(len(parcelas) == 2 and [p["id"] for p in parcelas] == [36, 37], "parcelas inesperadas")
    p1,p2 = parcelas
    _assert(p1["numero_parcela"] == 1 and p2["numero_parcela"] == 2, "numeração divergente")
    _assert(p1["ativo"] and p2["ativo"], "parcela inativa")
    _assert(_money(p1["valor"]) == VALOR and _money(p2["valor"]) == VALOR, "valor parcela divergente")
    _assert(not p2["pago"] and p2["data_pagamento"] is None, "segunda parcela alterada")
    _assert(
        (not p1["pago"] and p1["data_pagamento"] is None)
        or (p1["pago"] and p1["data_pagamento"] == DATA),
        "primeira parcela conflitante",
    )

    f1 = _row(con, "lancamentos_financeiros", 336)
    f2 = _row(con, "lancamentos_financeiros", 337)
    _assert(f1 is not None and f2 is not None, "financeiro ausente")
    _assert(
        f1["ativo"] and f1["ordem_servico_id"] == 672
        and f1["ordem_servico_parcela_id"] == 36
        and f1["tipo"] == "conta_receber"
        and f1["status"] == "recebido"
        and f1["data_pagamento"] == DATA
        and _money(f1["valor"]) == VALOR,
        "primeiro título divergente",
    )
    _assert(
        f2["ativo"] and f2["ordem_servico_id"] == 672
        and f2["ordem_servico_parcela_id"] == 37
        and f2["tipo"] == "conta_receber"
        and f2["status"] == "pendente"
        and f2["data_pagamento"] is None
        and _money(f2["valor"]) == VALOR,
        "segundo título divergente",
    )

    extrato = _row(con, "extratos_bancarios", 223)
    _assert(extrato is not None and extrato["ativo"] and extrato["conciliado"], "extrato ausente/não conciliado")
    _assert(
        extrato["data_movimento"] == DATA
        and extrato["tipo_movimento"] == "credito"
        and _money(extrato["valor"]) == Decimal("9550.00"),
        "movimento bancário divergente",
    )
    itens = con.execute(sa.text(
        "SELECT id,lancamento_id,valor_conciliado,ativo "
        "FROM conciliacao_bancaria_itens WHERE extrato_id=223 "
        "ORDER BY id FOR UPDATE"
    )).mappings().all()
    ativos = [i for i in itens if i["ativo"]]
    _assert(
        len(ativos) == 2
        and {(i["lancamento_id"], _money(i["valor_conciliado"])) for i in ativos}
            == {(336,VALOR),(338,Decimal("6000.00"))},
        "alocações N:N inesperadas",
    )
    _assert(
        sum((_money(i["valor_conciliado"]) for i in ativos), Decimal("0.00"))
            == Decimal("9550.00"),
        "soma das alocações divergente",
    )
    outros = con.execute(sa.text(
        "SELECT COUNT(*) FROM conciliacao_bancaria_itens "
        "WHERE lancamento_id=336 AND ativo=true AND extrato_id<>223"
    )).scalar_one()
    _assert(outros == 0, "título conciliado em outro extrato")

    if p1["pago"]:
        _assert(os_["status_pagamento"] == "parcial", "parcela paga com status inconsistente")
        return  # idempotência sem duplicar auditoria

    result = con.execute(sa.text(
        "UPDATE ordem_servico_parcelas "
        "SET pago=true, data_pagamento=:data, atualizado_em=:agora "
        "WHERE id=36 AND ordem_servico_id=672 AND pago=false AND data_pagamento IS NULL"
    ), {"data": DATA, "agora": datetime.utcnow()})
    _assert(result.rowcount == 1, "parcela não atualizada exatamente uma vez")
    con.execute(sa.text(
        "UPDATE ordem_servico SET status_pagamento='parcial' WHERE id=672"
    ))
    agora = datetime.utcnow()
    con.execute(sa.text(
        "INSERT INTO historico_financeiro "
        "(lancamento_id,campo_alterado,valor_anterior,valor_novo,usuario,"
        "data_alteracao,acao,motivo,criado_em,atualizado_em,ativo) "
        "VALUES (336,'sincronizacao_os_parcela','pendente','recebida',"
        "'reparo_os20260107_parcela36',:agora,'sincronizacao',"
        ":motivo,:agora,:agora,true)"
    ), {"agora": agora, "motivo": MOTIVO})


def downgrade():
    raise RuntimeError(
        "Reversão automática bloqueada: baixa auditada e conciliada. "
        "Exige procedimento de estorno financeiro específico."
    )
