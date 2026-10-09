# -*- coding: utf-8 -*-
"""Modulo de gestao tecnica de grupos geradores do ERP JSP."""

# Dependencias precisam estar registradas no metadata/class registry.
# Produto: vinculo opcional dos consumiveis.
# Usuario: responsavel autenticado opcional nas leituras de horimetro.
from app.produto.produto_model import Produto as _Produto  # noqa: F401
from app.auth.usuario_model import Usuario as _Usuario  # noqa: F401

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

from .gerador_plano_model import (
    PlanoManutencao,
    GeradorPlanoManutencao,
)

from .gerador_horimetro_model import (
    GeradorHorimetro,
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
    "PlanoManutencao",
    "GeradorPlanoManutencao",
    "GeradorHorimetro",
]
