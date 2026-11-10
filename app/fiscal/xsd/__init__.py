"""Schemas XSD versionados usados pelo modulo fiscal."""

from pathlib import Path


VERSAO_XSD_DPS_SUPORTADA = "1.01"

AMBIENTES_XSD_DPS = {
    "PRODUCAO": None,
    "HOMOLOGACAO": "producao_restrita",
}


def obter_caminho_xsd_dps(
    versao: str = VERSAO_XSD_DPS_SUPORTADA,
    *,
    ambiente: str | None = None,
) -> Path:
    """Retorna o XSD da DPS Nacional adequado ao ambiente."""

    versao_normalizada = str(
        versao or ""
    ).strip()

    if versao_normalizada != VERSAO_XSD_DPS_SUPORTADA:
        raise ValueError(
            "Versao XSD DPS nao suportada."
        )

    diretorio = (
        Path(__file__).resolve().parent
        / "sefin_nacional"
        / versao_normalizada
    )

    if ambiente is not None:
        ambiente_normalizado = str(
            ambiente or ""
        ).strip().upper()

        if ambiente_normalizado not in AMBIENTES_XSD_DPS:
            raise ValueError(
                "Ambiente XSD DPS nao suportado."
            )

        subdiretorio = AMBIENTES_XSD_DPS[
            ambiente_normalizado
        ]

        if subdiretorio:
            diretorio = diretorio / subdiretorio

    caminho = diretorio / "DPS_v1.01.xsd"

    if not caminho.is_file():
        raise FileNotFoundError(
            f"XSD permanente da DPS nao encontrado: {caminho}"
        )

    return caminho
