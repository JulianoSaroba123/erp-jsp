# -*- coding: utf-8 -*-
"""
ERP JSP - Modulo GERADORES
Models fundamentais da Fase G1.

Nesta fase:
- ClienteUnidade
- Gerador

Motor, alternador, controladora, QTA, bateria, planos,
manutencoes e checklists serao adicionados nas proximas fases.
"""

from sqlalchemy import CheckConstraint, Index, UniqueConstraint

from app.extensoes import db
from app.models import BaseModel


class ClienteUnidade(BaseModel):
    """
    Unidade, planta, filial ou local operacional pertencente a um cliente.

    Permite que um mesmo cliente tenha varios locais com equipamentos
    distintos sem duplicar o cadastro principal do cliente.
    """

    __tablename__ = "cliente_unidades"

    cliente_id = db.Column(
        db.Integer,
        db.ForeignKey(
            "clientes.id",
            ondelete="RESTRICT",
        ),
        nullable=False,
        index=True,
    )

    nome = db.Column(
        db.String(150),
        nullable=False,
    )

    descricao = db.Column(
        db.Text,
        nullable=True,
    )

    # Endereco da unidade.
    # Nao e obrigatorio, pois o cadastro pode ser iniciado
    # progressivamente durante levantamento em campo.
    cep = db.Column(
        db.String(10),
        nullable=True,
    )

    endereco = db.Column(
        db.String(200),
        nullable=True,
    )

    numero = db.Column(
        db.String(20),
        nullable=True,
    )

    complemento = db.Column(
        db.String(100),
        nullable=True,
    )

    bairro = db.Column(
        db.String(100),
        nullable=True,
    )

    cidade = db.Column(
        db.String(100),
        nullable=True,
    )

    estado = db.Column(
        db.String(2),
        nullable=True,
    )

    contato_nome = db.Column(
        db.String(150),
        nullable=True,
    )

    contato_telefone = db.Column(
        db.String(30),
        nullable=True,
    )

    contato_email = db.Column(
        db.String(150),
        nullable=True,
    )

    observacoes = db.Column(
        db.Text,
        nullable=True,
    )

    cliente = db.relationship(
        "Cliente",
        backref=db.backref(
            "unidades",
            lazy="dynamic",
        ),
    )

    __table_args__ = (
        Index(
            "ix_cliente_unidades_cliente_nome",
            "cliente_id",
            "nome",
        ),
    )

    def __repr__(self):
        return (
            f"<ClienteUnidade "
            f"id={self.id} "
            f"cliente={self.cliente_id} "
            f"nome={self.nome!r}>"
        )

    @property
    def endereco_completo(self):
        partes = []

        if self.endereco:
            trecho = self.endereco

            if self.numero:
                trecho += f", {self.numero}"

            if self.complemento:
                trecho += f" - {self.complemento}"

            partes.append(trecho)

        if self.bairro:
            partes.append(self.bairro)

        if self.cidade and self.estado:
            partes.append(
                f"{self.cidade}/{self.estado}"
            )
        elif self.cidade:
            partes.append(self.cidade)

        if self.cep:
            partes.append(
                f"CEP {self.cep}"
            )

        return " - ".join(partes)


class Gerador(BaseModel):
    """
    Prontuario principal de um grupo gerador.

    O cadastro pode ser preenchido progressivamente.
    Dados tecnicos especializados serao separados em
    entidades proprias nas fases seguintes.
    """

    __tablename__ = "geradores"

    STATUS_ATIVO = "ATIVO"
    STATUS_INATIVO = "INATIVO"
    STATUS_VENDIDO = "VENDIDO"
    STATUS_SUBSTITUIDO = "SUBSTITUIDO"
    STATUS_FORA_OPERACAO = "FORA_DE_OPERACAO"

    STATUS_VALIDOS = (
        STATUS_ATIVO,
        STATUS_INATIVO,
        STATUS_VENDIDO,
        STATUS_SUBSTITUIDO,
        STATUS_FORA_OPERACAO,
    )

    # Codigo JSP.
    # A geracao automatica e concorrente sera implementada
    # no service + migration da proxima etapa.
    codigo = db.Column(
        db.String(20),
        nullable=False,
        unique=True,
        index=True,
    )

    cliente_id = db.Column(
        db.Integer,
        db.ForeignKey(
            "clientes.id",
            ondelete="RESTRICT",
        ),
        nullable=False,
        index=True,
    )

    unidade_id = db.Column(
        db.Integer,
        db.ForeignKey(
            "cliente_unidades.id",
            ondelete="RESTRICT",
        ),
        nullable=True,
        index=True,
    )

    # Vinculo opcional com o cadastro generico de equipamentos
    # ja existente no ERP.
    equipamento_id = db.Column(
        db.Integer,
        db.ForeignKey(
            "equipamentos.id",
            ondelete="RESTRICT",
        ),
        nullable=True,
    )

    # ========================================================
    # IDENTIFICACAO
    # ========================================================

    descricao = db.Column(
        db.String(250),
        nullable=True,
    )

    fabricante_grupo = db.Column(
        db.String(150),
        nullable=True,
    )

    modelo = db.Column(
        db.String(150),
        nullable=True,
    )

    numero_serie = db.Column(
        db.String(150),
        nullable=True,
        index=True,
    )

    ano = db.Column(
        db.Integer,
        nullable=True,
    )

    fabricante_integrador = db.Column(
        db.String(150),
        nullable=True,
    )

    local_instalado = db.Column(
        db.String(250),
        nullable=True,
    )

    aplicacao = db.Column(
        db.String(200),
        nullable=True,
    )

    regime_operacao = db.Column(
        db.String(100),
        nullable=True,
    )

    # ========================================================
    # DADOS ELETRICOS
    # ========================================================

    potencia_standby_kva = db.Column(
        db.Numeric(12, 2),
        nullable=True,
    )

    potencia_standby_kw = db.Column(
        db.Numeric(12, 2),
        nullable=True,
    )

    potencia_prime_kva = db.Column(
        db.Numeric(12, 2),
        nullable=True,
    )

    potencia_prime_kw = db.Column(
        db.Numeric(12, 2),
        nullable=True,
    )

    tensao = db.Column(
        db.String(100),
        nullable=True,
    )

    numero_fases = db.Column(
        db.String(30),
        nullable=True,
    )

    frequencia_hz = db.Column(
        db.Numeric(8, 2),
        nullable=True,
    )

    fator_potencia = db.Column(
        db.Numeric(5, 3),
        nullable=True,
    )

    corrente_nominal_a = db.Column(
        db.Numeric(12, 2),
        nullable=True,
    )

    rpm = db.Column(
        db.Integer,
        nullable=True,
    )

    ligacao = db.Column(
        db.String(100),
        nullable=True,
    )

    neutro = db.Column(
        db.String(100),
        nullable=True,
    )

    sistema_aterramento = db.Column(
        db.String(100),
        nullable=True,
    )

    # ========================================================
    # PROTECAO
    # ========================================================

    disjuntor_descricao = db.Column(
        db.String(200),
        nullable=True,
    )

    disjuntor_corrente_a = db.Column(
        db.Numeric(12, 2),
        nullable=True,
    )

    disjuntor_capacidade_interrupcao_ka = db.Column(
        db.Numeric(10, 2),
        nullable=True,
    )

    disjuntor_numero_polos = db.Column(
        db.Integer,
        nullable=True,
    )

    protecao_diferencial = db.Column(
        db.String(150),
        nullable=True,
    )

    # ========================================================
    # CICLO DE VIDA
    # ========================================================

    status = db.Column(
        db.String(30),
        nullable=False,
        default=STATUS_ATIVO,
        server_default=STATUS_ATIVO,
        index=True,
    )

    observacoes = db.Column(
        db.Text,
        nullable=True,
    )

    cliente = db.relationship(
        "Cliente",
        backref=db.backref(
            "geradores",
            lazy="dynamic",
        ),
    )

    unidade = db.relationship(
        "ClienteUnidade",
        backref=db.backref(
            "geradores",
            lazy="dynamic",
        ),
    )

    equipamento = db.relationship(
        "Equipamento",
        backref=db.backref(
            "gerador_prontuario",
            uselist=False,
        ),
    )

    __table_args__ = (
        UniqueConstraint(
            "equipamento_id",
            name="uq_geradores_equipamento",
        ),
        CheckConstraint(
            "status IN ("
            "'ATIVO', "
            "'INATIVO', "
            "'VENDIDO', "
            "'SUBSTITUIDO', "
            "'FORA_DE_OPERACAO'"
            ")",
            name="ck_geradores_status",
        ),
        CheckConstraint(
            "potencia_standby_kva IS NULL "
            "OR potencia_standby_kva >= 0",
            name="ck_geradores_standby_kva",
        ),
        CheckConstraint(
            "potencia_standby_kw IS NULL "
            "OR potencia_standby_kw >= 0",
            name="ck_geradores_standby_kw",
        ),
        CheckConstraint(
            "potencia_prime_kva IS NULL "
            "OR potencia_prime_kva >= 0",
            name="ck_geradores_prime_kva",
        ),
        CheckConstraint(
            "potencia_prime_kw IS NULL "
            "OR potencia_prime_kw >= 0",
            name="ck_geradores_prime_kw",
        ),
        CheckConstraint(
            "frequencia_hz IS NULL "
            "OR frequencia_hz > 0",
            name="ck_geradores_frequencia",
        ),
        CheckConstraint(
            "fator_potencia IS NULL "
            "OR (fator_potencia > 0 "
            "AND fator_potencia <= 1)",
            name="ck_geradores_fator_potencia",
        ),
        CheckConstraint(
            "corrente_nominal_a IS NULL "
            "OR corrente_nominal_a >= 0",
            name="ck_geradores_corrente",
        ),
        CheckConstraint(
            "rpm IS NULL OR rpm > 0",
            name="ck_geradores_rpm",
        ),
        Index(
            "ix_geradores_cliente_status",
            "cliente_id",
            "status",
        ),
        Index(
            "ix_geradores_unidade_status",
            "unidade_id",
            "status",
        ),
    )

    def __repr__(self):
        return (
            f"<Gerador "
            f"{self.codigo} "
            f"cliente={self.cliente_id}>"
        )

    @property
    def nome_exibicao(self):
        partes = [
            self.codigo,
        ]

        identificacao = " ".join(
            p
            for p in (
                self.fabricante_grupo,
                self.modelo,
            )
            if p
        )

        if identificacao:
            partes.append(identificacao)

        return " - ".join(partes)

    @property
    def esta_operacional(self):
        return (
            self.ativo
            and self.status == self.STATUS_ATIVO
        )
