"""planos de manutencao e horimetro do modulo geradores G3

Revision ID: 20261006_03
Revises: 20261006_02
Create Date: 2026-10-06
"""

from alembic import op
import sqlalchemy as sa


revision = "20261006_03"
down_revision = "20261006_02"
branch_labels = None
depends_on = None


def upgrade() -> None:

    # ========================================================
    # PLANOS DE MANUTENCAO
    # ========================================================

    op.create_table(
        "planos_manutencao",

        sa.Column(
            "codigo",
            sa.String(length=50),
            nullable=False,
        ),
        sa.Column(
            "nome",
            sa.String(length=150),
            nullable=False,
        ),
        sa.Column(
            "tipo",
            sa.String(length=30),
            nullable=False,
        ),
        sa.Column(
            "descricao",
            sa.Text(),
            nullable=True,
        ),
        sa.Column(
            "plano_pai_id",
            sa.Integer(),
            nullable=True,
        ),
        sa.Column(
            "intervalo_horas",
            sa.Numeric(14, 2),
            nullable=True,
        ),
        sa.Column(
            "intervalo_meses",
            sa.Integer(),
            nullable=True,
        ),
        sa.Column(
            "observacoes",
            sa.Text(),
            nullable=True,
        ),

        sa.Column(
            "id",
            sa.Integer(),
            autoincrement=True,
            nullable=False,
        ),
        sa.Column(
            "criado_em",
            sa.DateTime(),
            nullable=False,
        ),
        sa.Column(
            "atualizado_em",
            sa.DateTime(),
            nullable=False,
        ),
        sa.Column(
            "ativo",
            sa.Boolean(),
            server_default=sa.text("true"),
            nullable=False,
        ),

        sa.ForeignKeyConstraint(
            ["plano_pai_id"],
            ["planos_manutencao.id"],
            name="fk_planos_manutencao_plano_pai",
            ondelete="RESTRICT",
        ),

        sa.PrimaryKeyConstraint(
            "id",
            name="pk_planos_manutencao",
        ),

        sa.CheckConstraint(
            "tipo IN ('BASICA', 'INTERMEDIARIA', 'AVANCADA')",
            name="ck_plano_manutencao_tipo",
        ),
        sa.CheckConstraint(
            "intervalo_horas IS NULL OR intervalo_horas > 0",
            name="ck_plano_manutencao_intervalo_horas",
        ),
        sa.CheckConstraint(
            "intervalo_meses IS NULL OR intervalo_meses > 0",
            name="ck_plano_manutencao_intervalo_meses",
        ),
        sa.CheckConstraint(
            "intervalo_horas IS NOT NULL OR intervalo_meses IS NOT NULL",
            name="ck_plano_manutencao_periodicidade",
        ),
        sa.CheckConstraint(
            "plano_pai_id IS NULL OR plano_pai_id <> id",
            name="ck_plano_manutencao_pai_diferente",
        ),
    )

    op.create_index(
        "ix_planos_manutencao_codigo",
        "planos_manutencao",
        ["codigo"],
        unique=True,
    )

    op.create_index(
        "ix_planos_manutencao_nome",
        "planos_manutencao",
        ["nome"],
        unique=False,
    )

    op.create_index(
        "ix_planos_manutencao_plano_pai_id",
        "planos_manutencao",
        ["plano_pai_id"],
        unique=False,
    )

    op.create_index(
        "ix_planos_manutencao_tipo",
        "planos_manutencao",
        ["tipo"],
        unique=False,
    )

    op.create_index(
        "ix_planos_manutencao_tipo_ativo",
        "planos_manutencao",
        ["tipo", "ativo"],
        unique=False,
    )

    # ========================================================
    # VINCULO GERADOR / PLANO
    # ========================================================

    op.create_table(
        "gerador_planos_manutencao",

        sa.Column(
            "gerador_id",
            sa.Integer(),
            nullable=False,
        ),
        sa.Column(
            "plano_id",
            sa.Integer(),
            nullable=False,
        ),
        sa.Column(
            "data_base_programacao",
            sa.Date(),
            nullable=True,
        ),
        sa.Column(
            "horimetro_base_programacao",
            sa.Numeric(14, 2),
            nullable=True,
        ),
        sa.Column(
            "observacoes",
            sa.Text(),
            nullable=True,
        ),

        sa.Column(
            "id",
            sa.Integer(),
            autoincrement=True,
            nullable=False,
        ),
        sa.Column(
            "criado_em",
            sa.DateTime(),
            nullable=False,
        ),
        sa.Column(
            "atualizado_em",
            sa.DateTime(),
            nullable=False,
        ),
        sa.Column(
            "ativo",
            sa.Boolean(),
            server_default=sa.text("true"),
            nullable=False,
        ),

        sa.ForeignKeyConstraint(
            ["gerador_id"],
            ["geradores.id"],
            name="fk_gerador_planos_manutencao_gerador",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["plano_id"],
            ["planos_manutencao.id"],
            name="fk_gerador_planos_manutencao_plano",
            ondelete="RESTRICT",
        ),

        sa.PrimaryKeyConstraint(
            "id",
            name="pk_gerador_planos_manutencao",
        ),

        sa.CheckConstraint(
            "horimetro_base_programacao IS NULL "
            "OR horimetro_base_programacao >= 0",
            name="ck_gerador_plano_horimetro_base",
        ),
    )

    op.create_index(
        "ix_gerador_planos_manutencao_gerador_id",
        "gerador_planos_manutencao",
        ["gerador_id"],
        unique=False,
    )

    op.create_index(
        "ix_gerador_planos_manutencao_plano_id",
        "gerador_planos_manutencao",
        ["plano_id"],
        unique=False,
    )

    op.create_index(
        "ix_gerador_planos_gerador_plano",
        "gerador_planos_manutencao",
        ["gerador_id", "plano_id"],
        unique=False,
    )

    op.create_index(
        "ix_gerador_planos_gerador_ativo",
        "gerador_planos_manutencao",
        ["gerador_id", "ativo"],
        unique=False,
    )

    # ========================================================
    # HISTORICO DE HORIMETRO
    # ========================================================

    op.create_table(
        "gerador_horimetros",

        sa.Column(
            "gerador_id",
            sa.Integer(),
            nullable=False,
        ),
        sa.Column(
            "leitura_anterior",
            sa.Numeric(14, 2),
            nullable=True,
        ),
        sa.Column(
            "leitura_atual",
            sa.Numeric(14, 2),
            nullable=False,
        ),
        sa.Column(
            "horas_acumuladas",
            sa.Numeric(14, 2),
            nullable=False,
        ),
        sa.Column(
            "data_leitura",
            sa.DateTime(),
            nullable=False,
        ),
        sa.Column(
            "responsavel",
            sa.String(length=150),
            nullable=False,
        ),
        sa.Column(
            "usuario_id",
            sa.Integer(),
            nullable=True,
        ),
        sa.Column(
            "tipo_evento",
            sa.String(length=30),
            server_default="NORMAL",
            nullable=False,
        ),
        sa.Column(
            "justificativa",
            sa.Text(),
            nullable=True,
        ),
        sa.Column(
            "observacoes",
            sa.Text(),
            nullable=True,
        ),

        sa.Column(
            "id",
            sa.Integer(),
            autoincrement=True,
            nullable=False,
        ),
        sa.Column(
            "criado_em",
            sa.DateTime(),
            nullable=False,
        ),
        sa.Column(
            "atualizado_em",
            sa.DateTime(),
            nullable=False,
        ),
        sa.Column(
            "ativo",
            sa.Boolean(),
            server_default=sa.text("true"),
            nullable=False,
        ),

        sa.ForeignKeyConstraint(
            ["gerador_id"],
            ["geradores.id"],
            name="fk_gerador_horimetros_gerador",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["usuario_id"],
            ["usuarios.id"],
            name="fk_gerador_horimetros_usuario",
            ondelete="RESTRICT",
        ),

        sa.PrimaryKeyConstraint(
            "id",
            name="pk_gerador_horimetros",
        ),

        sa.CheckConstraint(
            "leitura_anterior IS NULL OR leitura_anterior >= 0",
            name="ck_gerador_horimetro_anterior",
        ),
        sa.CheckConstraint(
            "leitura_atual >= 0",
            name="ck_gerador_horimetro_atual",
        ),
        sa.CheckConstraint(
            "horas_acumuladas >= 0",
            name="ck_gerador_horimetro_acumulado",
        ),
        sa.CheckConstraint(
            "tipo_evento IN ("
            "'NORMAL', "
            "'SUBSTITUICAO', "
            "'RESET', "
            "'FALHA_INSTRUMENTO'"
            ")",
            name="ck_gerador_horimetro_evento",
        ),
    )

    op.create_index(
        "ix_gerador_horimetros_data_leitura",
        "gerador_horimetros",
        ["data_leitura"],
        unique=False,
    )

    op.create_index(
        "ix_gerador_horimetros_gerador_id",
        "gerador_horimetros",
        ["gerador_id"],
        unique=False,
    )

    op.create_index(
        "ix_gerador_horimetros_usuario_id",
        "gerador_horimetros",
        ["usuario_id"],
        unique=False,
    )

    op.create_index(
        "ix_gerador_horimetros_tipo_evento",
        "gerador_horimetros",
        ["tipo_evento"],
        unique=False,
    )

    op.create_index(
        "ix_gerador_horimetros_gerador_data",
        "gerador_horimetros",
        ["gerador_id", "data_leitura"],
        unique=False,
    )

    op.create_index(
        "ix_gerador_horimetros_gerador_ativo",
        "gerador_horimetros",
        ["gerador_id", "ativo"],
        unique=False,
    )


def downgrade() -> None:

    op.drop_table(
        "gerador_horimetros"
    )

    op.drop_table(
        "gerador_planos_manutencao"
    )

    op.drop_table(
        "planos_manutencao"
    )
