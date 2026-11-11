"""H4-F4 - separacao segura de XSD por ambiente SEFIN Nacional."""

import hashlib

import pytest

from app.fiscal.providers.sefin_nacional_config import (
    AMBIENTES_SEFIN_NACIONAL,
)
from app.fiscal.xsd import obter_caminho_xsd_dps


HASHES_PRODREST_20261020 = {
    "DPS_v1.01.xsd": (
        "FE45E5250A48E519ABA89FC6A472863B"
        "8E602ED957778FB64692804933A00D0C"
    ),
    "tiposComplexos_v1.01.xsd": (
        "4F66F7C15BD3B05B3A16CBE5FA671B90"
        "C10E4C9C74276038730BE1C8C794B721"
    ),
    "tiposSimples_v1.01.xsd": (
        "562E326724F85CD7C41176D35E67C542"
        "376784D4C950EC1719704D480A8AF226"
    ),
    "xmldsig-core-schema.xsd": (
        "8C9792A056AEDCADFC95BF16F2D7448A"
        "35DA40DF71533E20AEA37D0329980C48"
    ),
}


def _sha256(caminho):
    return hashlib.sha256(
        caminho.read_bytes()
    ).hexdigest().upper()


def test_h4f4_001_producao_preserva_xsd_atual():
    caminho_padrao = obter_caminho_xsd_dps()
    caminho_producao = obter_caminho_xsd_dps(
        ambiente="PRODUCAO"
    )

    assert caminho_producao == caminho_padrao
    assert "producao_restrita" not in caminho_producao.parts


def test_h4f4_002_homologacao_usa_xsd_producao_restrita():
    caminho = obter_caminho_xsd_dps(
        ambiente="HOMOLOGACAO"
    )

    assert caminho.is_file()
    assert "producao_restrita" in caminho.parts
    assert caminho.name == "DPS_v1.01.xsd"


def test_h4f4_003_hashes_prodrest_20261020():
    diretorio = obter_caminho_xsd_dps(
        ambiente="HOMOLOGACAO"
    ).parent

    encontrados = {
        nome: _sha256(
            diretorio / nome
        )
        for nome in HASHES_PRODREST_20261020
    }

    assert encontrados == HASHES_PRODREST_20261020


def test_h4f4_004_rejeita_ambiente_desconhecido():
    with pytest.raises(
        ValueError,
        match="Ambiente XSD DPS nao suportado",
    ):
        obter_caminho_xsd_dps(
            ambiente="QUALQUER_COISA"
        )


def test_h4f4_005_perfil_homologacao_20261020():
    homologacao = AMBIENTES_SEFIN_NACIONAL[
        "HOMOLOGACAO"
    ]

    assert (
        homologacao["perfil_xsd"]
        == "PRODREST-v1.01-20261020"
    )
