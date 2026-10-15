"""G5-F3: execuções de checklists digitais por vínculo OS-gerador.

Revision ID: 20261014_02
Revises: 20261014_01
"""
from alembic import op
import sqlalchemy as sa

revision = "20261014_02"
down_revision = "20261014_01"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "gerador_checklist_execucoes",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("vinculo_id", sa.Integer(), nullable=False),
        sa.Column("tipo_plano", sa.String(30), nullable=False),
        sa.Column("versao_catalogo", sa.String(30), nullable=False),
        sa.Column("estado", sa.String(20), nullable=False,
                  server_default="RASCUNHO"),
        sa.Column("data_servico", sa.Date(), nullable=True),
        sa.Column("modelo_snapshot", sa.JSON(), nullable=False),
        sa.Column("identificacao_snapshot", sa.JSON(), nullable=False),
        sa.Column("respostas_snapshot", sa.JSON(), nullable=False),
        sa.Column("observacoes_gerais", sa.Text(), nullable=True),
        sa.Column("criado_por_id", sa.Integer(), nullable=True),
        sa.Column("atualizado_por_id", sa.Integer(), nullable=True),
        sa.Column("concluido_por_id", sa.Integer(), nullable=True),
        sa.Column("concluido_em", sa.DateTime(), nullable=True),
        sa.Column("criado_em", sa.DateTime(), nullable=False),
        sa.Column("atualizado_em", sa.DateTime(), nullable=False),
        sa.Column("ativo", sa.Boolean(), nullable=False,
                  server_default=sa.true()),
        sa.ForeignKeyConstraint(
            ["vinculo_id"], ["gerador_os_vinculos.id"],
            name="fk_gerador_checklist_vinculo", ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["criado_por_id"], ["usuarios.id"],
            name="fk_gerador_checklist_criador", ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["atualizado_por_id"], ["usuarios.id"],
            name="fk_gerador_checklist_atualizador", ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["concluido_por_id"], ["usuarios.id"],
            name="fk_gerador_checklist_finalizador", ondelete="SET NULL",
        ),
        sa.UniqueConstraint(
            "vinculo_id", "tipo_plano",
            name="uq_gerador_checklist_vinculo_tipo",
        ),
        sa.CheckConstraint(
            "tipo_plano IN ('BASICA','INTERMEDIARIA','AVANCADA')",
            name="ck_gerador_checklist_tipo",
        ),
        sa.CheckConstraint(
            "estado IN ('RASCUNHO','CONCLUIDO')",
            name="ck_gerador_checklist_estado",
        ),
    )
    op.create_index(
        "ix_gerador_checklist_execucoes_vinculo_id",
        "gerador_checklist_execucoes", ["vinculo_id"],
    )
    op.create_index(
        "ix_gerador_checklist_execucoes_estado",
        "gerador_checklist_execucoes", ["estado"],
    )
    op.create_index(
        "ix_gerador_checklist_execucoes_vinculo_estado",
        "gerador_checklist_execucoes", ["vinculo_id", "estado"],
    )


def downgrade():
    bind = op.get_bind()
    existentes = bind.execute(
        sa.text("SELECT COUNT(*) FROM gerador_checklist_execucoes")
    ).scalar()
    if existentes:
        raise RuntimeError(
            "Downgrade bloqueado: checklists existentes devem ser preservados."
        )
    op.drop_index(
        "ix_gerador_checklist_execucoes_vinculo_estado",
        table_name="gerador_checklist_execucoes",
    )
    op.drop_index(
        "ix_gerador_checklist_execucoes_estado",
        table_name="gerador_checklist_execucoes",
    )
    op.drop_index(
        "ix_gerador_checklist_execucoes_vinculo_id",
        table_name="gerador_checklist_execucoes",
    )
    op.drop_table("gerador_checklist_execucoes")
