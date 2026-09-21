from __future__ import annotations

import os

from app.fiscal.certificado_a1 import (
    ENV_PFX_PASSWORD,
    carregar_certificado_a1_do_ambiente,
)
from app.fiscal.providers.geisweb_tiete_http import (
    enviar_soap_geisweb,
)
from app.fiscal.providers.geisweb_tiete_mtls import (
    criar_session_a1,
)
from app.fiscal.providers.geisweb_tiete_response import (
    normalizar_resposta_geisweb,
)
from app.fiscal.providers.geisweb_tiete_resultado import (
    interpretar_resultado_envio_geisweb,
)
from app.fiscal.providers.geisweb_tiete_signer import (
    assinar_xml_geisweb,
)
from app.fiscal.providers.geisweb_tiete_soap import (
    montar_envelope_soap_geisweb,
    montar_headers_soap_geisweb,
)


OPERACAO_ENVIO = "EnviaSignLoteRps"
PARAMETRO_RESPOSTA = "EnviaSignLoteRpsResposta"


class GeisWebTransmissaoError(RuntimeError):
    """Erro de orquestracao da transmissao GeisWeb."""


def transmitir_payload_geisweb(
    *,
    payload: dict,
    configuracao,
) -> dict:
    if not isinstance(payload, dict):
        raise GeisWebTransmissaoError(
            "Payload GeisWeb deve ser um dict."
        )

    conteudo = payload.get("conteudo")

    if not conteudo:
        raise GeisWebTransmissaoError(
            "Payload GeisWeb nao possui XML em conteudo."
        )

    webservice = payload.get("webservice")

    if not isinstance(webservice, dict):
        raise GeisWebTransmissaoError(
            "Payload GeisWeb nao possui configuracao de webservice."
        )

    endpoint = webservice.get("endpoint")

    if not endpoint:
        raise GeisWebTransmissaoError(
            "Payload GeisWeb nao possui endpoint."
        )

    senha_pfx = os.environ.get(ENV_PFX_PASSWORD)

    if senha_pfx is None:
        raise GeisWebTransmissaoError(
            "Senha do certificado A1 nao configurada no ambiente."
        )

    material_certificado = (
        carregar_certificado_a1_do_ambiente()
    )

    xml_assinado = assinar_xml_geisweb(
        conteudo,
        material_certificado,
    )

    envelope = montar_envelope_soap_geisweb(
        xml_fiscal=xml_assinado,
        nome_operacao=OPERACAO_ENVIO,
    )

    headers = montar_headers_soap_geisweb(
        nome_operacao=OPERACAO_ENVIO,
    )

    soap_action = headers.get("SOAPAction")

    if not soap_action:
        raise GeisWebTransmissaoError(
            "SOAPAction do EnviaSignLoteRps nao foi resolvida."
        )

    session = criar_session_a1(
        material_certificado.caminho,
        senha_pfx,
    )

    try:
        resposta_http = enviar_soap_geisweb(
            session,
            endpoint=endpoint,
            soap_action=soap_action,
            envelope=envelope,
        )
    finally:
        session.close()

    resposta = normalizar_resposta_geisweb(
        resposta_http.text,
        operation=OPERACAO_ENVIO,
        response_parameter=PARAMETRO_RESPOSTA,
    )

    resultado_funcional = (
        interpretar_resultado_envio_geisweb(
            resposta.payload
        )
    )

    ambiente = getattr(
        configuracao,
        "ambiente",
        None,
    )

    return {
        "status": resultado_funcional.status,
        "mensagem": resultado_funcional.mensagem,
        "protocolo": None,
        "numero_nfse": resultado_funcional.numero_nfse,
        "dados_provider": {
            "provider": "GEISWEB_TIETE",
            "ambiente": ambiente,
            "operacao": OPERACAO_ENVIO,
            "http_status": resposta_http.status_code,
            "numero_lote": resultado_funcional.numero_lote,
            "codigo_verificacao": (
                resultado_funcional.codigo_verificacao
            ),
            "chave_nacional": (
                resultado_funcional.chave_nacional
            ),
            "mensagens": [
                {
                    "erro": mensagem.erro,
                    "status": mensagem.status,
                }
                for mensagem
                in resultado_funcional.mensagens
            ],
            "nfse": [
                {
                    "numero_rps": nota.numero_rps,
                    "numero_nfse": nota.numero_nfse,
                    "codigo_verificacao": (
                        nota.codigo_verificacao
                    ),
                    "chave_nacional": nota.chave_nacional,
                }
                for nota
                in resultado_funcional.nfse
            ],
            "resposta": resposta.payload,
            "resposta_is_xml": resposta.payload_is_xml,
        },
    }
