# -*- coding: utf-8 -*-
"""G1-A5 - Testes de dominio da fundacao do modulo Geradores."""

from __future__ import annotations

import ast
import os
from pathlib import Path

import pytest


# CRITICO:
# app/__init__.py cria uma app global durante o import.
# Forcamos essa inicializacao para TestingConfig / SQLite em memoria.
os.environ["FLASK_ENV"] = "testing"


@pytest.fixture()
def app_ctx():
    from app import create_app
    from app.extensoes import db

    app = create_app("testing")

    with app.app_context():

        # Registrar explicitamente os models envolvidos.
        from app.cliente.cliente_model import Cliente  # noqa: F401
        from app.equipamento.equipamento_model import Equipamento  # noqa: F401
        from app.geradores.gerador_model import ClienteUnidade, Gerador  # noqa: F401

        db.drop_all()
        db.create_all()

        yield app

        db.session.rollback()
        db.session.remove()
        db.drop_all()


def _cliente(
    db,
    *,
    nome="Cliente G1",
    documento="11222333000144",
    ativo=True,
):
    from app.cliente.cliente_model import Cliente

    cliente = Cliente(
        nome=nome,
        tipo="PJ",
        cpf_cnpj=documento,
        ativo=ativo,
    )

    db.session.add(cliente)
    db.session.commit()

    return cliente


def _equipamento(
    db,
    cliente,
    *,
    nome="Grupo Gerador Teste",
    ativo=True,
):
    from app.equipamento.equipamento_model import Equipamento

    equipamento = Equipamento(
        nome=nome,
        cliente_id=cliente.id,
        tipo="GRUPO GERADOR",
        ativo=ativo,
    )

    db.session.add(equipamento)
    db.session.commit()

    return equipamento


def _unidade(
    db,
    cliente,
    *,
    nome="Unidade Teste",
    ativo=True,
):
    from app.geradores.gerador_model import ClienteUnidade

    unidade = ClienteUnidade(
        cliente_id=cliente.id,
        nome=nome,
        ativo=ativo,
    )

    db.session.add(unidade)
    db.session.commit()

    return unidade


def test_g1_status_ciclo_de_vida():
    from app.geradores.gerador_model import Gerador

    assert Gerador.STATUS_ATIVO == "ATIVO"
    assert Gerador.STATUS_INATIVO == "INATIVO"
    assert Gerador.STATUS_VENDIDO == "VENDIDO"
    assert Gerador.STATUS_SUBSTITUIDO == "SUBSTITUIDO"
    assert Gerador.STATUS_FORA_OPERACAO == "FORA_DE_OPERACAO"

    assert Gerador.STATUS_VALIDOS == (
        "ATIVO",
        "INATIVO",
        "VENDIDO",
        "SUBSTITUIDO",
        "FORA_DE_OPERACAO",
    )


def test_g1_service_sem_commit_e_com_lock():
    arquivo = Path(
        "app/geradores/gerador_service.py"
    )

    source = arquivo.read_text(
        encoding="utf-8-sig"
    )

    tree = ast.parse(source)

    funcoes = {
        node.name: node
        for node in tree.body
        if isinstance(node, ast.FunctionDef)
    }

    assert "criar_unidade" in funcoes
    assert "criar_gerador" in funcoes
    assert "_carregar_equipamento_para_vinculo" in funcoes

    for nome in (
        "criar_unidade",
        "criar_gerador",
    ):
        trecho = ast.get_source_segment(
            source,
            funcoes[nome],
        ) or ""

        assert "db.session.flush" in trecho
        assert "db.session.commit" not in trecho

    trecho_equipamento = ast.get_source_segment(
        source,
        funcoes["_carregar_equipamento_para_vinculo"],
    ) or ""

    assert "with_for_update" in trecho_equipamento


def test_g1_codigo_gerador_usa_sequence_sem_consumir_banco_real(
    app_ctx,
    monkeypatch,
):
    from app.geradores import gerador_service as service

    class ResultadoFake:
        def scalar_one(self):
            return 1

    chamadas = []

    def execute_fake(statement):
        chamadas.append(str(statement))
        return ResultadoFake()

    monkeypatch.setattr(
        service.db.session,
        "execute",
        execute_fake,
    )

    # Caso a implementacao faça flush antes/depois do nextval,
    # mantemos tudo isolado.
    monkeypatch.setattr(
        service.db.session,
        "flush",
        lambda: None,
    )

    codigo = service._proximo_codigo_gerador()

    assert codigo == "GER-000001"
    assert len(chamadas) == 1
    assert "geradores_codigo_seq" in chamadas[0]
    assert "nextval" in chamadas[0].lower()


def test_g1_criar_unidade_valida_sem_commit(
    app_ctx,
    monkeypatch,
):
    from app.extensoes import db
    from app.geradores import gerador_service as service
    from app.geradores.gerador_model import ClienteUnidade

    cliente = _cliente(db)

    def commit_proibido():
        pytest.fail(
            "criar_unidade() nao pode executar commit()."
        )

    monkeypatch.setattr(
        db.session,
        "commit",
        commit_proibido,
    )

    unidade = service.criar_unidade(
        cliente.id,
        "Frigorifico - Unidade Principal",
        cidade="Tiete",
        estado="SP",
    )

    assert unidade.id is not None
    assert unidade.cliente_id == cliente.id
    assert unidade.nome == "Frigorifico - Unidade Principal"
    assert unidade.cidade == "Tiete"
    assert unidade.estado == "SP"

    assert (
        db.session.get(
            ClienteUnidade,
            unidade.id,
        )
        is unidade
    )


def test_g1_criar_unidade_rejeita_cliente_inativo(
    app_ctx,
):
    from app.extensoes import db
    from app.geradores import gerador_service as service

    cliente = _cliente(
        db,
        ativo=False,
    )

    with pytest.raises(
        service.GeradorDominioError,
        match="Cliente nao encontrado ou inativo",
    ):
        service.criar_unidade(
            cliente.id,
            "Unidade Invalida",
        )


def test_g1_criar_unidade_rejeita_campo_nao_permitido(
    app_ctx,
):
    from app.extensoes import db
    from app.geradores import gerador_service as service

    cliente = _cliente(db)

    with pytest.raises(
        service.GeradorDominioError,
        match="Campos nao permitidos",
    ):
        service.criar_unidade(
            cliente.id,
            "Unidade Teste",
            campo_inexistente="NAO",
        )


def test_g1_criar_gerador_progressivo_minimo(
    app_ctx,
    monkeypatch,
):
    from app.extensoes import db
    from app.geradores import gerador_service as service
    from app.geradores.gerador_model import Gerador

    cliente = _cliente(db)

    monkeypatch.setattr(
        service,
        "_proximo_codigo_gerador",
        lambda: "GER-000001",
    )

    def commit_proibido():
        pytest.fail(
            "criar_gerador() nao pode executar commit()."
        )

    monkeypatch.setattr(
        db.session,
        "commit",
        commit_proibido,
    )

    gerador = service.criar_gerador(
        cliente.id,
        descricao="Grupo gerador cadastro progressivo",
    )

    assert gerador.id is not None
    assert gerador.codigo == "GER-000001"
    assert gerador.cliente_id == cliente.id
    assert gerador.descricao == "Grupo gerador cadastro progressivo"

    # Cadastro tecnico progressivo:
    assert gerador.modelo is None
    assert gerador.numero_serie is None
    assert gerador.potencia_standby_kva is None
    assert gerador.equipamento_id is None
    assert gerador.unidade_id is None

    assert gerador.status == Gerador.STATUS_ATIVO


def test_g1_rejeita_unidade_de_outro_cliente(
    app_ctx,
    monkeypatch,
):
    from app.extensoes import db
    from app.geradores import gerador_service as service

    cliente_a = _cliente(
        db,
        nome="Cliente A",
        documento="11111111000111",
    )

    cliente_b = _cliente(
        db,
        nome="Cliente B",
        documento="22222222000122",
    )

    unidade_b = _unidade(
        db,
        cliente_b,
    )

    monkeypatch.setattr(
        service,
        "_proximo_codigo_gerador",
        lambda: "GER-000001",
    )

    with pytest.raises(
        service.GeradorDominioError,
        match="nao pertence ao cliente",
    ):
        service.criar_gerador(
            cliente_a.id,
            unidade_id=unidade_b.id,
        )


def test_g1_rejeita_unidade_inativa(
    app_ctx,
    monkeypatch,
):
    from app.extensoes import db
    from app.geradores import gerador_service as service

    cliente = _cliente(db)

    unidade = _unidade(
        db,
        cliente,
        ativo=False,
    )

    monkeypatch.setattr(
        service,
        "_proximo_codigo_gerador",
        lambda: "GER-000001",
    )

    with pytest.raises(
        service.GeradorDominioError,
        match="Unidade nao encontrada ou inativa",
    ):
        service.criar_gerador(
            cliente.id,
            unidade_id=unidade.id,
        )


def test_g1_rejeita_equipamento_de_outro_cliente(
    app_ctx,
    monkeypatch,
):
    from app.extensoes import db
    from app.geradores import gerador_service as service

    cliente_a = _cliente(
        db,
        nome="Cliente A",
        documento="33333333000133",
    )

    cliente_b = _cliente(
        db,
        nome="Cliente B",
        documento="44444444000144",
    )

    equipamento_b = _equipamento(
        db,
        cliente_b,
    )

    monkeypatch.setattr(
        service,
        "_proximo_codigo_gerador",
        lambda: "GER-000001",
    )

    with pytest.raises(
        service.GeradorDominioError,
        match="nao pertence ao cliente",
    ):
        service.criar_gerador(
            cliente_a.id,
            equipamento_id=equipamento_b.id,
        )


def test_g1_rejeita_equipamento_inativo(
    app_ctx,
    monkeypatch,
):
    from app.extensoes import db
    from app.geradores import gerador_service as service

    cliente = _cliente(db)

    equipamento = _equipamento(
        db,
        cliente,
        ativo=False,
    )

    monkeypatch.setattr(
        service,
        "_proximo_codigo_gerador",
        lambda: "GER-000001",
    )

    with pytest.raises(
        service.GeradorDominioError,
        match="Equipamento nao encontrado ou inativo",
    ):
        service.criar_gerador(
            cliente.id,
            equipamento_id=equipamento.id,
        )


def test_g1_bloqueia_prontuario_duplicado_por_equipamento(
    app_ctx,
    monkeypatch,
):
    from app.extensoes import db
    from app.geradores import gerador_service as service
    from app.geradores.gerador_model import Gerador

    cliente = _cliente(db)

    equipamento = _equipamento(
        db,
        cliente,
    )

    existente = Gerador(
        codigo="GER-999999",
        cliente_id=cliente.id,
        equipamento_id=equipamento.id,
        status=Gerador.STATUS_ATIVO,
    )

    db.session.add(existente)
    db.session.commit()

    monkeypatch.setattr(
        service,
        "_proximo_codigo_gerador",
        lambda: pytest.fail(
            "Codigo nao deve ser reservado "
            "quando o equipamento ja possui prontuario."
        ),
    )

    with pytest.raises(
        service.GeradorDominioError,
        match="ja possui prontuario",
    ):
        service.criar_gerador(
            cliente.id,
            equipamento_id=equipamento.id,
        )


def test_g1_criar_gerador_rejeita_campo_nao_permitido(
    app_ctx,
    monkeypatch,
):
    from app.extensoes import db
    from app.geradores import gerador_service as service

    cliente = _cliente(db)

    monkeypatch.setattr(
        service,
        "_proximo_codigo_gerador",
        lambda: pytest.fail(
            "Codigo nao deve ser reservado "
            "com campo de entrada invalido."
        ),
    )

    with pytest.raises(
        service.GeradorDominioError,
        match="Campos nao permitidos",
    ):
        service.criar_gerador(
            cliente.id,
            senha_secreta="nao permitido",
        )


@pytest.mark.parametrize(
    "valor",
    [
        None,
        "",
        "abc",
        0,
        -1,
    ],
)
def test_g1_rejeita_cliente_id_invalido(
    app_ctx,
    valor,
):
    from app.geradores import gerador_service as service

    with pytest.raises(
        service.GeradorDominioError,
        match="cliente_id invalido",
    ):
        service.criar_gerador(
            valor,
        )
