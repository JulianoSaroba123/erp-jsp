"""Validacao XSD local do XML GeisWeb Tiete 1.01."""

from dataclasses import dataclass
from pathlib import Path

from lxml import etree


XSD_DIR = (
    Path(__file__).resolve().parents[1]
    / "xsd"
    / "geisweb_tiete"
    / "1.01"
)

XSD_ENVIO = (
    XSD_DIR
    / "envio_lote_rps_reforma.xsd"
)

XSD_XMLDSIG = (
    XSD_DIR
    / "xmldsig-core-schema.xsd"
)

XMLDSIG_URL = (
    "http://www.gerenciadecidades.com.br/"
    "xsd/xmldsig-core-schema.xsd"
)


@dataclass(frozen=True)
class ResultadoValidacaoXsdGeisWeb:
    valido: bool
    erros: tuple[str, ...]


class _ResolverGeisWeb(etree.Resolver):

    def resolve(
        self,
        url,
        pubid,
        context,
    ):
        if url == XMLDSIG_URL:
            return self.resolve_filename(
                str(XSD_XMLDSIG),
                context,
            )

        return None


def _schema_envio():
    parser = etree.XMLParser(
        resolve_entities=False,
        no_network=True,
    )

    parser.resolvers.add(
        _ResolverGeisWeb()
    )

    arvore = etree.parse(
        str(XSD_ENVIO),
        parser,
    )

    return etree.XMLSchema(
        arvore
    )


def validar_xml_envio_lote_rps(
    xml,
) -> ResultadoValidacaoXsdGeisWeb:

    if isinstance(xml, str):
        xml = xml.encode(
            "ISO-8859-1"
        )

    if not isinstance(
        xml,
        (bytes, bytearray),
    ):
        raise TypeError(
            "XML GeisWeb deve ser bytes ou str."
        )

    parser = etree.XMLParser(
        resolve_entities=False,
        no_network=True,
    )

    documento = etree.fromstring(
        bytes(xml),
        parser,
    )

    schema = _schema_envio()

    valido = schema.validate(
        documento
    )

    erros = tuple(
        str(erro)
        for erro in schema.error_log
    )

    return ResultadoValidacaoXsdGeisWeb(
        valido=bool(valido),
        erros=erros,
    )
