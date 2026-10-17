# -*- coding: utf-8 -*-
"""G1: evita truncamento de textos no cadastro de grupos geradores."""

from __future__ import annotations

import os
from pathlib import Path
from types import SimpleNamespace

import pytest


# O projeto inicializa uma app durante o import do pacote.
# Todos os testes abaixo usam apenas o ambiente de teste.
os.environ["FLASK_ENV"] = "testing"


@pytest.mark.parametrize(
    ("campo", "limite"),
    [
        ("descricao", 250),
        ("fabricante_grupo", 150),
        ("modelo", 150),
        ("numero_serie", 150),
        ("local_instalado", 250),
        ("aplicacao", 200),
        ("regime_operacao", 100),
        ("disjuntor_descricao", 200),
    ],
)
def test_g1_valida_tamanhos_reais_do_modelo(campo, limite):
    from app.geradores.gerador_model import Gerador
    from app.geradores.gerador_service import (
        GeradorDominioError,
        _validar_tamanhos_textos_gerador,
    )

    assert Gerador.__table__.columns[campo].type.length == limite

    _validar_tamanhos_textos_gerador({campo: "x" * limite})

    with pytest.raises(
        GeradorDominioError,
        match=f"{limite} caracteres",
    ):
        _validar_tamanhos_textos_gerador({
            campo: "x" * (limite + 1),
        })


def test_g1_descricao_informa_campo_limite_e_orientacao():
    from app.geradores.gerador_service import (
        GeradorDominioError,
        _validar_tamanhos_textos_gerador,
    )

    with pytest.raises(GeradorDominioError) as erro:
        _validar_tamanhos_textos_gerador({
            "descricao": "D" * 251,
        })

    mensagem = str(erro.value)
    assert "Descrição / Identificação complementar" in mensagem
    assert "250 caracteres" in mensagem
    assert "informados: 251" in mensagem
    assert "Observações" in mensagem


def test_g1_observacoes_text_nao_recebe_corte():
    from app.geradores.gerador_model import Gerador
    from app.geradores.gerador_service import (
        _validar_tamanhos_textos_gerador,
    )

    assert Gerador.__table__.columns["observacoes"].type.length is None
    _validar_tamanhos_textos_gerador({
        "descricao": "GERADOR 01",
        "observacoes": "Texto longo " * 1000,
    })


def test_g1_valida_antes_de_reservar_codigo_ou_gravar(monkeypatch):
    from app.geradores import gerador_service as service

    monkeypatch.setattr(
        service,
        "_carregar_cliente_ativo",
        lambda cliente_id: SimpleNamespace(id=int(cliente_id)),
    )
    monkeypatch.setattr(
        service,
        "_proximo_codigo_gerador",
        lambda: pytest.fail(
            "Descricao invalida nao deve reservar codigo de gerador."
        ),
    )

    with pytest.raises(
        service.GeradorDominioError,
        match="250 caracteres",
    ):
        service.criar_gerador(
            1,
            descricao="D" * 251,
            observacoes="Detalhes completos.",
        )


def test_g1_formulario_aplica_maxlength_sem_truncar_observacoes():
    fonte = Path(
        "app/geradores/templates/geradores/form.html"
    ).read_text(encoding="utf-8-sig")

    assert 'maxlength="{{ limites_texto[nome] }}"' in fonte
    assert 'maxlength="{{ limites_texto[\'descricao\'] }}"' in fonte
    assert "utilize o campo Observações abaixo" in fonte
    assert 'name="observacoes"' in fonte

    from app.geradores.gerador_routes import _contexto_form_gerador
    from app.geradores.gerador_model import Gerador

    # A fonte dos limites deve ser a metadata ORM, nao numeros soltos.
    import inspect
    codigo = inspect.getsource(_contexto_form_gerador)
    assert "Gerador.__table__.columns" in codigo
    assert "coluna.type.length" in codigo
    assert Gerador.__table__.columns["descricao"].type.length == 250


def test_g1_tela_exibe_erro_e_preserva_formulario(monkeypatch):
    from flask import get_flashed_messages
    from app import create_app
    from app.geradores import gerador_routes as rotas
    from app.geradores import gerador_service as service

    app = create_app("testing")

    monkeypatch.setattr(
        rotas,
        "_contexto_form_gerador",
        lambda: {},
    )
    monkeypatch.setattr(
        rotas,
        "render_template",
        lambda template, **contexto: contexto,
    )
    monkeypatch.setattr(
        service,
        "_carregar_cliente_ativo",
        lambda cliente_id: SimpleNamespace(id=int(cliente_id)),
    )
    monkeypatch.setattr(
        service,
        "_proximo_codigo_gerador",
        lambda: pytest.fail("Nao pode reservar codigo com erro no texto."),
    )

    descricao = "D" * 251
    with app.test_request_context(
        "/geradores/novo",
        method="POST",
        data={"cliente_id": "1", "descricao": descricao},
    ):
        resposta = rotas.novo()
        mensagens = get_flashed_messages(with_categories=True)

    assert resposta["form_data"]["descricao"] == descricao
    assert any(
        categoria == "warning" and "250 caracteres" in mensagem
        for categoria, mensagem in mensagens
    )
