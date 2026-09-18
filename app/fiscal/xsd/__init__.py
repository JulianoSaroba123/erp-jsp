"""Schemas XSD versionados usados pelo modulo fiscal."""

from pathlib import Path


VERSAO_XSD_DPS_SUPORTADA = "1.01"


def obter_caminho_xsd_dps(
    versao: str = VERSAO_XSD_DPS_SUPORTADA,
) -> Path:
    """Retorna o XSD permanente da DPS Nacional."""

    versao_normalizada = str(
        versao or ""
    ).strip()

    if versao_normalizada != VERSAO_XSD_DPS_SUPORTADA:
        raise ValueError(
            "Versao XSD DPS nao suportada."
        )

    caminho = (
        Path(__file__).resolve().parent
        / "sefin_nacional"
        / versao_normalizada
        / "DPS_v1.01.xsd"
    )

    if not caminho.is_file():
        raise FileNotFoundError(
            f"XSD permanente da DPS nao encontrado: {caminho}"
        )

    return caminho