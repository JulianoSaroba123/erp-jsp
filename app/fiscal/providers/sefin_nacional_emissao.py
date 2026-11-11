"""Transporte tecnico da emissao sincrona SEFIN Nacional.

D24F03-B8-A3.3:
- recebe DPS XMLDSIG ja assinada;
- valida assinatura antes da rede;
- compacta XML em GZip;
- representa GZip em Base64;
- monta JSON dpsXmlGZipB64;
- resolve POST /nfse pelo ambiente configurado;
- utiliza mTLS temporario;
- retorna resposta HTTP tecnica;
- nao interpreta ainda o resultado fiscal.
"""

import base64
import gzip
import json

from app.fiscal.providers.sefin_nacional_config import (
    obter_configuracao_sefin,
)
from app.fiscal.providers.sefin_nacional_endpoints import (
    compor_url,
)
from app.fiscal.providers.sefin_nacional_http import (
    ClienteHttpSefin,
)
from app.fiscal.providers.sefin_nacional_mtls import (
    materializar_mtls_sefin,
)
from app.fiscal.xsd import obter_caminho_xsd_dps
from app.fiscal.xml.dps_signer import (
    AssinaturaXmlDpsInvalida,
    validar_assinatura_xml_dps,
)
from app.fiscal.xml.dps_xsd_validator import validar_xml_dps_xsd


class PreparacaoEmissaoSefinInvalida(ValueError):
    """Payload de emissao SEFIN nao pode ser preparado."""


def montar_corpo_emissao_nfse(
    xml_dps_assinado,
    *,
    caminho_xsd=None,
) -> bytes:
    """Monta JSON oficial contendo DPS GZip/Base64.

    Quando um XSD e informado, a DPS assinada precisa ser valida
    perante esse schema antes de qualquer empacotamento.
    """

    if not isinstance(
        xml_dps_assinado,
        (bytes, bytearray),
    ):
        raise PreparacaoEmissaoSefinInvalida(
            "XML assinado da DPS deve ser bytes."
        )

    xml = bytes(
        xml_dps_assinado
    )

    if not xml:
        raise PreparacaoEmissaoSefinInvalida(
            "XML assinado da DPS esta vazio."
        )

    try:
        validar_assinatura_xml_dps(
            xml
        )
    except AssinaturaXmlDpsInvalida as exc:
        raise PreparacaoEmissaoSefinInvalida(
            "XML da DPS nao possui assinatura XMLDSIG valida."
        ) from exc

    if caminho_xsd is not None:
        resultado_xsd = validar_xml_dps_xsd(
            xml,
            caminho_xsd,
        )

        if not resultado_xsd.valido:
            erros = "; ".join(
                str(erro)
                for erro in resultado_xsd.erros
            )

            mensagem = (
                "XML assinado da DPS invalido perante o XSD "
                "antes da transmissao."
            )

            if erros:
                mensagem = f"{mensagem} {erros}"

            raise PreparacaoEmissaoSefinInvalida(
                mensagem
            )

    # mtime=0 torna a compactacao deterministica.
    comprimido = gzip.compress(
        xml,
        compresslevel=9,
        mtime=0,
    )

    base64_xml = base64.b64encode(
        comprimido
    ).decode(
        "ascii"
    )

    corpo = {
        "dpsXmlGZipB64": base64_xml,
    }

    return json.dumps(
        corpo,
        ensure_ascii=False,
        separators=(",", ":"),
    ).encode(
        "utf-8"
    )


def executar_emissao_nfse_http(
    *,
    xml_dps_assinado,
    ambiente,
    material_certificado,
    cliente_http=None,
):
    """Executa somente o POST tecnico da DPS na SEFIN."""

    ambiente_normalizado = str(
        ambiente or ""
    ).strip().upper()

    metadados = obter_configuracao_sefin(
        ambiente_normalizado
    )

    rota = metadados[
        "rotas"
    ][
        "emitir_nfse"
    ]

    if str(
        rota.get("metodo") or ""
    ).strip().upper() != "POST":
        raise PreparacaoEmissaoSefinInvalida(
            "Rota emitir_nfse deve utilizar POST."
        )

    url = compor_url(
        ambiente=ambiente_normalizado,
        servico=rota["servico"],
        rota=rota["rota"],
    )

    caminho_xsd = obter_caminho_xsd_dps(
        metadados["layout_dps"],
        ambiente=ambiente_normalizado,
    )

    corpo = montar_corpo_emissao_nfse(
        xml_dps_assinado,
        caminho_xsd=caminho_xsd,
    )

    cliente = (
        cliente_http
        if cliente_http is not None
        else ClienteHttpSefin()
    )

    with materializar_mtls_sefin(
        material_certificado
    ) as certificado_cliente:
        return cliente.requisitar(
            metodo="POST",
            url=url,
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
            conteudo=corpo,
            certificado_cliente=certificado_cliente,
        )
