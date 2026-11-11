"""Consulta segura da parametrização municipal da NFS-e Nacional.

H4-F18:
- consulta GET do convênio municipal antes da emissão;
- usa o mesmo certificado A1/mTLS da emissão;
- interpreta 200 como convênio ativo;
- interpreta 404 conhecido como bloqueio ambiental;
- não executa POST;
- não acessa banco.
"""

from __future__ import annotations

from app.fiscal.providers.base import (
    ErroTransmissaoNfse,
)
from app.fiscal.providers.sefin_nacional_config import (
    obter_configuracao_sefin,
)
from app.fiscal.providers.sefin_nacional_convenio import (
    RespostaConvenioInvalida,
    interpretar_resposta_convenio,
    validar_convenio_ativo,
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


class ValidacaoConvenioSefinInvalida(
    ErroTransmissaoNfse
):
    """Convênio municipal impede a emissão SEFIN."""


def executar_consulta_convenio_http(
    *,
    ambiente,
    codigo_municipio,
    material_certificado,
    cliente_http=None,
):
    """Consulta o convênio municipal com GET e mTLS."""

    ambiente_normalizado = str(
        ambiente or ""
    ).strip().upper()

    codigo = str(
        codigo_municipio or ""
    ).strip()

    if not codigo:
        raise ValidacaoConvenioSefinInvalida(
            "Código IBGE do município não informado."
        )

    metadados = obter_configuracao_sefin(
        ambiente_normalizado
    )

    rota = metadados[
        "rotas"
    ][
        "parametros_convenio"
    ]

    if str(
        rota.get(
            "metodo"
        )
        or ""
    ).strip().upper() != "GET":
        raise ValidacaoConvenioSefinInvalida(
            "Rota de convênio municipal deve utilizar GET."
        )

    url = compor_url(
        ambiente=ambiente_normalizado,
        servico=rota[
            "servico"
        ],
        rota=rota[
            "rota"
        ],
        codigo_municipio=codigo,
    )

    cliente = (
        cliente_http
        if cliente_http is not None
        else ClienteHttpSefin()
    )

    try:
        with materializar_mtls_sefin(
            material_certificado
        ) as certificado_cliente:
            resposta = cliente.requisitar(
                metodo="GET",
                url=url,
                headers={
                    "Accept": "application/json",
                },
                conteudo=None,
                certificado_cliente=certificado_cliente,
            )

    except ErroTransmissaoNfse as exc:
        status_code = getattr(
            exc,
            "status_code",
            None,
        )

        conteudo = getattr(
            exc,
            "conteudo",
            b"",
        )

        if status_code != 404:
            raise

        resultado = interpretar_resposta_convenio(
            ambiente=ambiente_normalizado,
            codigo_municipio=codigo,
            status_code=404,
            conteudo=conteudo,
        )

        try:
            validar_convenio_ativo(
                resultado
            )
        except RespostaConvenioInvalida as gate_exc:
            erro = ValidacaoConvenioSefinInvalida(
                str(
                    gate_exc
                )
            )
            erro.status_code = 404
            erro.conteudo = bytes(
                conteudo or b""
            )
            erro.resultado_convenio = resultado
            raise erro from gate_exc

        raise

    resultado = interpretar_resposta_convenio(
        ambiente=ambiente_normalizado,
        codigo_municipio=codigo,
        status_code=resposta.status_code,
        conteudo=resposta.conteudo,
    )

    try:
        validar_convenio_ativo(
            resultado
        )
    except RespostaConvenioInvalida as exc:
        erro = ValidacaoConvenioSefinInvalida(
            str(
                exc
            )
        )
        erro.status_code = resultado.status_code
        erro.conteudo = bytes(
            resposta.conteudo or b""
        )
        erro.resultado_convenio = resultado
        raise erro from exc

    return resultado
