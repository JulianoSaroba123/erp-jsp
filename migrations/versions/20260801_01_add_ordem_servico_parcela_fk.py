"""Add ordem_servico_parcela_id FK to lancamentos_financeiros

Revision ID: 20260801_01
Revises:
Create Date: 2026-08-01
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20260801_01"
down_revision = None
branch_labels = None
depends_on = None


def _parse_numero_parcela(numero_parcela: str | None) -> int | None:
    if not numero_parcela:
        return None
    texto = str(numero_parcela).strip()
    if not texto or "/" not in texto:
        return None
    esquerda = texto.split("/", 1)[0].strip()
    if not esquerda.isdigit():
        return None
    return int(esquerda)


def upgrade() -> None:
    with op.batch_alter_table("lancamentos_financeiros", recreate="auto") as batch_op:
        batch_op.add_column(sa.Column("ordem_servico_parcela_id", sa.Integer(), nullable=True))
        batch_op.create_index(
            "ix_lancamentos_financeiros_ordem_servico_parcela_id",
            ["ordem_servico_parcela_id"],
            unique=False,
        )

    bind = op.get_bind()

    rows = bind.execute(
        sa.text(
            """
            SELECT id, ordem_servico_id, numero_parcela
            FROM lancamentos_financeiros
            WHERE ordem_servico_id IS NOT NULL
              AND ordem_servico_parcela_id IS NULL
            """
        )
    ).fetchall()

    vinculados = 0
    ambiguos = 0
    sem_match = 0

    for row in rows:
        lancamento_id = row[0]
        ordem_servico_id = row[1]
        numero_parcela_txt = row[2]

        numero_parcela = _parse_numero_parcela(numero_parcela_txt)
        if numero_parcela is None:
            sem_match += 1
            continue

        parcelas = bind.execute(
            sa.text(
                """
                SELECT id
                FROM ordem_servico_parcelas
                WHERE ordem_servico_id = :ordem_servico_id
                  AND numero_parcela = :numero_parcela
                """
            ),
            {
                "ordem_servico_id": ordem_servico_id,
                "numero_parcela": numero_parcela,
            },
        ).fetchall()

        if len(parcelas) != 1:
            if len(parcelas) > 1:
                ambiguos += 1
            else:
                sem_match += 1
            continue

        parcela_id = parcelas[0][0]

        concorrentes = bind.execute(
            sa.text(
                """
                SELECT id
                FROM lancamentos_financeiros
                WHERE ordem_servico_id = :ordem_servico_id
                  AND numero_parcela = :numero_parcela_txt
                  AND ordem_servico_parcela_id IS NULL
                """
            ),
            {
                "ordem_servico_id": ordem_servico_id,
                "numero_parcela_txt": numero_parcela_txt,
            },
        ).fetchall()

        if len(concorrentes) != 1:
            ambiguos += 1
            continue

        ja_vinculado = bind.execute(
            sa.text(
                """
                SELECT id
                FROM lancamentos_financeiros
                WHERE ordem_servico_parcela_id = :parcela_id
                  AND id <> :lancamento_id
                """
            ),
            {"parcela_id": parcela_id, "lancamento_id": lancamento_id},
        ).fetchone()

        if ja_vinculado is not None:
            ambiguos += 1
            continue

        bind.execute(
            sa.text(
                """
                UPDATE lancamentos_financeiros
                SET ordem_servico_parcela_id = :parcela_id
                WHERE id = :lancamento_id
                """
            ),
            {"parcela_id": parcela_id, "lancamento_id": lancamento_id},
        )
        vinculados += 1

    with op.batch_alter_table("lancamentos_financeiros", recreate="auto") as batch_op:
        batch_op.create_foreign_key(
            "fk_lancamentos_financeiros_ordem_servico_parcela_id",
            "ordem_servico_parcelas",
            ["ordem_servico_parcela_id"],
            ["id"],
        )
        batch_op.create_unique_constraint(
            "uq_lancamentos_financeiros_ordem_servico_parcela_id",
            ["ordem_servico_parcela_id"],
        )

    print(
        "[MIGRATION 20260801_01] Backfill ordem_servico_parcela_id -> "
        f"vinculados={vinculados}, ambiguos={ambiguos}, sem_match={sem_match}"
    )


def downgrade() -> None:
    with op.batch_alter_table("lancamentos_financeiros", recreate="auto") as batch_op:
        batch_op.drop_constraint(
            "uq_lancamentos_financeiros_ordem_servico_parcela_id",
            type_="unique",
        )
        batch_op.drop_constraint(
            "fk_lancamentos_financeiros_ordem_servico_parcela_id",
            type_="foreignkey",
        )
        batch_op.drop_index("ix_lancamentos_financeiros_ordem_servico_parcela_id")
        batch_op.drop_column("ordem_servico_parcela_id")
