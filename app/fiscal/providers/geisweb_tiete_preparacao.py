"""Preparacao local do payload GeisWeb Tiete.

Fluxo:
payload tecnico
-> adapter ERP
-> EnviaLoteRps
-> validacao XSD
-> conteudo publicado no payload

Sem assinatura, certificado, SOAP ou rede.
"""

from app.fiscal.providers.geisweb_tiete_config import (
    CODIGO_PROVIDER,
)
from app.fiscal.providers.geisweb_tiete_erp_adapter import (
    montar_lote_geisweb_da_os,
)
from app.fiscal.providers.geisweb_tiete_xml import (
    montar_xml_envio_lote_rps_serializado,
)
from app.fiscal.providers.geisweb_tiete_xsd import (
    validar_xml_envio_lote_rps,
)


class PreparacaoLocalGeisWebInvalida(ValueError):
    """Falha na preparacao local do payload GeisWeb."""


def _validar_payload(
    *,
    payload,
    documento,
    ordem_servico,
):
    if not isinstance(payload, dict):
        raise PreparacaoLocalGeisWebInvalida(
            "Payload GeisWeb deve ser dict."
        )

    if payload.get("provider") != CODIGO_PROVIDER:
        raise PreparacaoLocalGeisWebInvalida(
            "Payload nao pertence ao GEISWEB_TIETE."
        )

    if payload.get("conteudo") is not None:
        raise PreparacaoLocalGeisWebInvalida(
            "Payload GeisWeb ja possui conteudo."
        )

    if payload.get("documento_id") != getattr(
        documento,
        "id",
        None,
    ):
        raise PreparacaoLocalGeisWebInvalida(
            "Documento do payload diverge."
        )

    if payload.get("ordem_servico_id") != getattr(
        ordem_servico,
        "id",
        None,
    ):
        raise PreparacaoLocalGeisWebInvalida(
            "Ordem de servico do payload diverge."
        )


def preparar_payload_geisweb_com_xml(
    *,
    payload,
    documento,
    ordem_servico,
    configuracao_institucional,
    configuracao_fiscal,
    numero_lote,
    data_emissao,
    tipo_lancamento,
    regime_geisweb,
    codigo_nacional,
    base_calculo,
    ibs_cbs,
    outros_impostos,
    ncm="",
    tomador=None,
    servico=None,
    valores=None,
):
    _validar_payload(
        payload=payload,
        documento=documento,
        ordem_servico=ordem_servico,
    )

    lote = montar_lote_geisweb_da_os(
        documento=documento,
        ordem_servico=ordem_servico,
        configuracao=configuracao_institucional,
        configuracao_fiscal=configuracao_fiscal,
        numero_lote=numero_lote,
        data_emissao=data_emissao,
        tipo_lancamento=tipo_lancamento,
        regime_geisweb=regime_geisweb,
        codigo_nacional=codigo_nacional,
        base_calculo=base_calculo,
        ibs_cbs=ibs_cbs,
        outros_impostos=outros_impostos,
        ncm=ncm,
        tomador=tomador,
        servico=servico,
        valores=valores,
    )

    xml = montar_xml_envio_lote_rps_serializado(
        lote
    )

    validacao = validar_xml_envio_lote_rps(
        xml
    )

    if not validacao.valido:
        raise PreparacaoLocalGeisWebInvalida(
            "XML EnviaLoteRps invalido: "
            + "; ".join(validacao.erros)
        )

    resultado = dict(payload)

    resultado["conteudo"] = xml

    resultado["validacao_xsd"] = {
        "valido": True,
        "erros": (),
    }

    return resultado
