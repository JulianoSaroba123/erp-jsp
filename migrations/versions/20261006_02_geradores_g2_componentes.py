"""componentes tecnicos do modulo geradores G2

Revision ID: 20261006_02
Revises: 20261006_01
Create Date: 2026-10-06
"""

from alembic import op
import sqlalchemy as sa


revision = "20261006_02"
down_revision = "20261006_01"
branch_labels = None
depends_on = None


def upgrade() -> None:

    # ========================================================
    # MOTOR
    # ========================================================

    op.create_table(
        "gerador_motores",

        sa.Column("gerador_id", sa.Integer(), nullable=False),
        sa.Column("fabricante", sa.String(length=150), nullable=True),
        sa.Column("modelo", sa.String(length=150), nullable=True),
        sa.Column("variante", sa.String(length=150), nullable=True),
        sa.Column("numero_serie", sa.String(length=150), nullable=True),
        sa.Column("quantidade_cilindros", sa.Integer(), nullable=True),
        sa.Column("cilindrada_l", sa.Numeric(10, 3), nullable=True),
        sa.Column("aspiracao", sa.String(length=100), nullable=True),
        sa.Column("turbo", sa.Boolean(), nullable=True),
        sa.Column("intercooler", sa.Boolean(), nullable=True),
        sa.Column("potencia", sa.Numeric(12, 2), nullable=True),
        sa.Column("potencia_unidade", sa.String(length=20), nullable=True),
        sa.Column("rpm", sa.Integer(), nullable=True),
        sa.Column("combustivel", sa.String(length=80), nullable=True),
        sa.Column("capacidade_oleo_l", sa.Numeric(10, 2), nullable=True),
        sa.Column("especificacao_oleo", sa.String(length=200), nullable=True),
        sa.Column("pressao_normal_oleo", sa.String(length=100), nullable=True),
        sa.Column("temperatura_normal", sa.String(length=100), nullable=True),
        sa.Column("observacoes", sa.Text(), nullable=True),

        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("criado_em", sa.DateTime(), nullable=False),
        sa.Column("atualizado_em", sa.DateTime(), nullable=False),
        sa.Column(
            "ativo",
            sa.Boolean(),
            server_default=sa.text("true"),
            nullable=False,
        ),

        sa.ForeignKeyConstraint(
            ["gerador_id"],
            ["geradores.id"],
            name="fk_gerador_motores_gerador",
            ondelete="RESTRICT",
        ),

        sa.PrimaryKeyConstraint(
            "id",
            name="pk_gerador_motores",
        ),

        sa.CheckConstraint(
            "quantidade_cilindros IS NULL OR quantidade_cilindros > 0",
            name="ck_gerador_motor_cilindros",
        ),
        sa.CheckConstraint(
            "cilindrada_l IS NULL OR cilindrada_l >= 0",
            name="ck_gerador_motor_cilindrada",
        ),
        sa.CheckConstraint(
            "potencia IS NULL OR potencia >= 0",
            name="ck_gerador_motor_potencia",
        ),
        sa.CheckConstraint(
            "rpm IS NULL OR rpm > 0",
            name="ck_gerador_motor_rpm",
        ),
        sa.CheckConstraint(
            "capacidade_oleo_l IS NULL OR capacidade_oleo_l >= 0",
            name="ck_gerador_motor_capacidade_oleo",
        ),
    )

    op.create_index(
        "ix_gerador_motores_gerador_id",
        "gerador_motores",
        ["gerador_id"],
        unique=False,
    )

    op.create_index(
        "ix_gerador_motores_numero_serie",
        "gerador_motores",
        ["numero_serie"],
        unique=False,
    )

    op.create_index(
        "ix_gerador_motores_gerador_ativo",
        "gerador_motores",
        ["gerador_id", "ativo"],
        unique=False,
    )

    # ========================================================
    # ALTERNADOR
    # ========================================================

    op.create_table(
        "gerador_alternadores",

        sa.Column("gerador_id", sa.Integer(), nullable=False),
        sa.Column("fabricante", sa.String(length=150), nullable=True),
        sa.Column("modelo", sa.String(length=150), nullable=True),
        sa.Column("numero_serie", sa.String(length=150), nullable=True),
        sa.Column("potencia_kva", sa.Numeric(12, 2), nullable=True),
        sa.Column("tensao", sa.String(length=100), nullable=True),
        sa.Column("corrente_a", sa.Numeric(12, 2), nullable=True),
        sa.Column("frequencia_hz", sa.Numeric(8, 2), nullable=True),
        sa.Column("rpm", sa.Integer(), nullable=True),
        sa.Column("numero_polos", sa.Integer(), nullable=True),
        sa.Column("fator_potencia", sa.Numeric(5, 3), nullable=True),
        sa.Column("classe_isolacao", sa.String(length=50), nullable=True),
        sa.Column("grau_protecao", sa.String(length=50), nullable=True),
        sa.Column("sistema_excitacao", sa.String(length=150), nullable=True),
        sa.Column("possui_avr", sa.Boolean(), nullable=True),
        sa.Column("avr_fabricante", sa.String(length=150), nullable=True),
        sa.Column("avr_modelo", sa.String(length=150), nullable=True),
        sa.Column("ligacao", sa.String(length=100), nullable=True),
        sa.Column("observacoes", sa.Text(), nullable=True),

        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("criado_em", sa.DateTime(), nullable=False),
        sa.Column("atualizado_em", sa.DateTime(), nullable=False),
        sa.Column(
            "ativo",
            sa.Boolean(),
            server_default=sa.text("true"),
            nullable=False,
        ),

        sa.ForeignKeyConstraint(
            ["gerador_id"],
            ["geradores.id"],
            name="fk_gerador_alternadores_gerador",
            ondelete="RESTRICT",
        ),

        sa.PrimaryKeyConstraint(
            "id",
            name="pk_gerador_alternadores",
        ),

        sa.CheckConstraint(
            "potencia_kva IS NULL OR potencia_kva >= 0",
            name="ck_gerador_alternador_potencia",
        ),
        sa.CheckConstraint(
            "corrente_a IS NULL OR corrente_a >= 0",
            name="ck_gerador_alternador_corrente",
        ),
        sa.CheckConstraint(
            "frequencia_hz IS NULL OR frequencia_hz > 0",
            name="ck_gerador_alternador_frequencia",
        ),
        sa.CheckConstraint(
            "rpm IS NULL OR rpm > 0",
            name="ck_gerador_alternador_rpm",
        ),
        sa.CheckConstraint(
            "numero_polos IS NULL OR numero_polos > 0",
            name="ck_gerador_alternador_polos",
        ),
        sa.CheckConstraint(
            "fator_potencia IS NULL OR "
            "(fator_potencia > 0 AND fator_potencia <= 1)",
            name="ck_gerador_alternador_fp",
        ),
    )

    op.create_index(
        "ix_gerador_alternadores_gerador_id",
        "gerador_alternadores",
        ["gerador_id"],
        unique=False,
    )

    op.create_index(
        "ix_gerador_alternadores_numero_serie",
        "gerador_alternadores",
        ["numero_serie"],
        unique=False,
    )

    op.create_index(
        "ix_gerador_alternadores_gerador_ativo",
        "gerador_alternadores",
        ["gerador_id", "ativo"],
        unique=False,
    )

    # ========================================================
    # CONTROLADORA
    # ========================================================

    op.create_table(
        "gerador_controladoras",

        sa.Column("gerador_id", sa.Integer(), nullable=False),
        sa.Column("fabricante", sa.String(length=150), nullable=True),
        sa.Column("modelo", sa.String(length=150), nullable=True),
        sa.Column("versao", sa.String(length=100), nullable=True),
        sa.Column("firmware", sa.String(length=100), nullable=True),
        sa.Column("tensao_alimentacao", sa.String(length=100), nullable=True),
        sa.Column("comunicacao", sa.String(length=250), nullable=True),
        sa.Column("configuracao_relevante", sa.Text(), nullable=True),
        sa.Column("manual_referencia", sa.Text(), nullable=True),
        sa.Column("observacoes", sa.Text(), nullable=True),

        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("criado_em", sa.DateTime(), nullable=False),
        sa.Column("atualizado_em", sa.DateTime(), nullable=False),
        sa.Column(
            "ativo",
            sa.Boolean(),
            server_default=sa.text("true"),
            nullable=False,
        ),

        sa.ForeignKeyConstraint(
            ["gerador_id"],
            ["geradores.id"],
            name="fk_gerador_controladoras_gerador",
            ondelete="RESTRICT",
        ),

        sa.PrimaryKeyConstraint(
            "id",
            name="pk_gerador_controladoras",
        ),
    )

    op.create_index(
        "ix_gerador_controladoras_gerador_id",
        "gerador_controladoras",
        ["gerador_id"],
        unique=False,
    )

    op.create_index(
        "ix_gerador_controladoras_gerador_ativo",
        "gerador_controladoras",
        ["gerador_id", "ativo"],
        unique=False,
    )

    # ========================================================
    # QTA / ATS
    # ========================================================

    op.create_table(
        "gerador_qtas",

        sa.Column("gerador_id", sa.Integer(), nullable=False),
        sa.Column("fabricante", sa.String(length=150), nullable=True),
        sa.Column("modelo", sa.String(length=150), nullable=True),
        sa.Column("corrente_a", sa.Numeric(12, 2), nullable=True),
        sa.Column("numero_polos", sa.Integer(), nullable=True),
        sa.Column("tensao", sa.String(length=100), nullable=True),
        sa.Column("transferencia", sa.String(length=100), nullable=True),
        sa.Column("tipo", sa.String(length=30), nullable=True),
        sa.Column("controle", sa.String(length=250), nullable=True),
        sa.Column("intertravamento", sa.String(length=250), nullable=True),
        sa.Column("posicao_normal", sa.String(length=100), nullable=True),
        sa.Column("observacoes", sa.Text(), nullable=True),

        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("criado_em", sa.DateTime(), nullable=False),
        sa.Column("atualizado_em", sa.DateTime(), nullable=False),
        sa.Column(
            "ativo",
            sa.Boolean(),
            server_default=sa.text("true"),
            nullable=False,
        ),

        sa.ForeignKeyConstraint(
            ["gerador_id"],
            ["geradores.id"],
            name="fk_gerador_qtas_gerador",
            ondelete="RESTRICT",
        ),

        sa.PrimaryKeyConstraint(
            "id",
            name="pk_gerador_qtas",
        ),

        sa.CheckConstraint(
            "corrente_a IS NULL OR corrente_a >= 0",
            name="ck_gerador_qta_corrente",
        ),
        sa.CheckConstraint(
            "numero_polos IS NULL OR numero_polos > 0",
            name="ck_gerador_qta_polos",
        ),
        sa.CheckConstraint(
            "tipo IS NULL OR tipo IN ("
            "'CONTATOR', "
            "'DISJUNTOR', "
            "'CHAVE_MOTORIZADA', "
            "'CHAVE_REVERSORA', "
            "'OUTRO'"
            ")",
            name="ck_gerador_qta_tipo",
        ),
    )

    op.create_index(
        "ix_gerador_qtas_gerador_id",
        "gerador_qtas",
        ["gerador_id"],
        unique=False,
    )

    op.create_index(
        "ix_gerador_qtas_tipo",
        "gerador_qtas",
        ["tipo"],
        unique=False,
    )

    op.create_index(
        "ix_gerador_qtas_gerador_ativo",
        "gerador_qtas",
        ["gerador_id", "ativo"],
        unique=False,
    )

    # ========================================================
    # BATERIA
    # ========================================================

    op.create_table(
        "gerador_baterias",

        sa.Column("gerador_id", sa.Integer(), nullable=False),
        sa.Column("quantidade", sa.Integer(), nullable=True),
        sa.Column("tensao_nominal_v", sa.Numeric(10, 2), nullable=True),
        sa.Column("capacidade_ah", sa.Numeric(12, 2), nullable=True),
        sa.Column("fabricante", sa.String(length=150), nullable=True),
        sa.Column("modelo", sa.String(length=150), nullable=True),
        sa.Column("data_instalacao", sa.Date(), nullable=True),
        sa.Column("tensao_repouso_v", sa.Numeric(10, 2), nullable=True),
        sa.Column("tensao_partida_v", sa.Numeric(10, 2), nullable=True),
        sa.Column("observacoes", sa.Text(), nullable=True),

        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("criado_em", sa.DateTime(), nullable=False),
        sa.Column("atualizado_em", sa.DateTime(), nullable=False),
        sa.Column(
            "ativo",
            sa.Boolean(),
            server_default=sa.text("true"),
            nullable=False,
        ),

        sa.ForeignKeyConstraint(
            ["gerador_id"],
            ["geradores.id"],
            name="fk_gerador_baterias_gerador",
            ondelete="RESTRICT",
        ),

        sa.PrimaryKeyConstraint(
            "id",
            name="pk_gerador_baterias",
        ),

        sa.CheckConstraint(
            "quantidade IS NULL OR quantidade > 0",
            name="ck_gerador_bateria_quantidade",
        ),
        sa.CheckConstraint(
            "tensao_nominal_v IS NULL OR tensao_nominal_v >= 0",
            name="ck_gerador_bateria_tensao_nominal",
        ),
        sa.CheckConstraint(
            "capacidade_ah IS NULL OR capacidade_ah >= 0",
            name="ck_gerador_bateria_capacidade",
        ),
        sa.CheckConstraint(
            "tensao_repouso_v IS NULL OR tensao_repouso_v >= 0",
            name="ck_gerador_bateria_repouso",
        ),
        sa.CheckConstraint(
            "tensao_partida_v IS NULL OR tensao_partida_v >= 0",
            name="ck_gerador_bateria_partida",
        ),
    )

    op.create_index(
        "ix_gerador_baterias_gerador_id",
        "gerador_baterias",
        ["gerador_id"],
        unique=False,
    )

    op.create_index(
        "ix_gerador_baterias_gerador_ativo",
        "gerador_baterias",
        ["gerador_id", "ativo"],
        unique=False,
    )

    # ========================================================
    # CARREGADOR
    # ========================================================

    op.create_table(
        "gerador_carregadores",

        sa.Column("gerador_id", sa.Integer(), nullable=False),
        sa.Column("fabricante", sa.String(length=150), nullable=True),
        sa.Column("modelo", sa.String(length=150), nullable=True),
        sa.Column("tensao_nominal_v", sa.Numeric(10, 2), nullable=True),
        sa.Column("corrente_nominal_a", sa.Numeric(10, 2), nullable=True),
        sa.Column("tensao_medida_v", sa.Numeric(10, 2), nullable=True),
        sa.Column("observacoes", sa.Text(), nullable=True),

        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("criado_em", sa.DateTime(), nullable=False),
        sa.Column("atualizado_em", sa.DateTime(), nullable=False),
        sa.Column(
            "ativo",
            sa.Boolean(),
            server_default=sa.text("true"),
            nullable=False,
        ),

        sa.ForeignKeyConstraint(
            ["gerador_id"],
            ["geradores.id"],
            name="fk_gerador_carregadores_gerador",
            ondelete="RESTRICT",
        ),

        sa.PrimaryKeyConstraint(
            "id",
            name="pk_gerador_carregadores",
        ),

        sa.CheckConstraint(
            "tensao_nominal_v IS NULL OR tensao_nominal_v >= 0",
            name="ck_gerador_carregador_tensao",
        ),
        sa.CheckConstraint(
            "corrente_nominal_a IS NULL OR corrente_nominal_a >= 0",
            name="ck_gerador_carregador_corrente",
        ),
        sa.CheckConstraint(
            "tensao_medida_v IS NULL OR tensao_medida_v >= 0",
            name="ck_gerador_carregador_medida",
        ),
    )

    op.create_index(
        "ix_gerador_carregadores_gerador_id",
        "gerador_carregadores",
        ["gerador_id"],
        unique=False,
    )

    op.create_index(
        "ix_gerador_carregadores_gerador_ativo",
        "gerador_carregadores",
        ["gerador_id", "ativo"],
        unique=False,
    )

    # ========================================================
    # CONSUMIVEIS
    # ========================================================

    op.create_table(
        "gerador_consumiveis",

        sa.Column("gerador_id", sa.Integer(), nullable=False),
        sa.Column("produto_id", sa.Integer(), nullable=True),
        sa.Column("tipo", sa.String(length=40), nullable=False),
        sa.Column("fabricante_original", sa.String(length=150), nullable=True),
        sa.Column("referencia_original", sa.String(length=150), nullable=True),
        sa.Column("descricao", sa.Text(), nullable=True),
        sa.Column("quantidade", sa.Numeric(12, 3), nullable=True),
        sa.Column("unidade", sa.String(length=20), nullable=True),
        sa.Column("observacoes", sa.Text(), nullable=True),

        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("criado_em", sa.DateTime(), nullable=False),
        sa.Column("atualizado_em", sa.DateTime(), nullable=False),
        sa.Column(
            "ativo",
            sa.Boolean(),
            server_default=sa.text("true"),
            nullable=False,
        ),

        sa.ForeignKeyConstraint(
            ["gerador_id"],
            ["geradores.id"],
            name="fk_gerador_consumiveis_gerador",
            ondelete="RESTRICT",
        ),

        sa.ForeignKeyConstraint(
            ["produto_id"],
            ["produtos.id"],
            name="fk_gerador_consumiveis_produto",
            ondelete="RESTRICT",
        ),

        sa.PrimaryKeyConstraint(
            "id",
            name="pk_gerador_consumiveis",
        ),

        sa.CheckConstraint(
            "quantidade IS NULL OR quantidade > 0",
            name="ck_gerador_consumivel_quantidade",
        ),

        sa.CheckConstraint(
            "tipo IN ("
            "'FILTRO_OLEO', "
            "'FILTRO_COMBUSTIVEL', "
            "'PRE_FILTRO_COMBUSTIVEL', "
            "'SEPARADOR_AGUA', "
            "'FILTRO_AR_PRIMARIO', "
            "'FILTRO_AR_SECUNDARIO', "
            "'FILTRO_BLOW_BY', "
            "'OLEO', "
            "'LIQUIDO_ARREFECIMENTO', "
            "'CORREIA', "
            "'BATERIA', "
            "'OUTRO'"
            ")",
            name="ck_gerador_consumivel_tipo",
        ),
    )

    op.create_index(
        "ix_gerador_consumiveis_produto_id",
        "gerador_consumiveis",
        ["produto_id"],
        unique=False,
    )

    op.create_index(
        "ix_gerador_consumiveis_referencia_original",
        "gerador_consumiveis",
        ["referencia_original"],
        unique=False,
    )

    op.create_index(
        "ix_gerador_consumiveis_tipo",
        "gerador_consumiveis",
        ["tipo"],
        unique=False,
    )

    op.create_index(
        "ix_gerador_consumiveis_gerador_tipo",
        "gerador_consumiveis",
        ["gerador_id", "tipo"],
        unique=False,
    )

    # ========================================================
    # EQUIVALENTES
    # ========================================================

    op.create_table(
        "gerador_consumivel_equivalentes",

        sa.Column("consumivel_id", sa.Integer(), nullable=False),
        sa.Column("fabricante", sa.String(length=150), nullable=True),
        sa.Column("referencia", sa.String(length=150), nullable=False),
        sa.Column("descricao", sa.Text(), nullable=True),
        sa.Column("observacoes", sa.Text(), nullable=True),

        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("criado_em", sa.DateTime(), nullable=False),
        sa.Column("atualizado_em", sa.DateTime(), nullable=False),
        sa.Column(
            "ativo",
            sa.Boolean(),
            server_default=sa.text("true"),
            nullable=False,
        ),

        sa.ForeignKeyConstraint(
            ["consumivel_id"],
            ["gerador_consumiveis.id"],
            name="fk_gerador_consumivel_equiv_consumivel",
            ondelete="RESTRICT",
        ),

        sa.PrimaryKeyConstraint(
            "id",
            name="pk_gerador_consumivel_equivalentes",
        ),
    )

    op.create_index(
        "ix_gerador_consumivel_equivalentes_consumivel_id",
        "gerador_consumivel_equivalentes",
        ["consumivel_id"],
        unique=False,
    )

    op.create_index(
        "ix_gerador_consumivel_equivalentes_referencia",
        "gerador_consumivel_equivalentes",
        ["referencia"],
        unique=False,
    )

    op.create_index(
        "ix_gerador_consumivel_equiv_consumivel_ativo",
        "gerador_consumivel_equivalentes",
        ["consumivel_id", "ativo"],
        unique=False,
    )


def downgrade() -> None:

    op.drop_table(
        "gerador_consumivel_equivalentes"
    )

    op.drop_table(
        "gerador_consumiveis"
    )

    op.drop_table(
        "gerador_carregadores"
    )

    op.drop_table(
        "gerador_baterias"
    )

    op.drop_table(
        "gerador_qtas"
    )

    op.drop_table(
        "gerador_controladoras"
    )

    op.drop_table(
        "gerador_alternadores"
    )

    op.drop_table(
        "gerador_motores"
    )
