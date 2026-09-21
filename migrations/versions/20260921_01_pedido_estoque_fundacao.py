"""Fundacao de estoque para pedidos de venda.

Revision ID: 20260921_01
Revises: 20260919_03
Create Date: 2026-09-21

Responsabilidades:
- permitir estoque fracionado com NUMERIC(12,3);
- criar historico auditavel de movimentacoes;
- preparar rastreabilidade Pedido -> Estoque.
"""

from alembic import op
import sqlalchemy as sa


revision = "20260921_01"
down_revision = "20260919_03"
branch_labels = None
depends_on = None


def _alterar_estoque_para_numeric():
    bind = op.get_bind()
    dialect = bind.dialect.name

    if dialect == "postgresql":
        op.alter_column(
            "produtos",
            "estoque_atual",
            existing_type=sa.Integer(),
            type_=sa.Numeric(12, 3),
            existing_nullable=True,
            postgresql_using="estoque_atual::numeric(12,3)",
        )
        op.alter_column(
            "produtos",
            "estoque_minimo",
            existing_type=sa.Integer(),
            type_=sa.Numeric(12, 3),
            existing_nullable=True,
            postgresql_using="estoque_minimo::numeric(12,3)",
        )
        op.alter_column(
            "produtos",
            "estoque_maximo",
            existing_type=sa.Integer(),
            type_=sa.Numeric(12, 3),
            existing_nullable=True,
            postgresql_using="estoque_maximo::numeric(12,3)",
        )
        return

    # SQLite nao suporta ALTER COLUMN TYPE diretamente.
    # Alembic recria a tabela preservando dados e demais colunas.
    with op.batch_alter_table(
        "produtos",
        recreate="always",
    ) as batch_op:
        batch_op.alter_column(
            "estoque_atual",
            existing_type=sa.Integer(),
            type_=sa.Numeric(12, 3),
            existing_nullable=True,
        )
        batch_op.alter_column(
            "estoque_minimo",
            existing_type=sa.Integer(),
            type_=sa.Numeric(12, 3),
            existing_nullable=True,
        )
        batch_op.alter_column(
            "estoque_maximo",
            existing_type=sa.Integer(),
            type_=sa.Numeric(12, 3),
            existing_nullable=True,
        )


def _reverter_estoque_para_integer():
    bind = op.get_bind()
    dialect = bind.dialect.name

    if dialect == "postgresql":
        op.alter_column(
            "produtos",
            "estoque_atual",
            existing_type=sa.Numeric(12, 3),
            type_=sa.Integer(),
            existing_nullable=True,
            postgresql_using="estoque_atual::integer",
        )
        op.alter_column(
            "produtos",
            "estoque_minimo",
            existing_type=sa.Numeric(12, 3),
            type_=sa.Integer(),
            existing_nullable=True,
            postgresql_using="estoque_minimo::integer",
        )
        op.alter_column(
            "produtos",
            "estoque_maximo",
            existing_type=sa.Numeric(12, 3),
            type_=sa.Integer(),
            existing_nullable=True,
            postgresql_using="estoque_maximo::integer",
        )
        return

    with op.batch_alter_table(
        "produtos",
        recreate="always",
    ) as batch_op:
        batch_op.alter_column(
            "estoque_atual",
            existing_type=sa.Numeric(12, 3),
            type_=sa.Integer(),
            existing_nullable=True,
        )
        batch_op.alter_column(
            "estoque_minimo",
            existing_type=sa.Numeric(12, 3),
            type_=sa.Integer(),
            existing_nullable=True,
        )
        batch_op.alter_column(
            "estoque_maximo",
            existing_type=sa.Numeric(12, 3),
            type_=sa.Integer(),
            existing_nullable=True,
        )


def upgrade() -> None:
    _alterar_estoque_para_numeric()

    op.create_table(
        "movimentacoes_estoque",

        sa.Column(
            "id",
            sa.Integer(),
            primary_key=True,
            autoincrement=True,
        ),

        sa.Column(
            "produto_id",
            sa.Integer(),
            nullable=False,
        ),

        sa.Column(
            "pedido_id",
            sa.Integer(),
            nullable=True,
        ),

        sa.Column(
            "tipo",
            sa.String(length=20),
            nullable=False,
        ),

        sa.Column(
            "origem",
            sa.String(length=30),
            nullable=False,
        ),

        sa.Column(
            "quantidade",
            sa.Numeric(12, 3),
            nullable=False,
        ),

        sa.Column(
            "estoque_anterior",
            sa.Numeric(12, 3),
            nullable=False,
        ),

        sa.Column(
            "estoque_posterior",
            sa.Numeric(12, 3),
            nullable=False,
        ),

        sa.Column(
            "documento",
            sa.String(length=50),
            nullable=True,
        ),

        sa.Column(
            "observacoes",
            sa.Text(),
            nullable=True,
        ),

        sa.Column(
            "criado_em",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),

        sa.Column(
            "atualizado_em",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),

        sa.Column(
            "ativo",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("true"),
        ),

        sa.CheckConstraint(
            "tipo IN ('ENTRADA', 'SAIDA')",
            name="ck_mov_estoque_tipo",
        ),

        sa.CheckConstraint(
            "quantidade > 0",
            name="ck_mov_estoque_quantidade_positiva",
        ),

        sa.CheckConstraint(
            "estoque_anterior >= 0",
            name="ck_mov_estoque_saldo_anterior",
        ),

        sa.CheckConstraint(
            "estoque_posterior >= 0",
            name="ck_mov_estoque_saldo_posterior",
        ),

        sa.ForeignKeyConstraint(
            ["produto_id"],
            ["produtos.id"],
            name="fk_mov_estoque_produto_id",
            ondelete="RESTRICT",
        ),

        sa.ForeignKeyConstraint(
            ["pedido_id"],
            ["pedidos.id"],
            name="fk_mov_estoque_pedido_id",
            ondelete="RESTRICT",
        ),

        sa.UniqueConstraint(
            "pedido_id",
            "produto_id",
            "tipo",
            "origem",
            name="uq_mov_estoque_pedido_produto_tipo_origem",
        ),
    )

    op.create_index(
        "ix_movimentacoes_estoque_produto_id",
        "movimentacoes_estoque",
        ["produto_id"],
        unique=False,
    )

    op.create_index(
        "ix_movimentacoes_estoque_pedido_id",
        "movimentacoes_estoque",
        ["pedido_id"],
        unique=False,
    )

    op.create_index(
        "ix_movimentacoes_estoque_tipo",
        "movimentacoes_estoque",
        ["tipo"],
        unique=False,
    )

    op.create_index(
        "ix_movimentacoes_estoque_origem",
        "movimentacoes_estoque",
        ["origem"],
        unique=False,
    )

    op.create_index(
        "ix_movimentacoes_estoque_documento",
        "movimentacoes_estoque",
        ["documento"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_movimentacoes_estoque_documento",
        table_name="movimentacoes_estoque",
    )

    op.drop_index(
        "ix_movimentacoes_estoque_origem",
        table_name="movimentacoes_estoque",
    )

    op.drop_index(
        "ix_movimentacoes_estoque_tipo",
        table_name="movimentacoes_estoque",
    )

    op.drop_index(
        "ix_movimentacoes_estoque_pedido_id",
        table_name="movimentacoes_estoque",
    )

    op.drop_index(
        "ix_movimentacoes_estoque_produto_id",
        table_name="movimentacoes_estoque",
    )

    op.drop_table(
        "movimentacoes_estoque"
    )

    _reverter_estoque_para_integer()
