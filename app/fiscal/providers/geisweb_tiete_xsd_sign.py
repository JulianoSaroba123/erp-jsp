"""Validacao XSD do EnviaSignLoteRps GeisWeb Tiete.

Usa exclusivamente artefatos XSD versionados localmente.
Nenhum acesso de rede durante a validacao.
"""

from dataclasses import dataclass
from pathlib import Path

from lxml import etree


BASE = (
    Path(__file__).resolve().parent.parent
    / "xsd"
    / "geisweb_tiete"
    / "1.01"
)

XSD_SIGN = (
    BASE
    / "envio_lote_rps_sign_reforma.xsd"
)

XSD_DSIG = (
    BASE
    / "xmldsig-core-schema.xsd"
)

URL_DSIG = (
    "http://www.gerenciadecidades.com.br/"
    "xsd/xmldsig-core-schema.xsd"
)


@dataclass(frozen=True)
class ResultadoValidacaoXsdGeisWebAssinado:
    valido: bool
    erros: tuple[str, ...]


class _ResolverGeisWebAssinado(
    etree.Resolver
):
    def resolve(
        self,
        url,
        pubid,
        context,
    ):
        if url == URL_DSIG:
            return self.resolve_filename(
                str(XSD_DSIG),
                context,
            )

        return None


def _compilar_schema():
    if not XSD_SIGN.exists():
        raise RuntimeError(
            "XSD assinado GeisWeb nao encontrado."
        )

    if not XSD_DSIG.exists():
        raise RuntimeError(
            "XSD XMLDSIG local nao encontrado."
        )

    parser = etree.XMLParser(
        no_network=True,
        resolve_entities=False,
    )

    parser.resolvers.add(
        _ResolverGeisWebAssinado()
    )

    arvore_xsd = etree.parse(
        str(XSD_SIGN),
        parser,
    )

    return etree.XMLSchema(
        arvore_xsd
    )


def validar_xml_envio_sign_lote_rps(
    xml,
):
    if isinstance(xml, str):
        xml = xml.encode(
            "ISO-8859-1"
        )

    if not isinstance(
        xml,
        (bytes, bytearray),
    ):
        return ResultadoValidacaoXsdGeisWebAssinado(
            valido=False,
            erros=(
                "XML deve ser bytes ou str.",
            ),
        )

    try:
        parser = etree.XMLParser(
            no_network=True,
            resolve_entities=False,
        )

        documento = etree.fromstring(
            bytes(xml),
            parser,
        )

        schema = _compilar_schema()

        valido = schema.validate(
            documento
        )

        erros = tuple(
            str(item)
            for item in schema.error_log
        )

        return ResultadoValidacaoXsdGeisWebAssinado(
            valido=valido,
            erros=erros,
        )

    except (
        etree.XMLSyntaxError,
        etree.XMLSchemaParseError,
    ) as exc:
        return ResultadoValidacaoXsdGeisWebAssinado(
            valido=False,
            erros=(
                str(exc),
            ),
        )
