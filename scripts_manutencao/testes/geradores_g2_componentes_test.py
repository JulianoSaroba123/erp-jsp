# -*- coding: utf-8 -*-
"""G2 - Testes de dominio dos componentes do modulo Geradores."""

from __future__ import annotations

import ast
import os
from decimal import Decimal
from pathlib import Path

import pytest


os.environ["FLASK_ENV"] = "testing"


@pytest.fixture()
def app_ctx():
    from app import create_app
    from app.extensoes import db

    app = create_app("testing")

    with app.app_context():

        # Registrar explicitamente todos os models envolvidos antes
        # de create_all(), seguindo o padrao homologado no G1.
        from app.cliente.cliente_model import Cliente  # noqa: F401
        from app.produto.produto_model import Produto  # noqa: F401

        from app.geradores.gerador_model import (
            ClienteUnidade,  # noqa: F401
            Gerador,  # noqa: F401
        )

        from app.geradores.gerador_componente_model import (
            GeradorMotor,  # noqa: F401
            GeradorAlternador,  # noqa: F401
            GeradorControladora,  # noqa: F401
            GeradorQTA,  # noqa: F401
        )

        from app.geradores.gerador_partida_model import (
            GeradorBateria,  # noqa: F401
            GeradorCarregador,  # noqa: F401
        )

        from app.geradores.gerador_consumivel_model import (
            GeradorConsumivel,  # noqa: F401
            GeradorConsumivelEquivalente,  # noqa: F401
        )

        db.drop_all()
        db.create_all()

        yield app

        db.session.rollback()
        db.session.remove()
        db.drop_all()


def _cliente(db, *, ativo=True):
    from app.cliente.cliente_model import Cliente

    cliente = Cliente(
        nome="Cliente G2",
        tipo="PJ",
        cpf_cnpj="55666777000188",
        ativo=ativo,
    )

    db.session.add(cliente)
    db.session.commit()

    return cliente


def _gerador(db, cliente, *, ativo=True):
    from app.geradores.gerador_model import Gerador

    gerador = Gerador(
        codigo="GER-900001",
        cliente_id=cliente.id,
        descricao="Grupo gerador teste G2",
        status=Gerador.STATUS_ATIVO,
        ativo=ativo,
    )

    db.session.add(gerador)
    db.session.commit()

    return gerador


def _produto(db, *, ativo=True):
    from app.produto.produto_model import Produto

    produto = Produto(
        nome="Filtro teste G2",
        codigo="G2-FILTRO-001",
        unidade_medida="UN",
        estoque_atual=Decimal("7.000"),
        ativo=ativo,
    )

    db.session.add(produto)
    db.session.commit()

    return produto

def test_g2_service_sem_commit_e_sem_movimentacao_estoque():
    arquivo = Path(
        "app/geradores/gerador_componente_service.py"
    )

    source = arquivo.read_text(
        encoding="utf-8-sig"
    )

    tree = ast.parse(source)

    chamadas = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            chamadas.append(
                ast.get_source_segment(source, node) or ""
            )

    codigo_chamadas = "\n".join(chamadas)

    assert "db.session.commit(" not in codigo_chamadas
    assert "MovimentacaoEstoque(" not in codigo_chamadas
    assert "atualizar_estoque(" not in codigo_chamadas
    assert "estoque_atual =" not in source


def test_g2_tipos_consumivel():
    from app.geradores.gerador_consumivel_model import (
        GeradorConsumivel,
    )

    assert GeradorConsumivel.TIPOS_VALIDOS == (
        "FILTRO_OLEO",
        "FILTRO_COMBUSTIVEL",
        "PRE_FILTRO_COMBUSTIVEL",
        "SEPARADOR_AGUA",
        "FILTRO_AR_PRIMARIO",
        "FILTRO_AR_SECUNDARIO",
        "FILTRO_BLOW_BY",
        "OLEO",
        "LIQUIDO_ARREFECIMENTO",
        "CORREIA",
        "BATERIA",
        "OUTRO",
    )


def test_g2_cria_componentes_sem_commit(
    app_ctx,
    monkeypatch,
):
    from app.extensoes import db
    from app.geradores import gerador_componente_service as service

    cliente = _cliente(db)
    gerador = _gerador(db, cliente)

    def commit_proibido():
        pytest.fail(
            "Service G2 nao pode executar commit()."
        )

    monkeypatch.setattr(
        db.session,
        "commit",
        commit_proibido,
    )

    motor = service.criar_motor(
        gerador_id=gerador.id,
        fabricante="FPT",
        modelo="Modelo teste",
        rpm=1800,
    )

    alternador = service.criar_alternador(
        gerador_id=gerador.id,
        fabricante="Alternador teste",
        frequencia_hz=60,
    )

    controladora = service.criar_controladora(
        gerador_id=gerador.id,
        fabricante="KVA",
        modelo="K30i",
    )

    qta = service.criar_qta(
        gerador_id=gerador.id,
        tipo="CHAVE_MOTORIZADA",
        corrente_a=630,
    )

    bateria = service.criar_bateria(
        gerador_id=gerador.id,
        quantidade=2,
        tensao_nominal_v=12,
        capacidade_ah=150,
    )

    carregador = service.criar_carregador(
        gerador_id=gerador.id,
        fabricante="KVA",
        modelo="K21-Pro",
        tensao_nominal_v=24,
    )

    registros = (
        motor,
        alternador,
        controladora,
        qta,
        bateria,
        carregador,
    )

    assert all(
        registro.id is not None
        for registro in registros
    )

    assert all(
        registro.gerador_id == gerador.id
        for registro in registros
    )


def test_g2_rejeita_tipo_qta_invalido(app_ctx):
    from app.extensoes import db
    from app.geradores import gerador_componente_service as service

    cliente = _cliente(db)
    gerador = _gerador(db, cliente)

    with pytest.raises(
        service.GeradorG2DominioError,
        match="Tipo de QTA invalido",
    ):
        service.criar_qta(
            gerador_id=gerador.id,
            tipo="TELETRANSPORTE",
        )


def test_g2_rejeita_campo_nao_permitido(app_ctx):
    from app.extensoes import db
    from app.geradores import gerador_componente_service as service

    cliente = _cliente(db)
    gerador = _gerador(db, cliente)

    with pytest.raises(
        service.GeradorG2DominioError,
        match="Campos nao permitidos",
    ):
        service.criar_motor(
            gerador_id=gerador.id,
            senha_secreta="nao permitido",
        )

def test_g2_cria_consumivel_sem_produto(app_ctx):
    from app.extensoes import db
    from app.geradores import gerador_componente_service as service

    cliente = _cliente(db)
    gerador = _gerador(db, cliente)

    consumivel = service.criar_consumivel(
        gerador_id=gerador.id,
        tipo="FILTRO_OLEO",
        fabricante_original="FPT",
        referencia_original="5801986263",
        quantidade=1,
        unidade="UN",
    )

    assert consumivel.id is not None
    assert consumivel.gerador_id == gerador.id
    assert consumivel.produto_id is None
    assert consumivel.tipo == "FILTRO_OLEO"
    assert consumivel.referencia_original == "5801986263"


def test_g2_vincula_produto_sem_alterar_estoque(
    app_ctx,
    monkeypatch,
):
    from app.extensoes import db
    from app.geradores import gerador_componente_service as service

    cliente = _cliente(db)
    gerador = _gerador(db, cliente)
    produto = _produto(db)

    saldo_antes = Decimal(
        str(produto.estoque_atual)
    )

    def commit_proibido():
        pytest.fail(
            "criar_consumivel() nao pode executar commit()."
        )

    monkeypatch.setattr(
        db.session,
        "commit",
        commit_proibido,
    )

    consumivel = service.criar_consumivel(
        gerador_id=gerador.id,
        produto_id=produto.id,
        tipo="FILTRO_COMBUSTIVEL",
        fabricante_original="FPT",
        referencia_original="5802721728",
        quantidade=1,
        unidade="UN",
    )

    db.session.refresh(produto)

    assert consumivel.id is not None
    assert consumivel.produto_id == produto.id

    assert Decimal(
        str(produto.estoque_atual)
    ) == saldo_antes


def test_g2_rejeita_tipo_consumivel_invalido(app_ctx):
    from app.extensoes import db
    from app.geradores import gerador_componente_service as service

    cliente = _cliente(db)
    gerador = _gerador(db, cliente)

    with pytest.raises(
        service.GeradorG2DominioError,
        match="Tipo de consumivel invalido",
    ):
        service.criar_consumivel(
            gerador_id=gerador.id,
            tipo="FILTRO_INTERGALACTICO",
        )


def test_g2_rejeita_produto_inativo(app_ctx):
    from app.extensoes import db
    from app.geradores import gerador_componente_service as service

    cliente = _cliente(db)
    gerador = _gerador(db, cliente)
    produto = _produto(
        db,
        ativo=False,
    )

    with pytest.raises(
        service.GeradorG2DominioError,
        match="Produto nao encontrado ou inativo",
    ):
        service.criar_consumivel(
            gerador_id=gerador.id,
            produto_id=produto.id,
            tipo="FILTRO_OLEO",
        )


def test_g2_permite_multiplos_equivalentes(app_ctx):
    from app.extensoes import db
    from app.geradores import gerador_componente_service as service

    cliente = _cliente(db)
    gerador = _gerador(db, cliente)

    consumivel = service.criar_consumivel(
        gerador_id=gerador.id,
        tipo="FILTRO_AR_PRIMARIO",
        referencia_original="8041322",
    )

    equivalente_a = service.criar_equivalente(
        consumivel_id=consumivel.id,
        fabricante="Fabricante A",
        referencia="EQ-A",
    )

    equivalente_b = service.criar_equivalente(
        consumivel_id=consumivel.id,
        fabricante="Fabricante B",
        referencia="EQ-B",
    )

    assert equivalente_a.id is not None
    assert equivalente_b.id is not None
    assert equivalente_a.id != equivalente_b.id

    assert equivalente_a.consumivel_id == consumivel.id
    assert equivalente_b.consumivel_id == consumivel.id


def test_g2_rejeita_equivalente_sem_referencia(app_ctx):
    from app.extensoes import db
    from app.geradores import gerador_componente_service as service

    cliente = _cliente(db)
    gerador = _gerador(db, cliente)

    consumivel = service.criar_consumivel(
        gerador_id=gerador.id,
        tipo="CORREIA",
    )

    with pytest.raises(
        service.GeradorG2DominioError,
        match="Referencia equivalente e obrigatoria",
    ):
        service.criar_equivalente(
            consumivel_id=consumivel.id,
            referencia="   ",
        )


def test_g2_rejeita_gerador_inativo(app_ctx):
    from app.extensoes import db
    from app.geradores import gerador_componente_service as service

    cliente = _cliente(db)
    gerador = _gerador(
        db,
        cliente,
        ativo=False,
    )

    with pytest.raises(
        service.GeradorG2DominioError,
        match="Gerador nao encontrado ou inativo",
    ):
        service.criar_motor(
            gerador_id=gerador.id,
            fabricante="FPT",
        )
