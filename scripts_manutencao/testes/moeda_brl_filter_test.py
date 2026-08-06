# -*- coding: utf-8 -*-

from __future__ import annotations

from decimal import Decimal

import pytest


@pytest.fixture()
def app_ctx():
    from app import create_app

    app = create_app("testing")
    with app.app_context():
        yield app


@pytest.mark.parametrize(
    "valor, esperado",
    [
        (0, "R$ 0,00"),
        (2600, "R$ 2.600,00"),
        (Decimal("1234567.89"), "R$ 1.234.567,89"),
        (Decimal("12.3"), "R$ 12,30"),
        (None, "R$ 0,00"),
    ],
)
def test_filtro_moeda_brl_formata_valores(app_ctx, valor, esperado):
    filtro = app_ctx.jinja_env.filters.get("moeda_brl")
    assert filtro is not None
    assert filtro(valor) == esperado
