"""G5-F5: histórico aditivo dos checklists de geradores.

Revision ID: 20261015_01
Revises: 20261014_02

Requer as migrations F2/F3; não modifica tabelas legadas.
"""
from alembic import op
import sqlalchemy as sa

revision = "20261015_01"
down_revision = "20261014_02"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "gerador_checklist_eventos",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("execucao_id", sa.Integer(), nullable=False),
        sa.Column("sequencia", sa.Integer(), nullable=False),
        sa.Column("acao", sa.String(20), nullable=False),
        sa.Column("estado_resultante", sa.String(20), nullable=False),
        sa.Column("usuario_id", sa.Integer(), nullable=True),
        sa.Column("usuario_nome", sa.String(120), nullable=False),
        sa.Column("registrado_em", sa.DateTime(), nullable=False),
        sa.Column("sha256_respostas", sa.String(64), nullable=False),
        sa.Column("criado_em", sa.DateTime(), nullable=False),
        sa.Column("atualizado_em", sa.DateTime(), nullable=False),
        sa.Column("ativo", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.ForeignKeyConstraint(
            ["execucao_id"], ["gerador_checklist_execucoes.id"],
            name="fk_g5_evento_execucao", ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["usuario_id"], ["usuarios.id"],
            name="fk_g5_evento_usuario", ondelete="SET NULL",
        ),
        sa.UniqueConstraint(
            "execucao_id", "sequencia",
            name="uq_g5_evento_execucao_sequencia",
        ),
        sa.CheckConstraint(
            "sequencia > 0", name="ck_g5_evento_sequencia_positiva",
        ),
        sa.CheckConstraint(
            "acao IN ('CRIADO','RASCUNHO_SALVO','CONCLUIDO')",
            name="ck_g5_evento_acao",
        ),
    )
    op.create_index(
        "ix_gerador_checklist_eventos_execucao_id",
        "gerador_checklist_eventos", ["execucao_id"],
    )
    op.create_index(
        "ix_g5_evento_execucao_registrado",
        "gerador_checklist_eventos", ["execucao_id", "registrado_em"],
    )


def downgrade():
    if op.get_bind().execute(
        sa.text("SELECT COUNT(*) FROM gerador_checklist_eventos")
    ).scalar():
        raise RuntimeError(
            "Downgrade bloqueado: o histórico de manutenção não pode ser descartado."
        )
    op.drop_index(
        "ix_g5_evento_execucao_registrado",
        table_name="gerador_checklist_eventos",
    )
    op.drop_index(
        "ix_gerador_checklist_eventos_execucao_id",
        table_name="gerador_checklist_eventos",
    )
    op.drop_table("gerador_checklist_eventos")
