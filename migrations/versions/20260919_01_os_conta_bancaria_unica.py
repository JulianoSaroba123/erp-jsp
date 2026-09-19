"""Vincula conta unica aos lancamentos de OS sem conta.

Revision ID: 20260919_01
Revises: 20260917_01
Create Date: 2026-09-19

A normalizacao e deliberadamente feita via SQL direto da migration. Assim,
lancamentos historicos ja recebidos ganham apenas o vinculo de conta e nao
disparam os listeners ORM de saldo bancario.
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260919_01"
down_revision = "20260917_01"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()

    contas_ativas = bind.execute(
        sa.text(
            """
            SELECT id
            FROM contas_bancarias
            WHERE ativo = :ativo
              AND ativa = :ativa
            ORDER BY id
            """
        ),
        {"ativo": True, "ativa": True},
    ).fetchall()

    # Regra de negocio D25F02-B1:
    # so existe escolha automatica quando ha exatamente uma conta ativa.
    if len(contas_ativas) != 1:
        return

    conta_id = contas_ativas[0][0]

    bind.execute(
        sa.text(
            """
            UPDATE lancamentos_financeiros
               SET conta_bancaria_id = :conta_id
             WHERE conta_bancaria_id IS NULL
               AND ativo = :ativo
               AND origem = 'ORDEM_SERVICO'
            """
        ),
        {"conta_id": conta_id, "ativo": True},
    )


def downgrade() -> None:
    # Data migration intencionalmente nao reversivel: depois do saneamento
    # nao e seguro distinguir vinculos historicos corrigidos de vinculos
    # definidos legitimamente pela operacao.
    pass
