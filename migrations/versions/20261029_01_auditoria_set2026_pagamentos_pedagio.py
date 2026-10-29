"""Regularização autorizada de setembro/2026: títulos duplicados e data de pedágio.

Revision ID: 20261029_01
Revises: 20261028_01

Migração de dados restrita à assinatura exata dos 7 lançamentos e aos extratos
já conciliados. Falha fechada se algum estado divergir. Preserva o banco,
as conciliações N:N, os títulos legítimos e o histórico.
Autorização do responsável: 29/10/2026, auditoria setembro/2026.
"""
from datetime import date, datetime
from decimal import Decimal

from alembic import op
import sqlalchemy as sa

revision = "20261029_01"
down_revision = "20261028_01"
branch_labels = None
depends_on = None

_AUTOR = "auditoria_assistida_autorizada_20261029"
_DUPLICADOS = {
    99: ("Diária de auxiliar — Juliano Fraga Pereira — serviços gerais", "conta_pagar", Decimal("100.00"), date(2026, 9, 9)),
    123: ("Pagamento de auxiliar - Luã - Serviço MARPA", "despesa", Decimal("200.00"), date(2026, 9, 11)),
    141: ("PAGAMENTO DIARIA - AUXILIAR LUÃ", "despesa", Decimal("400.00"), date(2026, 9, 11)),
    142: ("PAGAMENTO DIÁRIAS - AUXILIAR JULIANO FRAGA", "despesa", Decimal("400.00"), date(2026, 9, 11)),
}
_CORRETOS = {
    165: ("Pagamento de mão de obra Luã – OS20260087 – Eliana Saroba", "conta_pagar", Decimal("600.00"), date(2026, 9, 11)),
    166: ("Pagamento de serviços prestados Juliano Fraga", "conta_pagar", Decimal("500.00"), date(2026, 9, 11)),
}
_PEDAGIO = (182, "Pagamento de pedágio em deslocamento", Decimal("20.40"))
_DATA_ERRADA = date(26, 2, 9)
_DATA_CORRETA = date(2026, 9, 9)

_FIN = sa.table(
    "lancamentos_financeiros",
    sa.column("id", sa.Integer), sa.column("descricao", sa.String),
    sa.column("valor", sa.Numeric(12, 2)), sa.column("tipo", sa.String),
    sa.column("status", sa.String), sa.column("origem", sa.String),
    sa.column("ativo", sa.Boolean), sa.column("data_lancamento", sa.Date),
    sa.column("data_pagamento", sa.Date), sa.column("data_vencimento", sa.Date),
    sa.column("conta_bancaria_id", sa.Integer),
    sa.column("ordem_servico_id", sa.Integer),
    sa.column("ordem_servico_parcela_id", sa.Integer),
    sa.column("proposta_id", sa.Integer), sa.column("proposta_parcela_id", sa.Integer),
    sa.column("pedido_id", sa.Integer), sa.column("custo_fixo_id", sa.Integer),
    sa.column("usuario_editor", sa.String), sa.column("data_edicao_auditoria", sa.DateTime),
    sa.column("atualizado_em", sa.DateTime),
)
_EXT = sa.table(
    "extratos_bancarios",
    sa.column("id", sa.Integer), sa.column("lancamento_id", sa.Integer),
    sa.column("valor", sa.Numeric(12, 2)), sa.column("tipo_movimento", sa.String),
    sa.column("data_movimento", sa.Date), sa.column("ativo", sa.Boolean),
    sa.column("conciliado", sa.Boolean),
)
_NN = sa.table(
    "conciliacao_bancaria_itens",
    sa.column("id", sa.Integer), sa.column("lancamento_id", sa.Integer),
    sa.column("extrato_id", sa.Integer), sa.column("valor_conciliado", sa.Numeric(12, 2)),
    sa.column("ativo", sa.Boolean),
)
_HIST = sa.table(
    "historico_financeiro",
    sa.column("lancamento_id", sa.Integer), sa.column("campo_alterado", sa.String),
    sa.column("valor_anterior", sa.Text), sa.column("valor_novo", sa.Text),
    sa.column("usuario", sa.String), sa.column("data_alteracao", sa.DateTime),
    sa.column("acao", sa.String), sa.column("motivo", sa.Text),
    sa.column("criado_em", sa.DateTime), sa.column("atualizado_em", sa.DateTime),
    sa.column("ativo", sa.Boolean),
)


def _exigir(condicao, mensagem):
    if not condicao:
        raise RuntimeError("Auditoria set/2026 abortada sem alterações: " + mensagem)


def _auditar(con, now, lancamento_id, campo, anterior, novo, acao, motivo):
    con.execute(
        sa.insert(_HIST).values(
            lancamento_id=lancamento_id, campo_alterado=campo,
            valor_anterior=str(anterior), valor_novo=str(novo),
            usuario=_AUTOR, data_alteracao=now, acao=acao,
            motivo=motivo, criado_em=now, atualizado_em=now, ativo=True,
        )
    )


def _preflight(con):
    todos = set(_DUPLICADOS) | set(_CORRETOS) | {_PEDAGIO[0]}
    registros = {
        r["id"]: r for r in con.execute(
            sa.select(_FIN).where(_FIN.c.id.in_(sorted(todos))).with_for_update()
        ).mappings()
    }
    # Migração de estrutura em ambiente vazio: nenhuma alteração de dados.
    if not registros:
        return None
    _exigir(set(registros) == todos, "conjunto parcial de IDs; verificar ambiente/dados")

    # Aplicação repetida somente é aceita quando TODO o conjunto foi concluído.
    ja_corrigido = all(not registros[i]["ativo"] for i in _DUPLICADOS)
    ja_corrigido &= all(
        registros[182][campo] == _DATA_CORRETA
        for campo in ("data_lancamento", "data_vencimento", "data_pagamento")
    )
    if ja_corrigido:
        _exigir(
            all(r["ativo"] and r["status"] == "pago" for i, r in registros.items() if i in _CORRETOS),
            "títulos legítimos mudaram após correção",
        )
        return False

    for i, (descricao, tipo, valor, data_pgto) in {**_DUPLICADOS, **_CORRETOS}.items():
        r = registros[i]
        _exigir(r["descricao"] == descricao, f"descrição alterada no ID {i}")
        _exigir(r["tipo"] == tipo and Decimal(str(r["valor"])) == valor, f"valor/tipo alterado no ID {i}")
        _exigir(r["status"] == "pago" and r["ativo"] is True, f"status/atividade alterado no ID {i}")
        _exigir(r["data_pagamento"] == data_pgto, f"data de quitação alterada no ID {i}")
        _exigir((r["origem"] or "MANUAL").strip().upper() == "MANUAL", f"origem integrada no ID {i}")
        if i in _DUPLICADOS:
            for campo in ("ordem_servico_id", "ordem_servico_parcela_id", "proposta_id",
                          "proposta_parcela_id", "pedido_id", "custo_fixo_id"):
                _exigir(r[campo] is None, f"vínculo direto {campo} no ID {i}")

    r = registros[182]
    _exigir(r["descricao"] == _PEDAGIO[1] and Decimal(str(r["valor"])) == _PEDAGIO[2],
            "assinatura do pedágio ID 182 alterada")
    _exigir(r["ativo"] is True and r["status"] == "pago" and r["tipo"] == "despesa",
            "situação do pedágio alterada")
    for campo in ("data_lancamento", "data_vencimento", "data_pagamento"):
        _exigir(r[campo] == _DATA_ERRADA, f"data {campo} divergente no ID 182")

    # Mesmo critério da inativação regular: nenhum vínculo externo, ativo ou histórico.
    inspector = sa.inspect(con)
    for nome in ("conciliacao_bancaria_itens", "extratos_bancarios", "notas_fiscais",
                 "notas_fiscais_servico", "os_custos_internos", "rateios_despesas"):
        if not inspector.has_table(nome):
            continue
        tabela = sa.table(nome, sa.column("lancamento_id", sa.Integer))
        vinculo = con.execute(sa.select(tabela.c.lancamento_id).where(
            tabela.c.lancamento_id.in_(sorted(_DUPLICADOS))
        ).limit(1)).first()
        _exigir(vinculo is None, f"referência externa em {nome}")

    # Os pagamentos de R$ 600 e R$ 500 e o pedágio devem permanecer conciliados.
    extratos = {
        r["id"]: r for r in con.execute(
            sa.select(_EXT).where(_EXT.c.id.in_([2, 3, 15])).with_for_update()
        ).mappings()
    }
    esperado = {
        2: (166, Decimal("500.00"), date(2026, 9, 11)),
        3: (165, Decimal("600.00"), date(2026, 9, 11)),
        15: (182, Decimal("20.40"), date(2026, 9, 9)),
    }
    _exigir(set(extratos) == set(esperado), "extratos legítimos não localizados")
    for i, (lid, valor, data) in esperado.items():
        e = extratos[i]
        _exigir(
            e["ativo"] is True and e["conciliado"] is True and
            e["lancamento_id"] == lid and e["data_movimento"] == data and
            e["tipo_movimento"] == "debito" and Decimal(str(e["valor"])) == valor,
            f"extrato {i} mudou; não é seguro continuar",
        )
    vinculos = con.execute(
        sa.select(_NN).where(_NN.c.extrato_id.in_([2, 3, 15]),
                             _NN.c.ativo.is_(True)).with_for_update()
    ).mappings().all()
    alocacoes = {(r["extrato_id"], r["lancamento_id"]): Decimal(str(r["valor_conciliado"]))
                 for r in vinculos}
    _exigir(
        len(vinculos) == 3 and alocacoes == {
            (2, 166): Decimal("500.00"),
            (3, 165): Decimal("600.00"),
            (15, 182): Decimal("20.40"),
        },
        "alocações N:N legítimas divergentes",
    )
    return True


def upgrade():
    con = op.get_bind()
    if _preflight(con) is not True:
        return
    now = datetime.utcnow()
    motivo_base = (
        "Autorização do responsável em 29/10/2026: em 11/09/2026 houve somente "
        "R$ 600,00 para Luã e R$ 500,00 para Juliano Fraga, registrados nos "
        "financeiros 165 e 166 e conciliados aos extratos 3 e 2. "
        "Duplicidade gerencial sem novo desembolso; preservar os títulos originais."
    )
    for i in sorted(_DUPLICADOS):
        alterado = con.execute(
            sa.update(_FIN).where(_FIN.c.id == i, _FIN.c.ativo.is_(True))
            .values(ativo=False, usuario_editor=_AUTOR,
                    data_edicao_auditoria=now, atualizado_em=now)
        )
        _exigir(alterado.rowcount == 1, f"falha ao inativar ID {i}")
        _auditar(con, now, i, "ativo", "ativo", "inativo", "inativacao",
                 motivo_base + f" Lançamento duplicado ID {i}: R$ {_DUPLICADOS[i][2]:.2f}.")
    alterado = con.execute(
        sa.update(_FIN).where(_FIN.c.id == _PEDAGIO[0], _FIN.c.ativo.is_(True))
        .values(data_lancamento=_DATA_CORRETA, data_vencimento=_DATA_CORRETA,
                data_pagamento=_DATA_CORRETA, usuario_editor=_AUTOR,
                data_edicao_auditoria=now, atualizado_em=now)
    )
    _exigir(alterado.rowcount == 1, "falha ao corrigir pedágio ID 182")
    for campo in ("data_lancamento", "data_vencimento", "data_pagamento"):
        _auditar(con, now, 182, campo, _DATA_ERRADA.isoformat(),
                 _DATA_CORRETA.isoformat(), "edicao",
                 "Correção autorizada de erro de digitação no pedágio SPVIAS, "
                 "extrato Cora 15 de 09/09/2026; sem alteração de valor, saldo ou conciliação.")


def downgrade():
    raise RuntimeError(
        "Reversão automática de auditoria financeira bloqueada. "
        "Revisão humana necessária para preservar eventos e conciliações."
    )
