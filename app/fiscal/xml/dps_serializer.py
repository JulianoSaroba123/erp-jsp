"""Fundacao de serializacao XML da DPS Nacional."""

from lxml import etree


NAMESPACE_NFSE = "http://www.sped.fazenda.gov.br/nfse"
VERSAO_DPS = "1.01"


def _qname(nome: str) -> etree.QName:
    """Retorna QName no namespace oficial da NFS-e."""

    nome_normalizado = str(nome or "").strip()

    if not nome_normalizado:
        raise ValueError("Nome do elemento XML nao pode ser vazio.")

    return etree.QName(
        NAMESPACE_NFSE,
        nome_normalizado,
    )


def criar_elemento_nfse(
    nome: str,
    *,
    raiz: bool = False,
    **atributos,
):
    """Cria elemento XML pertencente ao namespace oficial da NFS-e."""

    nsmap = {None: NAMESPACE_NFSE} if raiz else None

    elemento = etree.Element(
        _qname(nome),
        nsmap=nsmap,
    )

    for chave, valor in atributos.items():
        if valor is not None:
            elemento.set(
                str(chave),
                str(valor),
            )

    return elemento


def serializar_xml(elemento) -> bytes:
    """Serializa arvore XML em UTF-8 de forma deterministica."""

    if elemento is None:
        raise ValueError("Elemento XML nao informado.")

    return etree.tostring(
        elemento,
        encoding="UTF-8",
        xml_declaration=True,
        pretty_print=False,
    )
