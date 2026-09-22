"""Validacao XSD local da DPS da NFS-e Nacional.

D24F02-B6-A5:
- valida XML da DPS contra o XSD informado;
- nao realiza HTTP;
- nao assina XML;
- nao altera o pacote XSD original;
- trata de forma estrita a incompatibilidade conhecida de TSSerieDPS.
"""

from dataclasses import dataclass
from pathlib import Path
import shutil
import tempfile

from lxml import etree


XSD_NAMESPACE = "http://www.w3.org/2001/XMLSchema"

PADRAO_SERIE_OFICIAL = r"^0{0,4}\d{1,5}$"
PADRAO_SERIE_COMPATIVEL = r"0{0,4}\d{1,5}"

STATUS_VALIDO = "VALIDO"
STATUS_VALIDO_COMPATIBILIDADE_SERIE = (
    "VALIDO_COM_COMPATIBILIDADE_TSSERIEDPS"
)
STATUS_INVALIDO = "INVALIDO"


class ValidacaoXsdDpsInvalida(ValueError):
    """Falha tecnica ao preparar ou executar a validacao XSD."""


@dataclass(frozen=True)
class ResultadoValidacaoXsdDps:
    valido: bool
    status: str
    compatibilidade_aplicada: bool
    erros: tuple[str, ...]


def _parser_xml():
    return etree.XMLParser(
        resolve_entities=False,
        no_network=True,
    )


def _carregar_xml(xml):
    if hasattr(xml, "tag"):
        return xml

    if isinstance(xml, str):
        xml = xml.encode("utf-8")

    if not isinstance(
        xml,
        (bytes, bytearray),
    ):
        raise ValidacaoXsdDpsInvalida(
            "XML da DPS deve ser bytes, str ou elemento XML."
        )

    try:
        return etree.fromstring(
            bytes(xml),
            parser=_parser_xml(),
        )
    except etree.XMLSyntaxError as exc:
        raise ValidacaoXsdDpsInvalida(
            "XML da DPS sintaticamente invalido."
        ) from exc


def _normalizar_caminho_xsd(caminho_xsd):
    caminho = Path(caminho_xsd)

    if not caminho.is_file():
        raise ValidacaoXsdDpsInvalida(
            f"XSD DPS nao encontrado: {caminho}"
        )

    return caminho.resolve()


def _compilar_schema(caminho_xsd):
    try:
        documento = etree.parse(
            str(caminho_xsd),
            parser=_parser_xml(),
        )

        return etree.XMLSchema(
            documento
        )

    except (
        etree.XMLSyntaxError,
        etree.XMLSchemaParseError,
        OSError,
    ) as exc:
        raise ValidacaoXsdDpsInvalida(
            f"Falha ao compilar XSD DPS: {caminho_xsd}"
        ) from exc


def _formatar_erros(error_log):
    return tuple(
        (
            f"{erro.type_name}: "
            f"{erro.message}"
        )
        for erro in error_log
    )


def _somente_incompatibilidade_serie(error_log):
    erros = list(error_log)

    if not erros:
        return False

    for erro in erros:
        mensagem = str(
            erro.message or ""
        )

        if (
            erro.type_name
            != "SCHEMAV_CVC_PATTERN_VALID"
        ):
            return False

        if "}serie'" not in mensagem:
            return False

        if (
            PADRAO_SERIE_OFICIAL
            not in mensagem
        ):
            return False

    return True


def _corrigir_tss_serie_em_copia(
    caminho_tipos_simples,
):
    try:
        arvore = etree.parse(
            str(caminho_tipos_simples),
            parser=_parser_xml(),
        )
    except etree.XMLSyntaxError as exc:
        raise ValidacaoXsdDpsInvalida(
            "Nao foi possivel ler tiposSimples_v1.01.xsd."
        ) from exc

    patterns = arvore.xpath(
        (
            "//xs:simpleType"
            "[@name='TSSerieDPS']"
            "/xs:restriction"
            "/xs:pattern"
        ),
        namespaces={
            "xs": XSD_NAMESPACE,
        },
    )

    if len(patterns) != 1:
        raise ValidacaoXsdDpsInvalida(
            "TSSerieDPS nao encontrado de forma unica no XSD."
        )

    pattern = patterns[0]

    valor_atual = pattern.get(
        "value"
    )

    if valor_atual != PADRAO_SERIE_OFICIAL:
        raise ValidacaoXsdDpsInvalida(
            "Pattern TSSerieDPS diverge do defeito conhecido."
        )

    pattern.set(
        "value",
        PADRAO_SERIE_COMPATIVEL,
    )

    arvore.write(
        str(caminho_tipos_simples),
        encoding="UTF-8",
        xml_declaration=True,
    )


def _validar_com_compatibilidade(
    raiz_xml,
    caminho_xsd,
):
    diretorio_origem = caminho_xsd.parent

    with tempfile.TemporaryDirectory(
        prefix="erp_jsp_xsd_",
    ) as temporario:

        diretorio_copia = (
            Path(temporario)
            / "schema"
        )

        shutil.copytree(
            diretorio_origem,
            diretorio_copia,
        )

        xsd_copia = (
            diretorio_copia
            / caminho_xsd.name
        )

        tipos_simples = (
            diretorio_copia
            / "tiposSimples_v1.01.xsd"
        )

        if not tipos_simples.is_file():
            raise ValidacaoXsdDpsInvalida(
                "tiposSimples_v1.01.xsd nao encontrado "
                "no pacote XSD."
            )

        _corrigir_tss_serie_em_copia(
            tipos_simples
        )

        schema = _compilar_schema(
            xsd_copia
        )

        valido = schema.validate(
            raiz_xml
        )

        erros = _formatar_erros(
            schema.error_log
        )

        return valido, erros


def validar_xml_dps_xsd(
    xml,
    caminho_xsd,
    *,
    permitir_compatibilidade_serie=True,
):
    """Valida XML da DPS contra o XSD informado.

    A compatibilidade TSSerieDPS somente e aplicada quando
    a validacao original falha exclusivamente pelo pattern
    conhecido da serie.

    Qualquer outra divergencia permanece erro fiscal real.
    """

    caminho_xsd = _normalizar_caminho_xsd(
        caminho_xsd
    )

    raiz_xml = _carregar_xml(
        xml
    )

    schema = _compilar_schema(
        caminho_xsd
    )

    if schema.validate(
        raiz_xml
    ):
        return ResultadoValidacaoXsdDps(
            valido=True,
            status=STATUS_VALIDO,
            compatibilidade_aplicada=False,
            erros=(),
        )

    erros_originais = list(
        schema.error_log
    )

    if (
        not permitir_compatibilidade_serie
        or not _somente_incompatibilidade_serie(
            erros_originais
        )
    ):
        return ResultadoValidacaoXsdDps(
            valido=False,
            status=STATUS_INVALIDO,
            compatibilidade_aplicada=False,
            erros=_formatar_erros(
                erros_originais
            ),
        )

    valido, erros = (
        _validar_com_compatibilidade(
            raiz_xml,
            caminho_xsd,
        )
    )

    if valido:
        return ResultadoValidacaoXsdDps(
            valido=True,
            status=(
                STATUS_VALIDO_COMPATIBILIDADE_SERIE
            ),
            compatibilidade_aplicada=True,
            erros=(),
        )

    return ResultadoValidacaoXsdDps(
        valido=False,
        status=STATUS_INVALIDO,
        compatibilidade_aplicada=True,
        erros=erros,
    )
