"""G5-F2 - vínculo seguro entre ordem de serviço e geradores

Revision ID: 20261014_01
Revises: cdbaf09054ac

Cria somente tabela nova. Nenhuma OS/gerador é modificado.
"""
from alembic import op
import sqlalchemy as sa

revision = "20261014_01"
down_revision = "cdbaf09054ac"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "gerador_os_vinculos",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("ordem_servico_id", sa.Integer(), nullable=False),
        sa.Column("gerador_id", sa.Integer(), nullable=False),
        sa.Column("criado_por_id", sa.Integer(), nullable=True),
        sa.Column("criado_em", sa.DateTime(), nullable=False),
        sa.Column("atualizado_em", sa.DateTime(), nullable=False),
        sa.Column("ativo", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.ForeignKeyConstraint(
            ["ordem_servico_id"], ["ordem_servico.id"],
            name="fk_gerador_os_vinculos_os", ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["gerador_id"], ["geradores.id"],
            name="fk_gerador_os_vinculos_gerador", ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["criado_por_id"], ["usuarios.id"],
            name="fk_gerador_os_vinculos_usuario", ondelete="SET NULL",
        ),
        sa.UniqueConstraint(
            "ordem_servico_id", "gerador_id",
            name="uq_gerador_os_vinculo_par",
        ),
        sa.CheckConstraint(
            "ordem_servico_id > 0 AND gerador_id > 0",
            name="ck_gerador_os_vinculos_ids_positivos",
        ),
    )
    op.create_index(
        "ix_gerador_os_vinculos_ordem_servico_id",
        "gerador_os_vinculos", ["ordem_servico_id"],
    )
    op.create_index(
        "ix_gerador_os_vinculos_gerador_id",
        "gerador_os_vinculos", ["gerador_id"],
    )
    op.create_index(
        "ix_gerador_os_vinculos_os_ativo",
        "gerador_os_vinculos", ["ordem_servico_id", "ativo"],
    )


def downgrade():
    bind = op.get_bind()
    existentes = bind.execute(
        sa.text("SELECT COUNT(*) FROM gerador_os_vinculos")
    ).scalar()
    if existentes:
        raise RuntimeError(
            "Downgrade bloqueado: existem vinculos OS-gerador. "
            "Preservar auditoria e planejar rollback seguro."
        )
    op.drop_index(
        "ix_gerador_os_vinculos_os_ativo", table_name="gerador_os_vinculos"
    )
    op.drop_index(
        "ix_gerador_os_vinculos_gerador_id", table_name="gerador_os_vinculos"
    )
    op.drop_index(
        "ix_gerador_os_vinculos_ordem_servico_id", table_name="gerador_os_vinculos"
    )
    op.drop_table("gerador_os_vinculos")
