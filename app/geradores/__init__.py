# -*- coding: utf-8 -*-
"""Modulo de gestao tecnica de grupos geradores do ERP JSP."""

# Produto precisa estar registrado no metadata/class registry porque
# GeradorConsumivel possui vinculo opcional com produtos.id.
from app.produto.produto_model import Produto as _Produto  # noqa: F401

from .gerador_model import (
    ClienteUnidade,
    Gerador,
)

from .gerador_componente_model import (
    GeradorMotor,
    GeradorAlternador,
    GeradorControladora,
    GeradorQTA,
)

from .gerador_partida_model import (
    GeradorBateria,
    GeradorCarregador,
)

from .gerador_consumivel_model import (
    GeradorConsumivel,
    GeradorConsumivelEquivalente,
)

__all__ = [
    "ClienteUnidade",
    "Gerador",
    "GeradorMotor",
    "GeradorAlternador",
    "GeradorControladora",
    "GeradorQTA",
    "GeradorBateria",
    "GeradorCarregador",
    "GeradorConsumivel",
    "GeradorConsumivelEquivalente",
]
