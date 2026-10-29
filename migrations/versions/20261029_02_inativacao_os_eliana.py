"""Inativação autorizada: OS20260087 (618) e recebimento indevido (224).

Revision ID: 20261029_02
Revises: 20261029_01

Escopo mínimo, auditado e falha fechada. NUNCA excluir OS, lançamento,
itens ou anexos. Não alterar contas bancárias, vínculos N:N ou extratos.
Autorização explícita do titular em 29/10/2026.
"""
from datetime import datetime, date
from decimal import Decimal

from alembic import op
import sqlalchemy as sa

revision = "20261029_02"
down_revision = "20261029_01"
branch_labels = None
depends_on = None

_AUTOR = "auditoria_assistida_os_eliana_20261029"
_MOTIVO = (
    "Conforme autorização expressa em 29/10/2026, OS20260087 (ID 618) "
    "reconhecida como ordem incorreta; recebimento automático ID 224 "
    "de R$ 600,00 sem conciliação bancária. Inativar ambos mantendo "
    "os documentos, itens, anexos, rastreabilidade e recebimentos legítimos "
    "da Eliana: OS20260101/fin139 R$800 e OS20260102/fin140 R$600. "
    "Não alterar o desembolso real de mão de obra ID165."
)


def _assert(cond, message):
    if not cond:
        raise RuntimeError("Inativação OS618/FIN224 abortada integralmente: " + message)


def _tabela(con, name):
    return sa.Table(name, sa.MetaData(), autoload_with=con)


def _uma(con, tabela, id):
    return con.execute(
        sa.select(tabela).where(tabela.c.id == id).with_for_update()
    ).mappings().one_or_none()


def _count_refs(con, tabela, coluna, id):
    return con.execute(
        sa.select(sa.func.count()).select_from(tabela).where(tabela.c[coluna] == id)
    ).scalar_one()


def _auditoria_financeira(con, now):
    h = _tabela(con, "historico_financeiro")
    con.execute(sa.insert(h).values(
        lancamento_id=224, campo_alterado="ativo",
        valor_anterior="ativo", valor_novo="inativo",
        usuario=_AUTOR, data_alteracao=now,
        acao="inativacao", motivo=_MOTIVO,
        criado_em=now, atualizado_em=now, ativo=True,
    ))


def _auditoria_os(con, now):
    auditoria = _tabela(con, "os_atividade_auditoria")
    con.execute(sa.insert(auditoria).values(
        ordem_servico_id=618, lancamento_id=224,
        campo_alterado="ativo",
        valor_anterior="ativo", valor_novo="inativo",
        usuario=_AUTOR, motivo=_MOTIVO,
        criado_em=now,
    ))


def _verificar_relacoes(con):
    insp = sa.inspect(con)
    # Toda FK real, inclusive sistemas implantados após esta versão.
    # Tabelas de serviço/arquivos são preservadas; qualquer outro vínculo
    # operacional/fiscal em 618 ou financeiro em 224 bloqueia tudo.
    aceitos_os = {
        ("lancamentos_financeiros", "ordem_servico_id"): 1,
        ("ordem_servico_itens", "ordem_servico_id"): 1,
        ("ordem_servico_anexos", "ordem_servico_id"): 6,
    }
    aceitos_fin = {
        ("historico_financeiro", "lancamento_id"): None,
        ("os_atividade_auditoria", "lancamento_id"): 0,
    }
    observados_os = {}
    observados_fin = {}
    for nome in insp.get_table_names():
        if nome == "alembic_version":
            continue
        for fk in insp.get_foreign_keys(nome):
            target = fk.get("referred_table")
            if target not in ("ordem_servico", "lancamentos_financeiros"):
                continue
            cols = fk.get("constrained_columns", [])
            _assert(fk.get("referred_columns") == ["id"] and len(cols) == 1,
                    f"FK complexa encontrada em {nome}")
            coluna = cols[0]
            tabela = _tabela(con, nome)
            if target == "ordem_servico":
                qtd = _count_refs(con, tabela, coluna, 618)
                observados_os[(nome, coluna)] = qtd
                esperado = aceitos_os.get((nome, coluna), 0)
                _assert(qtd == esperado,
                        f"vínculo com OS618 inesperado em {nome}.{coluna}: {qtd}")
            else:
                qtd = _count_refs(con, tabela, coluna, 224)
                observados_fin[(nome, coluna)] = qtd
                esperado = aceitos_fin.get((nome, coluna), 0)
                if esperado is not None:
                    _assert(qtd == esperado,
                            f"vínculo com financeiro224 em {nome}.{coluna}: {qtd}")
    for chave, n in aceitos_os.items():
        _assert(observados_os.get(chave, 0) == n,
                "dependência de OS618 ausente/alterada: " + str(chave))
    _assert(observados_fin.get(("historico_financeiro", "lancamento_id"), 0) == 0,
            "financeiro224 já tem histórico de edição; revisão manual necessária")


def _preflight(con):
    os = _tabela(con, "ordem_servico")
    financeiro = _tabela(con, "lancamentos_financeiros")
    ordem = _uma(con, os, 618)
    lanc = _uma(con, financeiro, 224)
    if ordem is None and lanc is None:
        return False  # Banco de teste novo, sem dados do cliente
    _assert(ordem is not None and lanc is not None, "alvo parcial/ausente")
    # Segunda execução idempotente só quando ambos já estão inativos.
    if ordem["ativo"] is False and lanc["ativo"] is False:
        return False
    _assert(ordem["ativo"] is True and lanc["ativo"] is True,
            "inativação parcial requer revisão humana")

    _assert(
        ordem["numero"] == "OS20260087"
        and ordem["titulo"] == "Reparo em Instalação Elétrica Predial"
        and ordem["cliente_id"] == 51
        and ordem["status"] == "concluida"
        and ordem["status_pagamento"] == "pago"
        and ordem["situacao_fiscal"] == "PENDENTE"
        and ordem["proposta_id"] is None
        and Decimal(str(ordem["valor_total"])) == Decimal("600.00"),
        "dados da OS618 mudaram",
    )
    _assert(
        lanc["descricao"] == "OS OS20260087 - Reparo em Instalação Elétrica Predial"
        and lanc["ordem_servico_id"] == 618
        and lanc["origem"] == "ORDEM_SERVICO"
        and lanc["tipo"] == "conta_receber"
        and lanc["status"] == "recebido"
        and lanc["cliente_id"] == 51
        and lanc["conta_bancaria_id"] == 1
        and lanc["sem_movimentacao_bancaria"] is False
        and lanc["data_pagamento"] == date(2026, 9, 8)
        and Decimal(str(lanc["valor"])) == Decimal("600.00"),
        "dados do financeiro224 mudaram",
    )

    # Recebimentos verdadeiros devem continuar integralmente conciliados.
    for id_os, id_fin, valor, id_ext, data in (
        (666, 139, Decimal("800.00"), 1, date(2026, 9, 11)),
        (667, 140, Decimal("600.00"), 51, date(2026, 9, 17)),
    ):
        outra = _uma(con, os, id_os)
        titulo = _uma(con, financeiro, id_fin)
        _assert(
            outra is not None and outra["ativo"] is True
            and outra["cliente_id"] == 51 and outra["status"] == "concluida"
            and titulo is not None and titulo["ativo"] is True
            and titulo["ordem_servico_id"] == id_os
            and titulo["status"] == "recebido"
            and Decimal(str(titulo["valor"])) == valor,
            f"OS/recebimento legítimo {id_os}/{id_fin} alterado",
        )
        ext = _uma(con, _tabela(con, "extratos_bancarios"), id_ext)
        _assert(
            ext is not None and ext["ativo"] is True and ext["conciliado"] is True
            and ext["lancamento_id"] == id_fin
            and ext["tipo_movimento"] == "credito"
            and ext["data_movimento"] == data
            and Decimal(str(ext["valor"])) == valor,
            f"extrato legítimo {id_ext} divergente",
        )
        nn = _tabela(con, "conciliacao_bancaria_itens")
        aloc = con.execute(sa.select(nn).where(
            nn.c.extrato_id == id_ext, nn.c.ativo.is_(True)
        ).with_for_update()).mappings().all()
        _assert(
            len(aloc) == 1 and aloc[0]["lancamento_id"] == id_fin
            and Decimal(str(aloc[0]["valor_conciliado"])) == valor,
            f"conciliação legítima {id_ext}/{id_fin} divergente",
        )
    real = _uma(con, financeiro, 165)
    _assert(
        real is not None and real["ativo"] is True
        and real["status"] == "pago"
        and Decimal(str(real["valor"])) == Decimal("600.00"),
        "desembolso real ao Luã (165) mudou",
    )
    _verificar_relacoes(con)
    return True


def upgrade():
    op.create_table(
        "os_atividade_auditoria",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("ordem_servico_id", sa.Integer(),
                  sa.ForeignKey("ordem_servico.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("lancamento_id", sa.Integer(),
                  sa.ForeignKey("lancamentos_financeiros.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("campo_alterado", sa.String(50), nullable=False),
        sa.Column("valor_anterior", sa.String(50), nullable=False),
        sa.Column("valor_novo", sa.String(50), nullable=False),
        sa.Column("usuario", sa.String(100), nullable=False),
        sa.Column("motivo", sa.Text(), nullable=False),
        sa.Column("criado_em", sa.DateTime(), nullable=False),
    )
    con = op.get_bind()
    if not _preflight(con):
        return

    now = datetime.utcnow()
    financeiro = _tabela(con, "lancamentos_financeiros")
    ordem = _tabela(con, "ordem_servico")
    fin_affected = con.execute(sa.update(financeiro).where(
        financeiro.c.id == 224,
        financeiro.c.ativo.is_(True),
    ).values(
        ativo=False, usuario_editor=_AUTOR,
        data_edicao_auditoria=now, atualizado_em=now,
    ))
    _assert(fin_affected.rowcount == 1, "financeiro224 não foi atualizado")
    os_affected = con.execute(sa.update(ordem).where(
        ordem.c.id == 618, ordem.c.ativo.is_(True)
    ).values(ativo=False, atualizado_em=now))
    _assert(os_affected.rowcount == 1, "OS618 não foi atualizada")
    _auditoria_financeira(con, now)
    _auditoria_os(con, now)


def downgrade():
    raise RuntimeError(
        "Reversão automática bloqueada: inativação financeira/OS auditada. "
        "Corrigir apenas mediante novo processo com autorização expressa."
    )
