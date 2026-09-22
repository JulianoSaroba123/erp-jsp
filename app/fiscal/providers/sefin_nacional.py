"""Provider da NFS-e Nacional / SEFIN.

D24F02-B1:
- registro e preparacao local do provider.

D24F03-B8-A3.5B:
- implementa transmissao concreta da DPS assinada;
- respeita o disjuntor integracao_ativa;
- carrega certificado A1 somente apos o disjuntor;
- utiliza transporte HTTP/mTLS isolado;
- normaliza sucesso 201;
- converte rejeicao HTTP 400 em resultado canonico REJEITADA;
- propaga erros tecnicos de autenticacao/comunicacao/indisponibilidade;
- nao executa commit;
- nao altera documento fiscal;
- nao altera financeiro.
"""

from lxml import etree

from app.fiscal.certificado_a1 import (
    carregar_certificado_a1_do_ambiente,
)
from app.fiscal.providers.base import (
    ErroTransmissaoNfse,
    NfseProvider,
)
from app.fiscal.providers.sefin_nacional_config import (
    obter_configuracao_sefin,
)
from app.fiscal.providers.sefin_nacional_emissao import (
    executar_emissao_nfse_http,
)
from app.fiscal.providers.sefin_nacional_resposta import (
    RespostaEmissaoSefinInvalida,
    normalizar_resposta_emissao_sefin,
)
from app.fiscal.providers.registry import (
    normalizar_codigo_provider,
    registrar_provider,
)


NFSE_NS = "http://www.sped.fazenda.gov.br/nfse"


def _extrair_numero_nfse(
    xml_nfse: bytes,
) -> str:
    if not isinstance(
        xml_nfse,
        (bytes, bytearray),
    ):
        raise ErroTransmissaoNfse(
            "XML da NFS-e retornado pela SEFIN deve ser bytes."
        )

    xml = bytes(
        xml_nfse
    )

    if not xml:
        raise ErroTransmissaoNfse(
            "XML da NFS-e retornado pela SEFIN esta vazio."
        )

    if b"<!DOCTYPE" in xml.upper():
        raise ErroTransmissaoNfse(
            "XML da NFS-e retornado pela SEFIN possui DOCTYPE nao permitido."
        )

    parser = etree.XMLParser(
        resolve_entities=False,
        no_network=True,
        load_dtd=False,
        recover=False,
    )

    try:
        raiz = etree.fromstring(
            xml,
            parser=parser,
        )
    except etree.XMLSyntaxError as exc:
        raise ErroTransmissaoNfse(
            "XML da NFS-e retornado pela SEFIN e invalido."
        ) from exc

    numero = raiz.find(
        f".//{{{NFSE_NS}}}infNFSe/"
        f"{{{NFSE_NS}}}nNFSe"
    )

    if numero is None:
        raise ErroTransmissaoNfse(
            "XML da NFS-e retornado pela SEFIN nao possui nNFSe."
        )

    valor = str(
        numero.text or ""
    ).strip()

    if not valor:
        raise ErroTransmissaoNfse(
            "Numero da NFS-e retornado pela SEFIN esta vazio."
        )

    return valor


def _mensagem_para_dict(
    mensagem,
) -> dict:
    return {
        "mensagem": mensagem.mensagem,
        "codigo": mensagem.codigo,
        "descricao": mensagem.descricao,
        "complemento": mensagem.complemento,
    }


def _texto_mensagem_processamento(
    mensagem,
) -> str:
    partes = []

    if mensagem.codigo:
        partes.append(
            f"[{mensagem.codigo}]"
        )

    texto = (
        mensagem.mensagem
        or mensagem.descricao
    )

    if texto:
        partes.append(
            texto
        )

    if mensagem.complemento:
        partes.append(
            mensagem.complemento
        )

    return " ".join(
        partes
    ).strip()


def _mensagem_rejeicao(
    resposta,
) -> str:
    detalhes = [
        _texto_mensagem_processamento(
            erro
        )
        for erro in resposta.erros
    ]

    detalhes = [
        item
        for item in detalhes
        if item
    ]

    mensagem = (
        "NFS-e rejeitada pela SEFIN Nacional."
    )

    if detalhes:
        mensagem += " " + "; ".join(
            detalhes
        )

    return mensagem


def _mensagem_sucesso(
    resposta,
) -> str:
    detalhes = [
        _texto_mensagem_processamento(
            alerta
        )
        for alerta in resposta.alertas
    ]

    detalhes = [
        item
        for item in detalhes
        if item
    ]

    mensagem = (
        "NFS-e autorizada pela SEFIN Nacional."
    )

    if detalhes:
        mensagem += " Alertas: " + "; ".join(
            detalhes
        )

    return mensagem


def _normalizar_resposta_ou_falhar(
    *,
    status_code,
    conteudo,
):
    try:
        return normalizar_resposta_emissao_sefin(
            status_code=status_code,
            conteudo=conteudo,
        )
    except RespostaEmissaoSefinInvalida as exc:
        raise ErroTransmissaoNfse(
            "Resposta da SEFIN Nacional nao pode ser normalizada."
        ) from exc


def _dados_provider_base(
    resposta,
) -> dict:
    return {
        "provider": "SEFIN_NACIONAL",
        "http_status": resposta.status_code,
        "tipo_ambiente": resposta.tipo_ambiente,
        "versao_aplicativo": resposta.versao_aplicativo,
        "data_hora_processamento": (
            resposta.data_hora_processamento
        ),
        "id_dps": resposta.id_dps,
        "chave_acesso": resposta.chave_acesso,
    }


@registrar_provider
class SefinNacionalProvider(NfseProvider):
    """Provider da NFS-e Nacional."""

    codigo = "SEFIN_NACIONAL"

    def validar_configuracao(
        self,
        configuracao,
    ) -> None:
        if configuracao is None:
            raise ValueError(
                "Configuracao fiscal nao informada."
            )

        provider = normalizar_codigo_provider(
            getattr(
                configuracao,
                "provider",
                None,
            )
        )

        if provider != self.codigo:
            raise ValueError(
                "Configuracao fiscal nao utiliza o provider "
                "SEFIN_NACIONAL."
            )

        ambiente = str(
            getattr(
                configuracao,
                "ambiente",
                "",
            )
            or ""
        ).strip().upper()

        if ambiente not in {
            "HOMOLOGACAO",
            "PRODUCAO",
        }:
            raise ValueError(
                "Ambiente fiscal invalido para SEFIN_NACIONAL."
            )

    def preparar_payload(
        self,
        *,
        documento,
        ordem_servico,
        configuracao,
    ) -> dict:
        self.validar_configuracao(
            configuracao
        )

        if documento is None:
            raise ValueError(
                "Documento NFS-e nao informado."
            )

        if ordem_servico is None:
            raise ValueError(
                "Ordem de servico nao informada."
            )

        ambiente = str(
            configuracao.ambiente
        ).strip().upper()

        metadados = obter_configuracao_sefin(
            ambiente
        )

        return {
            "provider": self.codigo,
            "ambiente": ambiente,
            "tipo_documento": "DPS",
            "documento_id": getattr(
                documento,
                "id",
                None,
            ),
            "ordem_servico_id": getattr(
                ordem_servico,
                "id",
                None,
            ),
            "layout": {
                "versao": metadados[
                    "layout_dps"
                ],
                "perfil_xsd": metadados[
                    "perfil_xsd"
                ],
            },
            "municipio_prestador": {
                "codigo_ibge": metadados[
                    "codigo_municipio"
                ],
            },
            "rotas": metadados[
                "rotas"
            ],
            "conteudo": None,
        }

    def transmitir(
        self,
        *,
        payload: dict,
        configuracao,
    ) -> dict:
        """Transmite uma DPS assinada para a SEFIN Nacional."""

        self.validar_configuracao(
            configuracao
        )

        # Disjuntor antes de certificado e antes de rede.
        self.validar_integracao_externa(
            configuracao
        )

        if not isinstance(
            payload,
            dict,
        ):
            raise ErroTransmissaoNfse(
                "Payload SEFIN deve ser dict."
            )

        provider_payload = str(
            payload.get(
                "provider"
            )
            or ""
        ).strip().upper()

        if provider_payload != self.codigo:
            raise ErroTransmissaoNfse(
                "Payload nao pertence ao provider SEFIN_NACIONAL."
            )

        ambiente = str(
            configuracao.ambiente
        ).strip().upper()

        ambiente_payload = str(
            payload.get(
                "ambiente"
            )
            or ""
        ).strip().upper()

        if ambiente_payload != ambiente:
            raise ErroTransmissaoNfse(
                "Ambiente do payload diverge da configuracao fiscal."
            )

        conteudo = payload.get(
            "conteudo"
        )

        if not isinstance(
            conteudo,
            (bytes, bytearray),
        ) or not conteudo:
            raise ErroTransmissaoNfse(
                "Payload SEFIN deve possuir XML DPS assinado em bytes."
            )

        material_certificado = (
            carregar_certificado_a1_do_ambiente()
        )

        try:
            resposta_http = executar_emissao_nfse_http(
                xml_dps_assinado=bytes(
                    conteudo
                ),
                ambiente=ambiente,
                material_certificado=material_certificado,
            )

        except ErroTransmissaoNfse as exc:
            status_code = getattr(
                exc,
                "status_code",
                None,
            )

            corpo = getattr(
                exc,
                "conteudo",
                b"",
            )

            # HTTP 400 da emissao representa rejeicao
            # processavel da DPS. Outros erros tecnicos
            # continuam propagando.
            if status_code != 400 or not corpo:
                raise

            resposta = _normalizar_resposta_ou_falhar(
                status_code=400,
                conteudo=corpo,
            )

            dados_provider = _dados_provider_base(
                resposta
            )

            dados_provider[
                "erros"
            ] = [
                _mensagem_para_dict(
                    erro
                )
                for erro in resposta.erros
            ]

            return {
                "status": "REJEITADA",
                "mensagem": _mensagem_rejeicao(
                    resposta
                ),
                "protocolo": None,
                "numero_nfse": None,
                "dados_provider": dados_provider,
            }

        resposta = _normalizar_resposta_ou_falhar(
            status_code=resposta_http.status_code,
            conteudo=resposta_http.conteudo,
        )

        if not resposta.sucesso:
            raise ErroTransmissaoNfse(
                "SEFIN retornou resposta nao bem-sucedida "
                "fora do fluxo esperado."
            )

        numero_nfse = _extrair_numero_nfse(
            resposta.nfse_xml
        )

        try:
            xml_nfse_texto = resposta.nfse_xml.decode(
                "utf-8"
            )
        except UnicodeDecodeError as exc:
            raise ErroTransmissaoNfse(
                "XML da NFS-e retornado pela SEFIN "
                "nao esta em UTF-8 valido."
            ) from exc

        dados_provider = _dados_provider_base(
            resposta
        )

        dados_provider[
            "nfse_xml"
        ] = xml_nfse_texto

        dados_provider[
            "alertas"
        ] = [
            _mensagem_para_dict(
                alerta
            )
            for alerta in resposta.alertas
        ]

        return {
            "status": "ACEITA",
            "mensagem": _mensagem_sucesso(
                resposta
            ),
            "protocolo": None,
            "numero_nfse": numero_nfse,
            "dados_provider": dados_provider,
        }
