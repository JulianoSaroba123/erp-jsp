"""fundacao do modulo geradores G1

Revision ID: 20261006_01
Revises: 20261005_01
Create Date: 2026-10-06
"""

from alembic import op
import sqlalchemy as sa


revision = "20261006_01"
down_revision = "20261005_01"
branch_labels = None
depends_on = None


def upgrade() -> None:

    # ========================================================
    # SEQUENCIA IMUTAVEL DO CODIGO JSP
    # ========================================================

    op.execute(
        """
        CREATE SEQUENCE geradores_codigo_seq
        START WITH 1
        INCREMENT BY 1
        NO MINVALUE
        NO MAXVALUE
        CACHE 1
        """
    )

    # ========================================================
    # CLIENTE / UNIDADE
    # ========================================================

    op.create_table(
        "cliente_unidades",

        sa.Column(
            "cliente_id",
            sa.Integer(),
            nullable=False,
        ),

        sa.Column(
            "nome",
            sa.String(length=150),
            nullable=False,
        ),

        sa.Column(
            "descricao",
            sa.Text(),
            nullable=True,
        ),

        sa.Column(
            "cep",
            sa.String(length=10),
            nullable=True,
        ),

        sa.Column(
            "endereco",
            sa.String(length=200),
            nullable=True,
        ),

        sa.Column(
            "numero",
            sa.String(length=20),
            nullable=True,
        ),

        sa.Column(
            "complemento",
            sa.String(length=100),
            nullable=True,
        ),

        sa.Column(
            "bairro",
            sa.String(length=100),
            nullable=True,
        ),

        sa.Column(
            "cidade",
            sa.String(length=100),
            nullable=True,
        ),

        sa.Column(
            "estado",
            sa.String(length=2),
            nullable=True,
        ),

        sa.Column(
            "contato_nome",
            sa.String(length=150),
            nullable=True,
        ),

        sa.Column(
            "contato_telefone",
            sa.String(length=30),
            nullable=True,
        ),

        sa.Column(
            "contato_email",
            sa.String(length=150),
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
            ["cliente_id"],
            ["clientes.id"],
            name="fk_cliente_unidades_cliente",
            ondelete="RESTRICT",
        ),

        sa.PrimaryKeyConstraint(
            "id",
            name="pk_cliente_unidades",
        ),
    )

    op.create_index(
        "ix_cliente_unidades_cliente_id",
        "cliente_unidades",
        ["cliente_id"],
        unique=False,
    )

    op.create_index(
        "ix_cliente_unidades_cliente_nome",
        "cliente_unidades",
        [
            "cliente_id",
            "nome",
        ],
        unique=False,
    )

    # ========================================================
    # GERADORES
    # ========================================================

    op.create_table(
        "geradores",

        sa.Column(
            "codigo",
            sa.String(length=20),
            nullable=False,
        ),

        sa.Column(
            "cliente_id",
            sa.Integer(),
            nullable=False,
        ),

        sa.Column(
            "unidade_id",
            sa.Integer(),
            nullable=True,
        ),

        sa.Column(
            "equipamento_id",
            sa.Integer(),
            nullable=True,
        ),

        # IDENTIFICACAO

        sa.Column(
            "descricao",
            sa.String(length=250),
            nullable=True,
        ),

        sa.Column(
            "fabricante_grupo",
            sa.String(length=150),
            nullable=True,
        ),

        sa.Column(
            "modelo",
            sa.String(length=150),
            nullable=True,
        ),

        sa.Column(
            "numero_serie",
            sa.String(length=150),
            nullable=True,
        ),

        sa.Column(
            "ano",
            sa.Integer(),
            nullable=True,
        ),

        sa.Column(
            "fabricante_integrador",
            sa.String(length=150),
            nullable=True,
        ),

        sa.Column(
            "local_instalado",
            sa.String(length=250),
            nullable=True,
        ),

        sa.Column(
            "aplicacao",
            sa.String(length=200),
            nullable=True,
        ),

        sa.Column(
            "regime_operacao",
            sa.String(length=100),
            nullable=True,
        ),

        # DADOS ELETRICOS

        sa.Column(
            "potencia_standby_kva",
            sa.Numeric(12, 2),
            nullable=True,
        ),

        sa.Column(
            "potencia_standby_kw",
            sa.Numeric(12, 2),
            nullable=True,
        ),

        sa.Column(
            "potencia_prime_kva",
            sa.Numeric(12, 2),
            nullable=True,
        ),

        sa.Column(
            "potencia_prime_kw",
            sa.Numeric(12, 2),
            nullable=True,
        ),

        sa.Column(
            "tensao",
            sa.String(length=100),
            nullable=True,
        ),

        sa.Column(
            "numero_fases",
            sa.String(length=30),
            nullable=True,
        ),

        sa.Column(
            "frequencia_hz",
            sa.Numeric(8, 2),
            nullable=True,
        ),

        sa.Column(
            "fator_potencia",
            sa.Numeric(5, 3),
            nullable=True,
        ),

        sa.Column(
            "corrente_nominal_a",
            sa.Numeric(12, 2),
            nullable=True,
        ),

        sa.Column(
            "rpm",
            sa.Integer(),
            nullable=True,
        ),

        sa.Column(
            "ligacao",
            sa.String(length=100),
            nullable=True,
        ),

        sa.Column(
            "neutro",
            sa.String(length=100),
            nullable=True,
        ),

        sa.Column(
            "sistema_aterramento",
            sa.String(length=100),
            nullable=True,
        ),

        # PROTECAO

        sa.Column(
            "disjuntor_descricao",
            sa.String(length=200),
            nullable=True,
        ),

        sa.Column(
            "disjuntor_corrente_a",
            sa.Numeric(12, 2),
            nullable=True,
        ),

        sa.Column(
            "disjuntor_capacidade_interrupcao_ka",
            sa.Numeric(10, 2),
            nullable=True,
        ),

        sa.Column(
            "disjuntor_numero_polos",
            sa.Integer(),
            nullable=True,
        ),

        sa.Column(
            "protecao_diferencial",
            sa.String(length=150),
            nullable=True,
        ),

        # CICLO DE VIDA

        sa.Column(
            "status",
            sa.String(length=30),
            server_default="ATIVO",
            nullable=False,
        ),

        sa.Column(
            "observacoes",
            sa.Text(),
            nullable=True,
        ),

        # BASEMODEL

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

        # FKs

        sa.ForeignKeyConstraint(
            ["cliente_id"],
            ["clientes.id"],
            name="fk_geradores_cliente",
            ondelete="RESTRICT",
        ),

        sa.ForeignKeyConstraint(
            ["unidade_id"],
            ["cliente_unidades.id"],
            name="fk_geradores_unidade",
            ondelete="RESTRICT",
        ),

        sa.ForeignKeyConstraint(
            ["equipamento_id"],
            ["equipamentos.id"],
            name="fk_geradores_equipamento",
            ondelete="RESTRICT",
        ),

        # PK

        sa.PrimaryKeyConstraint(
            "id",
            name="pk_geradores",
        ),

        # UNIQUE

        sa.UniqueConstraint(
            "equipamento_id",
            name="uq_geradores_equipamento",
        ),

        # CHECKS

        sa.CheckConstraint(
            """
            status IN (
                'ATIVO',
                'INATIVO',
                'VENDIDO',
                'SUBSTITUIDO',
                'FORA_DE_OPERACAO'
            )
            """,
            name="ck_geradores_status",
        ),

        sa.CheckConstraint(
            """
            potencia_standby_kva IS NULL
            OR potencia_standby_kva >= 0
            """,
            name="ck_geradores_standby_kva",
        ),

        sa.CheckConstraint(
            """
            potencia_standby_kw IS NULL
            OR potencia_standby_kw >= 0
            """,
            name="ck_geradores_standby_kw",
        ),

        sa.CheckConstraint(
            """
            potencia_prime_kva IS NULL
            OR potencia_prime_kva >= 0
            """,
            name="ck_geradores_prime_kva",
        ),

        sa.CheckConstraint(
            """
            potencia_prime_kw IS NULL
            OR potencia_prime_kw >= 0
            """,
            name="ck_geradores_prime_kw",
        ),

        sa.CheckConstraint(
            """
            frequencia_hz IS NULL
            OR frequencia_hz > 0
            """,
            name="ck_geradores_frequencia",
        ),

        sa.CheckConstraint(
            """
            fator_potencia IS NULL
            OR (
                fator_potencia > 0
                AND fator_potencia <= 1
            )
            """,
            name="ck_geradores_fator_potencia",
        ),

        sa.CheckConstraint(
            """
            corrente_nominal_a IS NULL
            OR corrente_nominal_a >= 0
            """,
            name="ck_geradores_corrente",
        ),

        sa.CheckConstraint(
            """
            rpm IS NULL
            OR rpm > 0
            """,
            name="ck_geradores_rpm",
        ),
    )

    # codigo GER unico e indexado

    op.create_index(
        "ix_geradores_codigo",
        "geradores",
        ["codigo"],
        unique=True,
    )

    op.create_index(
        "ix_geradores_cliente_id",
        "geradores",
        ["cliente_id"],
        unique=False,
    )

    op.create_index(
        "ix_geradores_unidade_id",
        "geradores",
        ["unidade_id"],
        unique=False,
    )

    op.create_index(
        "ix_geradores_numero_serie",
        "geradores",
        ["numero_serie"],
        unique=False,
    )

    op.create_index(
        "ix_geradores_status",
        "geradores",
        ["status"],
        unique=False,
    )

    op.create_index(
        "ix_geradores_cliente_status",
        "geradores",
        [
            "cliente_id",
            "status",
        ],
        unique=False,
    )

    op.create_index(
        "ix_geradores_unidade_status",
        "geradores",
        [
            "unidade_id",
            "status",
        ],
        unique=False,
    )


def downgrade() -> None:

    # O downgrade remove somente a fundacao G1.
    # Nenhuma tabela historica existente do ERP e alterada.

    op.drop_table(
        "geradores"
    )

    op.drop_table(
        "cliente_unidades"
    )

    op.execute(
        "DROP SEQUENCE IF EXISTS geradores_codigo_seq"
    )
