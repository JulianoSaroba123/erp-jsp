"""Checkpoint Cora comprovado e reparo estritamente condicionado do saldo legado.

Revision ID: 20261109_01
Revises: 20261107_01

Fonte externa: extrato oficial Cora 25/10 a 31/10/2026, saldo final R$ 3.282,73.
Fonte interna: extratos Cora 01/11 a 09/11, 40/40 conciliados,
entradas R$ 13.949,00 e saídas R$ 8.722,96.
NÃO cria receita/despesa, não edita lançamentos nem conciliações.
Falha FECHADA se a fotografia da produção tiver mudado.
"""
from datetime import date, datetime
from decimal import Decimal

from alembic import op
import sqlalchemy as sa


revision = "20261109_01"
down_revision = "20261107_01"
branch_labels = None
depends_on = None

CONTA_ID = 1
REFERENCIA = date(2026, 10, 31)
ULTIMO_MOVIMENTO = date(2026, 11, 9)
SALDO_REFERENCIA = Decimal("3282.73")
ENTRADAS = Decimal("13949.00")
SAIDAS = Decimal("8722.96")
SALDO_ALVO = Decimal("8508.77")
SALDO_ANTERIOR_ERP = Decimal("-24544.59")
FONTE = "Extrato oficial Cora 25/10/2026 a 31/10/2026, saldo final disponível"
MOTIVO = (
    "Reconciliação auditada: saldo Cora em 31/10/2026 R$ 3.282,73 "
    "+ créditos de novembro R$ 13.949,00 - débitos R$ 8.722,96 = "
    "R$ 8.508,77 em 09/11/2026. Corrige exclusivamente campo "
    "contas_bancarias.saldo_atual; não modifica histórico financeiro."
)


def _money(value):
    return Decimal(str(value or 0)).quantize(Decimal("0.01"))


def _assert(condition, description):
    if not condition:
        raise RuntimeError("Saldo Cora: regularização bloqueada - " + description)


def upgrade():
    op.create_table(
        "saldo_bancario_referencias",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("conta_bancaria_id", sa.Integer(), sa.ForeignKey("contas_bancarias.id"), nullable=False),
        sa.Column("data_referencia", sa.Date(), nullable=False),
        sa.Column("saldo_referencia", sa.Numeric(14, 2), nullable=False),
        sa.Column("fonte", sa.Text(), nullable=False),
        sa.Column("saldo_interno_anterior", sa.Numeric(14, 2), nullable=True),
        sa.Column("saldo_interno_reparado", sa.Numeric(14, 2), nullable=True),
        sa.Column("motivo", sa.Text(), nullable=False),
        sa.Column("criado_em", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("conta_bancaria_id", "data_referencia", name="uq_saldo_bancario_referencia_conta_data"),
    )

    connection = op.get_bind()
    conta = connection.execute(sa.text(
        "SELECT id,nome,banco,ativa,ativo,saldo_atual "
        "FROM contas_bancarias WHERE id=:id FOR UPDATE"
    ), {"id": CONTA_ID}).mappings().one_or_none()
    if conta is None:
        return  # Instância de testes/instalação sem Cora; tabela permanece vazia.

    _assert(
        conta["ativo"] is True and conta["ativa"] is True
        and "cora" in str(conta["nome"]).lower()
        and "cora" in str(conta["banco"]).lower(),
        "identidade da conta #1 divergente",
    )
    _assert(_money(conta["saldo_atual"]) == SALDO_ANTERIOR_ERP,
            "saldo interno mudou; faça novo checkpoint e auditoria antes de aplicar")

    resumo = connection.execute(sa.text(
        "SELECT count(*) AS total, "
        "count(*) FILTER (WHERE conciliado) AS conciliados, "
        "count(*) FILTER (WHERE NOT conciliado) AS pendentes, "
        "max(data_movimento) AS ultimo, "
        "COALESCE(sum(valor) FILTER (WHERE tipo_movimento='credito'),0) AS entradas, "
        "COALESCE(sum(valor) FILTER (WHERE tipo_movimento='debito'),0) AS saidas, "
        "count(*) FILTER (WHERE tipo_movimento NOT IN ('credito','debito')) AS tipos_invalidos "
        "FROM extratos_bancarios WHERE ativo=true AND conta_bancaria_id=:id "
        "AND data_movimento>:referencia"
    ), {"id": CONTA_ID, "referencia": REFERENCIA}).mappings().one()

    _assert(
        resumo["total"] == 40 and resumo["conciliados"] == 40
        and resumo["pendentes"] == 0 and resumo["ultimo"] == ULTIMO_MOVIMENTO
        and resumo["tipos_invalidos"] == 0
        and _money(resumo["entradas"]) == ENTRADAS
        and _money(resumo["saidas"]) == SAIDAS,
        "extratos mudaram desde 09/11; não aplicar saldo antigo",
    )
    _assert(SALDO_REFERENCIA + ENTRADAS - SAIDAS == SALDO_ALVO,
            "aritmética do checkpoint inconsistente")

    now = datetime.utcnow()
    inserted = connection.execute(sa.text(
        "INSERT INTO saldo_bancario_referencias "
        "(conta_bancaria_id,data_referencia,saldo_referencia,fonte,"
        "saldo_interno_anterior,saldo_interno_reparado,motivo,criado_em) "
        "VALUES (:id,:data,:saldo,:fonte,:anterior,:reparado,:motivo,:now)"
    ), dict(id=CONTA_ID,data=REFERENCIA,saldo=SALDO_REFERENCIA,
            fonte=FONTE,anterior=SALDO_ANTERIOR_ERP,
            reparado=SALDO_ALVO,motivo=MOTIVO,now=now))
    _assert(inserted.rowcount == 1, "referência não registrada")

    changed = connection.execute(sa.text(
        "UPDATE contas_bancarias SET saldo_atual=:alvo,atualizado_em=:now "
        "WHERE id=:id AND saldo_atual=:anterior"
    ), dict(alvo=SALDO_ALVO,now=now,id=CONTA_ID,anterior=SALDO_ANTERIOR_ERP))
    _assert(changed.rowcount == 1, "saldo mudou durante o reparo")
    _assert(_money(connection.execute(
        sa.text("SELECT saldo_atual FROM contas_bancarias WHERE id=:id"),
        {"id": CONTA_ID}).scalar_one()) == SALDO_ALVO,
        "saldo persistido diverge do checkpoint")


def downgrade():
    raise RuntimeError(
        "Reversão automática bloqueada: ajuste auditado do saldo Cora. "
        "Não reintroduzir valor historicamente inválido."
    )
