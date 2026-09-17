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

class SerializacaoDpsInvalida(ValueError):
    """Erro de contrato entre a DPS canonica e o XML."""


def _valor_obrigatorio(dados, chave, *, grupo="identificacao"):
    """Obtem campo obrigatorio da representacao canonica."""

    if not isinstance(dados, dict):
        raise SerializacaoDpsInvalida(
            f"Grupo {grupo} da DPS canonica invalido."
        )

    valor = dados.get(chave)

    if valor is None or str(valor).strip() == "":
        raise SerializacaoDpsInvalida(
            f"Campo obrigatorio ausente: {grupo}.{chave}."
        )

    return str(valor).strip()


def adicionar_elemento_nfse(pai, nome: str, valor):
    """Adiciona elemento textual no namespace oficial da NFS-e."""

    if pai is None:
        raise SerializacaoDpsInvalida(
            "Elemento pai XML nao informado."
        )

    elemento = etree.SubElement(
        pai,
        _qname(nome),
    )

    elemento.text = str(valor)

    return elemento


def montar_xml_dps(dps_canonica: dict):
    """Monta a estrutura XML inicial DPS/infDPS conforme layout 1.01."""

    if not isinstance(dps_canonica, dict):
        raise SerializacaoDpsInvalida(
            "DPS canonica deve ser um dicionario."
        )

    identificacao = dps_canonica.get("identificacao")

    if not isinstance(identificacao, dict):
        raise SerializacaoDpsInvalida(
            "Grupo identificacao da DPS canonica nao informado."
        )

    versao_layout = _valor_obrigatorio(
        identificacao,
        "versao_layout",
    )

    if versao_layout != VERSAO_DPS:
        raise SerializacaoDpsInvalida(
            "Versao da DPS canonica incompativel com o serializador."
        )

    raiz = criar_elemento_nfse(
        "DPS",
        raiz=True,
        versao=VERSAO_DPS,
    )

    inf_dps = etree.SubElement(
        raiz,
        _qname("infDPS"),
    )

    inf_dps.set(
        "Id",
        _valor_obrigatorio(
            identificacao,
            "id",
        ),
    )

    # Ordem obrigatoria definida pelo TCInfDPS do XSD v1.01.
    campos = (
        ("tpAmb", "tp_amb"),
        ("dhEmi", "dh_emi"),
        ("verAplic", "versao_aplicativo"),
        ("serie", "serie"),
        ("nDPS", "numero_dps"),
        ("dCompet", "competencia"),
        ("tpEmit", "tipo_emitente"),
        ("cLocEmi", "municipio_emissao_ibge"),
    )

    for tag_xml, chave_canonica in campos:
        adicionar_elemento_nfse(
            inf_dps,
            tag_xml,
            _valor_obrigatorio(
                identificacao,
                chave_canonica,
            ),
        )

    return raiz
