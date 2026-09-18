"""D24F02-B6-A6 - pacote XSD permanente da DPS."""

import hashlib
from pathlib import Path

import pytest

from app.fiscal.xsd import (
    obter_caminho_xsd_dps,
)


HASHES_ESPERADOS = {
    "DPS_v1.01.xsd": (
        "FE45E5250A48E519ABA89FC6A472863B"
        "8E602ED957778FB64692804933A00D0C"
    ),
    "tiposComplexos_v1.01.xsd": (
        "E8E09D525574CC224CA6D1F8D8EB036"
        "6043AB2A3AA8D0D234058E6244D60E371"
    ),
    "tiposSimples_v1.01.xsd": (
        "830EA116C34D7310699E34B214B7214A6"
        "5F7E5D3B1F09AEAA702F7E3F4283B17"
    ),
    "xmldsig-core-schema.xsd": (
        "49848F732663AECB618D72AD6130C5C32"
        "40F0A10F3A1A8544B7D48A6C726046F"
    ),
}


def _sha256(caminho: Path) -> str:
    return hashlib.sha256(
        caminho.read_bytes()
    ).hexdigest().upper()


def test_b6a6_001_resolve_xsd_permanente():
    caminho = obter_caminho_xsd_dps()

    assert caminho.is_file()

    partes = caminho.parts

    assert "app" in partes
    assert "fiscal" in partes
    assert "xsd" in partes
    assert "sefin_nacional" in partes
    assert "1.01" in partes

    assert caminho.name == "DPS_v1.01.xsd"


def test_b6a6_002_hashes_pacote_permanente():
    diretorio = obter_caminho_xsd_dps().parent

    encontrados = {
        nome: _sha256(
            diretorio / nome
        )
        for nome in HASHES_ESPERADOS
    }

    assert encontrados == HASHES_ESPERADOS


def test_b6a6_003_rejeita_versao_nao_suportada():
    with pytest.raises(
        ValueError,
        match="Versao XSD DPS nao suportada",
    ):
        obter_caminho_xsd_dps(
            "9.99"
        )