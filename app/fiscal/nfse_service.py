"""Servicos da nova fundacao NFS-e.

Nenhuma funcao deste modulo transmite NFS-e.
Nenhuma funcao deste modulo gera lancamento financeiro.
"""

from sqlalchemy import or_
from sqlalchemy.exc import IntegrityError

import hashlib
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation

from app.extensoes import db
from app.fiscal.configuracao_fiscal_model import ConfiguracaoFiscal
from app.fiscal.nfse_documento_model import (
    AMBIENTES_NFSE,
    NfseDocumento,
)
from app.ordem_servico.ordem_servico_model import (
    OrdemServico,
    OrdemServicoParcela,
)
from app.fiscal.providers.registry import normalizar_codigo_provider
from app.fiscal.providers.resolver import resolver_provider_nfse
from app.fiscal.providers.geisweb_tiete_preparacao import (
    PreparacaoLocalGeisWebInvalida,
    preparar_payload_geisweb_com_xml,
)
from app.fiscal.providers.geisweb_tiete_xsd import (
    validar_xml_envio_lote_rps,
)
from app.fiscal.dps_erp_adapter import montar_dps_canonica_da_os
from app.fiscal.xml.dps_serializer import montar_xml_dps_serializado
from app.fiscal.xml.dps_signer import (
    AssinaturaXmlDpsInvalida,
    assinar_xml_dps,
    validar_assinatura_xml_dps,
)
from app.fiscal.xml.dps_xsd_validator import validar_xml_dps_xsd
from app.fiscal.xsd import obter_caminho_xsd_dps


from app.fiscal.providers.base import STATUS_TRANSMISSAO_NFSE_VALIDOS


class ConflitoIdempotencia(ValueError):
    """A mesma chave foi reutilizada para outro contexto fiscal."""


class PreparacaoNfseInvalida(ValueError):
    """A OS ou a configuracao nao permite preparar a NFS-e."""


class TransmissaoNfseInvalida(ValueError):
    """A fronteira de transmissao recebeu dados invalidos."""


class TransicaoStatusNfseInvalida(ValueError):
    """A tentativa de alterar o ciclo de vida NFS-e e invalida."""


def gerar_chave_emissao_original(ordem_servico_id: int) -> str:
    """Chave legada para a primeira intencao NFS-e de uma OS."""
    return f"nfse:os:{ordem_servico_id}:emissao:original"


def gerar_chave_emissao_parcela(
    ordem_servico_id: int,
    parcela_id: int,
) -> str:
    """Chave deterministica da emissao original de uma parcela."""
    return (
        f"nfse:os:{ordem_servico_id}:"
        f"parcela:{parcela_id}:emissao:original"
    )


def _normalizar_provider(provider):
    if provider is None:
        return None

    valor = str(provider).strip()
    return valor or None


def _validar_documento_existente(
    documento: NfseDocumento,
    *,
    ordem_servico_id: int,
    configuracao_fiscal_id: int,
    ambiente: str,
    provider,
) -> None:
    """Impede reutilizacao da chave para outra intencao fiscal."""

    provider_normalizado = _normalizar_provider(provider)

    mesmo_contexto = (
        documento.ordem_servico_id == ordem_servico_id
        and documento.configuracao_fiscal_id == configuracao_fiscal_id
        and documento.ambiente == ambiente
        and documento.provider == provider_normalizado
    )

    if not mesmo_contexto:
        raise ConflitoIdempotencia(
            "chave_idempotencia ja associada "
            "a contexto fiscal diferente"
        )


def obter_ou_criar_rascunho(
    *,
    ordem_servico_id: int,
    configuracao_fiscal_id: int,
    chave_idempotencia: str,
    ambiente: str = "HOMOLOGACAO",
    provider: str | None = None,
) -> tuple[NfseDocumento, bool]:
    """Retorna a intencao existente ou cria um unico rascunho."""

    chave = (chave_idempotencia or "").strip()

    if not chave:
        raise ValueError("chave_idempotencia e obrigatoria")

    if len(chave) > 160:
        raise ValueError(
            "chave_idempotencia excede 160 caracteres"
        )

    ambiente_normalizado = (ambiente or "").strip().upper()

    if ambiente_normalizado not in AMBIENTES_NFSE:
        raise ValueError("ambiente fiscal invalido")

    provider_normalizado = _normalizar_provider(provider)

    existente = NfseDocumento.query.filter_by(
        chave_idempotencia=chave
    ).first()

    if existente is not None:
        _validar_documento_existente(
            existente,
            ordem_servico_id=ordem_servico_id,
            configuracao_fiscal_id=configuracao_fiscal_id,
            ambiente=ambiente_normalizado,
            provider=provider_normalizado,
        )
        return existente, False

    documento = NfseDocumento(
        ordem_servico_id=ordem_servico_id,
        configuracao_fiscal_id=configuracao_fiscal_id,
        status="RASCUNHO",
        ambiente=ambiente_normalizado,
        provider=provider_normalizado,
        chave_idempotencia=chave,
        mensagem_status=(
            "Rascunho criado pela camada idempotente "
            "da fundacao fiscal."
        ),
    )

    try:
        with db.session.begin_nested():
            db.session.add(documento)
            db.session.flush()

        return documento, True

    except IntegrityError:
        existente = NfseDocumento.query.filter_by(
            chave_idempotencia=chave
        ).first()

        if existente is not None:
            _validar_documento_existente(
                existente,
                ordem_servico_id=ordem_servico_id,
                configuracao_fiscal_id=configuracao_fiscal_id,
                ambiente=ambiente_normalizado,
                provider=provider_normalizado,
            )
            return existente, False

        raise


def _bloquear_documento_nfse_para_rps(
    documento_id: int,
):
    """Carrega e bloqueia o documento durante a reserva do RPS."""
    return (
        NfseDocumento.query
        .filter_by(id=documento_id)
        .with_for_update()
        .one_or_none()
    )


def _bloquear_configuracao_fiscal_para_rps(
    configuracao_fiscal_id: int,
):
    """Carrega e bloqueia a configuracao durante a reserva do RPS."""
    return (
        ConfiguracaoFiscal.query
        .filter_by(id=configuracao_fiscal_id)
        .with_for_update()
        .one_or_none()
    )


def _flush_reserva_rps() -> None:
    """Materializa a reserva sem assumir o commit da transacao."""
    db.session.flush()


def reservar_rps_nfse(
    *,
    documento: NfseDocumento,
    configuracao: ConfiguracaoFiscal,
) -> tuple[NfseDocumento, bool]:
    """Reserva de forma idempotente a numeracao RPS de um documento.

    D24F02-B7-A4:
    - bloqueia documento e configuracao fiscal para evitar corrida;
    - reutiliza a numeracao quando ela ja estiver reservada;
    - usa configuracao.serie_rps e configuracao.proximo_rps;
    - incrementa proximo_rps somente em uma nova reserva;
    - nao executa commit;
    - nao transmite;
    - nao monta XML;
    - nao altera financeiro.

    O chamador continua responsavel pelo commit ou rollback da transacao.
    """

    if documento is None:
        raise PreparacaoNfseInvalida(
            "Documento NFS-e nao informado para reserva de RPS."
        )

    if configuracao is None:
        raise PreparacaoNfseInvalida(
            "Configuracao fiscal nao informada para reserva de RPS."
        )

    documento_id = getattr(
        documento,
        "id",
        None,
    )

    configuracao_id = getattr(
        configuracao,
        "id",
        None,
    )

    if documento_id is None:
        raise PreparacaoNfseInvalida(
            "Documento NFS-e deve estar persistido antes da reserva de RPS."
        )

    if configuracao_id is None:
        raise PreparacaoNfseInvalida(
            "Configuracao fiscal deve estar persistida antes da reserva de RPS."
        )

    documento_bloqueado = _bloquear_documento_nfse_para_rps(
        documento_id
    )

    if documento_bloqueado is None:
        raise PreparacaoNfseInvalida(
            "Documento NFS-e nao encontrado para reserva de RPS."
        )

    configuracao_bloqueada = (
        _bloquear_configuracao_fiscal_para_rps(
            configuracao_id
        )
    )

    if configuracao_bloqueada is None:
        raise PreparacaoNfseInvalida(
            "Configuracao fiscal nao encontrada para reserva de RPS."
        )

    if (
        documento_bloqueado.configuracao_fiscal_id
        != configuracao_bloqueada.id
    ):
        raise PreparacaoNfseInvalida(
            "Documento NFS-e nao pertence a configuracao fiscal informada."
        )

    if not documento_bloqueado.pode_ser_editada:
        raise PreparacaoNfseInvalida(
            "Documento NFS-e nao permite reserva de RPS."
        )

    numero_atual = getattr(
        documento_bloqueado,
        "numero_rps",
        None,
    )

    serie_atual = str(
        getattr(
            documento_bloqueado,
            "serie_rps",
            "",
        )
        or ""
    ).strip()

    # Reserva existente valida: idempotencia pura.
    if numero_atual is not None and serie_atual:
        if (
            isinstance(numero_atual, bool)
            or not isinstance(numero_atual, int)
            or numero_atual < 1
        ):
            raise PreparacaoNfseInvalida(
                "Numero RPS previamente reservado e invalido."
            )

        return documento_bloqueado, False

    # Estado parcial nao pode ser completado silenciosamente.
    if numero_atual is not None or serie_atual:
        raise PreparacaoNfseInvalida(
            "Documento NFS-e possui reserva RPS parcial ou inconsistente."
        )

    serie = str(
        getattr(
            configuracao_bloqueada,
            "serie_rps",
            "",
        )
        or ""
    ).strip()

    if not serie:
        raise PreparacaoNfseInvalida(
            "Serie RPS da configuracao fiscal nao informada."
        )

    proximo_rps = getattr(
        configuracao_bloqueada,
        "proximo_rps",
        None,
    )

    if (
        isinstance(proximo_rps, bool)
        or not isinstance(proximo_rps, int)
        or proximo_rps < 1
    ):
        raise PreparacaoNfseInvalida(
            "Proximo RPS da configuracao fiscal e invalido."
        )

    documento_bloqueado.serie_rps = serie
    documento_bloqueado.numero_rps = proximo_rps

    configuracao_bloqueada.proximo_rps = (
        proximo_rps + 1
    )

    _flush_reserva_rps()

    return documento_bloqueado, True


def preparar_payload_nfse(
    *,
    documento: NfseDocumento,
    ordem_servico: OrdemServico,
    configuracao: ConfiguracaoFiscal,
) -> dict:
    """Prepara localmente o payload tecnico de uma NFS-e.

    Esta funcao NAO:
    - transmite NFS-e;
    - realiza chamadas externas;
    - gera ou consome RPS;
    - incrementa proximo_rps;
    - altera status do documento;
    - realiza commit;
    - cria lancamento financeiro.
    """

    if documento is None:
        raise PreparacaoNfseInvalida(
            "Documento NFS-e nao informado."
        )

    if ordem_servico is None:
        raise PreparacaoNfseInvalida(
            "Ordem de servico nao informada."
        )

    if configuracao is None:
        raise PreparacaoNfseInvalida(
            "Configuracao fiscal nao informada."
        )

    if not documento.pode_ser_editada:
        raise PreparacaoNfseInvalida(
            "Documento NFS-e nao permite preparacao local."
        )

    if ordem_servico.status != "concluida":
        raise PreparacaoNfseInvalida(
            "A NFS-e somente pode ser preparada para OS concluida."
        )

    if ordem_servico.situacao_fiscal != "EMITIR_NFSE":
        raise PreparacaoNfseInvalida(
            "A OS nao possui decisao fiscal EMITIR_NFSE."
        )

    if documento.ordem_servico_id != ordem_servico.id:
        raise PreparacaoNfseInvalida(
            "Documento NFS-e nao pertence a ordem de servico informada."
        )

    if documento.configuracao_fiscal_id != configuracao.id:
        raise PreparacaoNfseInvalida(
            "Documento NFS-e nao pertence a configuracao fiscal informada."
        )

    ambiente_configuracao = (
        configuracao.ambiente or "HOMOLOGACAO"
    ).strip().upper()

    ambiente_documento = (
        documento.ambiente or ""
    ).strip().upper()

    if ambiente_configuracao not in AMBIENTES_NFSE:
        raise PreparacaoNfseInvalida(
            "Ambiente da configuracao fiscal e invalido."
        )

    if ambiente_documento != ambiente_configuracao:
        raise PreparacaoNfseInvalida(
            "Ambiente do documento diverge da configuracao fiscal."
        )

    provider_configuracao = normalizar_codigo_provider(
        configuracao.provider
    )

    provider_documento = normalizar_codigo_provider(
        documento.provider
    )

    if provider_documento != provider_configuracao:
        raise PreparacaoNfseInvalida(
            "Provider do documento diverge da configuracao fiscal."
        )

    provider = resolver_provider_nfse(configuracao)

    payload = provider.preparar_payload(
        documento=documento,
        ordem_servico=ordem_servico,
        configuracao=configuracao,
    )

    if not isinstance(payload, dict):
        raise PreparacaoNfseInvalida(
            "Provider NFS-e retornou payload local invalido."
        )

    return payload


def preparar_payload_nfse_com_geisweb(
    *,
    documento: NfseDocumento,
    ordem_servico: OrdemServico,
    configuracao_fiscal: ConfiguracaoFiscal,
    configuracao_institucional,
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
) -> dict:
    """Prepara localmente o XML do provider GEISWEB_TIETE.

    Nenhuma assinatura, certificado ou comunicacao externa ocorre aqui.
    """

    payload = preparar_payload_nfse(
        documento=documento,
        ordem_servico=ordem_servico,
        configuracao=configuracao_fiscal,
    )

    provider = normalizar_codigo_provider(
        payload.get("provider")
    )

    if provider != "GEISWEB_TIETE":
        raise PreparacaoNfseInvalida(
            "Preparacao GeisWeb recebeu payload de outro provider."
        )

    try:
        return preparar_payload_geisweb_com_xml(
            payload=payload,
            documento=documento,
            ordem_servico=ordem_servico,
            configuracao_institucional=configuracao_institucional,
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

    except PreparacaoLocalGeisWebInvalida as exc:
        raise PreparacaoNfseInvalida(
            f"Falha na preparacao local GeisWeb: {exc}"
        ) from exc

_STATUS_DOCUMENTO_POR_RESULTADO_TRANSMISSAO = {
    "PROCESSANDO": "PROCESSANDO",
    "ACEITA": "AUTORIZADA",
    "REJEITADA": "REJEITADA",
}


def preparar_payload_nfse_com_dps(
    *,
    documento: NfseDocumento,
    ordem_servico: OrdemServico,
    configuracao_fiscal: ConfiguracaoFiscal,
    configuracao_institucional,
    versao_layout: str,
    tipo_emitente,
    municipio_incidencia_ibge,
    iss: dict,
    totais_tributos: dict,
    municipio_prestacao_ibge=None,
    ibs_cbs=None,
    data_emissao=None,
    versao_aplicativo="ERP-JSP",
    material_certificado=None,
) -> dict:
    """Integra ERP -> DPS -> XML -> XSD ao payload tecnico NFS-e.

    D24F02-B7-A3:
    - preserva a preparacao tecnica existente do provider;
    - nao transmite;
    - preserva o fluxo B7 quando nao ha certificado;
    - quando informado, assina a DPS com XMLDSIG;
    - valida novamente o XML assinado contra o XSD;
    - nao realiza HTTP;
    - nao reserva nem consome novo RPS;
    - somente publica conteudo apos validacao XSD positiva.
    """

    payload = preparar_payload_nfse(
        documento=documento,
        ordem_servico=ordem_servico,
        configuracao=configuracao_fiscal,
    )

    dps_canonica = montar_dps_canonica_da_os(
        documento=documento,
        ordem_servico=ordem_servico,
        configuracao=configuracao_institucional,
        configuracao_fiscal=configuracao_fiscal,
        versao_layout=versao_layout,
        tipo_emitente=tipo_emitente,
        municipio_incidencia_ibge=municipio_incidencia_ibge,
        iss=iss,
        totais_tributos=totais_tributos,
        municipio_prestacao_ibge=municipio_prestacao_ibge,
        ibs_cbs=ibs_cbs,
        data_emissao=data_emissao,
        versao_aplicativo=versao_aplicativo,
    )

    xml_dps = montar_xml_dps_serializado(
        dps_canonica
    )

    caminho_xsd = obter_caminho_xsd_dps(
        versao_layout
    )

    resultado_xsd = validar_xml_dps_xsd(
        xml_dps,
        caminho_xsd,
    )

    if not resultado_xsd.valido:
        erros = "; ".join(
            str(erro)
            for erro in resultado_xsd.erros
        )

        mensagem = "XML da DPS invalido perante o XSD."

        if erros:
            mensagem = f"{mensagem} {erros}"

        raise PreparacaoNfseInvalida(
            mensagem
        )

    xml_conteudo = xml_dps

    if material_certificado is not None:
        try:
            xml_conteudo = assinar_xml_dps(
                xml_dps,
                material_certificado=material_certificado,
            )
        except AssinaturaXmlDpsInvalida as exc:
            raise PreparacaoNfseInvalida(
                f"Falha ao assinar XML da DPS: {exc}"
            ) from exc

        resultado_xsd_assinado = validar_xml_dps_xsd(
            xml_conteudo,
            caminho_xsd,
        )

        if not resultado_xsd_assinado.valido:
            erros = "; ".join(
                str(erro)
                for erro in resultado_xsd_assinado.erros
            )

            mensagem = (
                "XML assinado da DPS invalido perante o XSD."
            )

            if erros:
                mensagem = f"{mensagem} {erros}"

            raise PreparacaoNfseInvalida(
                mensagem
            )

    payload["conteudo"] = xml_conteudo

    return payload


def _commit_preparacao_local_nfse() -> None:
    """Confirma a preparacao fiscal local."""
    db.session.commit()


def _rollback_preparacao_local_nfse() -> None:
    """Reverte integralmente a preparacao fiscal local."""
    db.session.rollback()


def preparar_documento_nfse_com_dps(
    *,
    documento: NfseDocumento,
    ordem_servico: OrdemServico,
    configuracao_fiscal: ConfiguracaoFiscal,
    configuracao_institucional,
    versao_layout: str,
    tipo_emitente,
    municipio_incidencia_ibge,
    iss: dict,
    totais_tributos: dict,
    municipio_prestacao_ibge=None,
    ibs_cbs=None,
    data_emissao=None,
    versao_aplicativo="ERP-JSP",
    material_certificado=None,
) -> tuple[NfseDocumento, dict]:
    """Orquestra a preparacao fiscal local completa da DPS.

    D24F02-B7-A5:
    - reserva RPS de forma idempotente;
    - monta DPS canonica;
    - serializa XML;
    - valida XML contra XSD versionado;
    - publica o XML somente no payload em memoria;
    - marca o documento como PREPARADA;
    - confirma tudo em uma unica transacao;
    - executa rollback integral em qualquer falha;
    - nao transmite;
    - opcionalmente assina a DPS com certificado A1 em memoria;
    - preserva a preparacao sem assinatura quando nao informado;
    - nao realiza HTTP;
    - nao altera financeiro.
    """

    try:
        documento_reservado, _ = reservar_rps_nfse(
            documento=documento,
            configuracao=configuracao_fiscal,
        )

        payload = preparar_payload_nfse_com_dps(
            documento=documento_reservado,
            ordem_servico=ordem_servico,
            configuracao_fiscal=configuracao_fiscal,
            configuracao_institucional=configuracao_institucional,
            versao_layout=versao_layout,
            tipo_emitente=tipo_emitente,
            municipio_incidencia_ibge=municipio_incidencia_ibge,
            iss=iss,
            totais_tributos=totais_tributos,
            municipio_prestacao_ibge=municipio_prestacao_ibge,
            ibs_cbs=ibs_cbs,
            data_emissao=data_emissao,
            versao_aplicativo=versao_aplicativo,
            material_certificado=material_certificado,
        )

        documento_reservado.status = "PREPARADA"
        if material_certificado is None:
            documento_reservado.mensagem_status = (
                "DPS preparada localmente e validada contra o XSD. "
                "Nenhuma NFS-e foi transmitida."
            )
        else:
            documento_reservado.mensagem_status = (
                "DPS preparada localmente, assinada digitalmente "
                "e validada contra o XSD. "
                "Nenhuma NFS-e foi transmitida."
            )

        _commit_preparacao_local_nfse()

        return documento_reservado, payload

    except Exception:
        _rollback_preparacao_local_nfse()
        raise



def preparar_documento_nfse_com_geisweb(
    *,
    documento: NfseDocumento,
    ordem_servico: OrdemServico,
    configuracao_fiscal: ConfiguracaoFiscal,
    configuracao_institucional,
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
) -> tuple[NfseDocumento, dict]:
    """Orquestra a preparacao fiscal local do GEISWEB_TIETE.

    - reserva RPS de forma idempotente;
    - monta EnviaLoteRps;
    - valida XML contra o XSD GeisWeb;
    - publica o XML somente no payload em memoria;
    - marca o documento como PREPARADA;
    - confirma tudo em uma unica transacao;
    - executa rollback integral em qualquer falha;
    - nao assina;
    - nao carrega certificado;
    - nao realiza HTTP;
    - nao transmite NFS-e.
    """

    try:
        documento_reservado, _ = reservar_rps_nfse(
            documento=documento,
            configuracao=configuracao_fiscal,
        )

        payload = preparar_payload_nfse_com_geisweb(
            documento=documento_reservado,
            ordem_servico=ordem_servico,
            configuracao_fiscal=configuracao_fiscal,
            configuracao_institucional=configuracao_institucional,
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

        conteudo = payload.get("conteudo")

        if not isinstance(
            conteudo,
            (bytes, bytearray),
        ) or not conteudo:
            raise PreparacaoNfseInvalida(
                "Payload GeisWeb nao possui XML valido "
                "para persistencia."
            )

        xml_envio = bytes(conteudo)

        documento_reservado.xml_envio = xml_envio
        documento_reservado.xml_envio_sha256 = hashlib.sha256(
            xml_envio
        ).hexdigest()
        documento_reservado.preparado_em = datetime.now(
            timezone.utc
        )

        documento_reservado.status = "PREPARADA"
        documento_reservado.mensagem_status = (
            "NFS-e GeisWeb preparada localmente e validada "
            "contra o XSD. Artefato fiscal persistido. "
            "Nenhuma NFS-e foi transmitida."
        )

        _commit_preparacao_local_nfse()

        return documento_reservado, payload

    except Exception:
        _rollback_preparacao_local_nfse()
        raise

def _normalizar_resultado_transmissao_nfse(
    resultado,
) -> dict:
    """Valida e normaliza o retorno canonico de um provider NFS-e."""

    if not isinstance(resultado, dict):
        raise TransmissaoNfseInvalida(
            "Provider NFS-e deve retornar dict na transmissao."
        )

    status = resultado.get("status")

    if not isinstance(status, str) or not status.strip():
        raise TransmissaoNfseInvalida(
            "Resultado NFS-e deve informar status."
        )

    status = status.strip().upper()

    if status not in STATUS_TRANSMISSAO_NFSE_VALIDOS:
        raise TransmissaoNfseInvalida(
            f"Status de transmissao NFS-e invalido: {status}."
        )

    campos_texto = {}

    for campo in (
        "mensagem",
        "protocolo",
        "numero_nfse",
    ):
        valor = resultado.get(campo)

        if valor is not None and not isinstance(valor, str):
            raise TransmissaoNfseInvalida(
                f"Campo {campo} do resultado NFS-e deve ser texto ou None."
            )

        if isinstance(valor, str):
            valor = valor.strip() or None

        campos_texto[campo] = valor

    dados_provider = resultado.get(
        "dados_provider",
        {},
    )

    if dados_provider is None:
        dados_provider = {}

    if not isinstance(dados_provider, dict):
        raise TransmissaoNfseInvalida(
            "Campo dados_provider deve ser dict."
        )

    return {
        "status": status,
        "mensagem": campos_texto["mensagem"],
        "protocolo": campos_texto["protocolo"],
        "numero_nfse": campos_texto["numero_nfse"],
        "dados_provider": dict(dados_provider),
    }


def aplicar_resultado_transmissao_nfse(
    *,
    documento: NfseDocumento,
    resultado: dict,
) -> NfseDocumento:
    """Aplica ao documento um resultado canonico de transmissao.

    D24F01-C10H:
    - nao realiza transmissao;
    - nao executa commit;
    - nao consome RPS;
    - nao altera financeiro;
    - preserva o estado fiscal em erros tecnicos;
    - permite somente transicoes externas conhecidas.
    """

    if documento is None:
        raise TransicaoStatusNfseInvalida(
            "Documento NFS-e nao informado."
        )

    resultado_normalizado = _normalizar_resultado_transmissao_nfse(
        resultado
    )

    status_resultado = resultado_normalizado["status"]

    # ERRO representa falha tecnica/operacional.
    # Nao e um estado fiscal persistivel do documento.
    if status_resultado == "ERRO":
        return documento

    status_atual = str(
        getattr(documento, "status", "") or ""
    ).strip().upper()

    if status_atual not in {
        "PENDENTE_ENVIO",
        "PROCESSANDO",
    }:
        raise TransicaoStatusNfseInvalida(
            "Documento NFS-e em estado "
            f"{status_atual or '<VAZIO>'} nao pode receber "
            "resultado de transmissao."
        )

    novo_status = _STATUS_DOCUMENTO_POR_RESULTADO_TRANSMISSAO.get(
        status_resultado
    )

    if novo_status is None:
        raise TransicaoStatusNfseInvalida(
            "Resultado de transmissao sem transicao fiscal conhecida: "
            f"{status_resultado}."
        )

    numero_nfse = resultado_normalizado["numero_nfse"]

    if novo_status == "AUTORIZADA" and not numero_nfse:
        raise TransicaoStatusNfseInvalida(
            "NFS-e autorizada deve possuir numero_nfse."
        )

    dados_provider = resultado_normalizado["dados_provider"]

    chave_acesso = dados_provider.get(
        "chave_acesso"
    )

    if chave_acesso is None:
        chave_acesso = dados_provider.get("chave_nacional")

    if chave_acesso is not None:
        if not isinstance(
            chave_acesso,
            str,
        ):
            raise TransicaoStatusNfseInvalida(
                "chave_acesso do provider deve ser texto ou None."
            )

        chave_acesso = chave_acesso.strip() or None

    if chave_acesso is not None and len(chave_acesso) > 100:
        raise TransicaoStatusNfseInvalida(
            "chave_acesso excede 100 caracteres."
        )
    codigo_verificacao = dados_provider.get("codigo_verificacao")

    if codigo_verificacao is not None:
        if not isinstance(codigo_verificacao, str):
            raise TransicaoStatusNfseInvalida(
                "codigo_verificacao do provider deve ser texto ou None."
            )

        codigo_verificacao = codigo_verificacao.strip() or None

    if (
        codigo_verificacao is not None
        and len(codigo_verificacao) > 100
    ):
        raise TransicaoStatusNfseInvalida(
            "codigo_verificacao excede 100 caracteres."
        )

    # Todas as validacoes ocorrem antes de qualquer mutacao.
    documento.status = novo_status
    documento.mensagem_status = resultado_normalizado["mensagem"]

    protocolo = resultado_normalizado["protocolo"]

    if protocolo is not None:
        documento.protocolo = protocolo

    if novo_status == "AUTORIZADA":
        documento.numero_nfse = numero_nfse

        if codigo_verificacao is not None:
            documento.codigo_verificacao = codigo_verificacao

        if chave_acesso is not None:
            documento.chave_acesso = chave_acesso

    return documento



def reconstruir_payload_geisweb_para_envio(
    *,
    documento: NfseDocumento,
    ordem_servico: OrdemServico,
    configuracao: ConfiguracaoFiscal,
) -> dict:
    """Reconstr?i o envelope t?cnico usando o XML fiscal persistido.

    H3-S5O:
    - nao gera novo XML;
    - nao reserva novo RPS;
    - valida SHA-256 do artefato persistido;
    - valida novamente o XML contra o XSD GeisWeb;
    - reconstr?i somente metadados de transporte;
    - nao transmite;
    - nao executa commit.
    """

    if documento is None:
        raise TransmissaoNfseInvalida(
            "Documento NFS-e nao informado."
        )

    if ordem_servico is None:
        raise TransmissaoNfseInvalida(
            "Ordem de servico nao informada."
        )

    if configuracao is None:
        raise TransmissaoNfseInvalida(
            "Configuracao fiscal nao informada."
        )

    status_atual = str(
        getattr(documento, "status", "") or ""
    ).strip().upper()

    if status_atual not in {
        "PREPARADA",
        "PENDENTE_ENVIO",
    }:
        raise TransicaoStatusNfseInvalida(
            "Documento NFS-e em estado "
            f"{status_atual or '<VAZIO>'} nao possui "
            "artefato liberado para envio."
        )

    provider_documento = normalizar_codigo_provider(
        getattr(documento, "provider", None)
    )

    provider_configuracao = normalizar_codigo_provider(
        getattr(configuracao, "provider", None)
    )

    if provider_documento != "GEISWEB_TIETE":
        raise TransmissaoNfseInvalida(
            "Documento nao pertence ao provider GEISWEB_TIETE."
        )

    if provider_configuracao != provider_documento:
        raise TransmissaoNfseInvalida(
            "Provider atual diverge do provider do documento preparado."
        )

    ambiente_documento = str(
        getattr(documento, "ambiente", "") or ""
    ).strip().upper()

    ambiente_configuracao = str(
        getattr(configuracao, "ambiente", "") or ""
    ).strip().upper()

    if (
        not ambiente_documento
        or ambiente_documento != ambiente_configuracao
    ):
        raise TransmissaoNfseInvalida(
            "Ambiente fiscal atual diverge do documento preparado."
        )

    conteudo = getattr(
        documento,
        "xml_envio",
        None,
    )

    if not isinstance(
        conteudo,
        (bytes, bytearray),
    ) or not conteudo:
        raise TransmissaoNfseInvalida(
            "Documento NFS-e nao possui XML de envio persistido."
        )

    xml_envio = bytes(conteudo)

    hash_persistido = str(
        getattr(
            documento,
            "xml_envio_sha256",
            "",
        )
        or ""
    ).strip().lower()

    hash_calculado = hashlib.sha256(
        xml_envio
    ).hexdigest()

    if (
        len(hash_persistido) != 64
        or hash_persistido != hash_calculado
    ):
        raise TransmissaoNfseInvalida(
            "Integridade do XML fiscal persistido nao confere."
        )

    validacao = validar_xml_envio_lote_rps(
        xml_envio
    )

    if not validacao.valido:
        erros = "; ".join(
            str(erro)
            for erro in validacao.erros
        )

        mensagem = (
            "XML fiscal persistido nao e mais valido "
            "perante o XSD GeisWeb."
        )

        if erros:
            mensagem = f"{mensagem} {erros}"

        raise TransmissaoNfseInvalida(
            mensagem
        )

    provider = resolver_provider_nfse(
        configuracao
    )

    payload = provider.preparar_payload(
        documento=documento,
        ordem_servico=ordem_servico,
        configuracao=configuracao,
    )

    if not isinstance(payload, dict):
        raise TransmissaoNfseInvalida(
            "Provider GeisWeb retornou payload tecnico invalido."
        )

    if normalizar_codigo_provider(
        payload.get("provider")
    ) != "GEISWEB_TIETE":
        raise TransmissaoNfseInvalida(
            "Payload reconstruido pertence a outro provider."
        )

    payload["conteudo"] = xml_envio

    return payload

def liberar_documento_nfse_geisweb_para_envio(
    *,
    documento: NfseDocumento,
    ordem_servico: OrdemServico,
    configuracao: ConfiguracaoFiscal,
) -> NfseDocumento:
    """Libera artefato GeisWeb persistido para a fronteira de envio.

    H3-S5P:
    - usa somente o XML fiscal persistido;
    - revalida integridade, XSD, provider e ambiente via H3-S5O;
    - nao gera novo XML;
    - nao reserva novo RPS;
    - nao assina novamente;
    - nao transmite;
    - nao executa commit;
    - somente apos todas as validacoes muda
      PREPARADA para PENDENTE_ENVIO.
    """

    payload = reconstruir_payload_geisweb_para_envio(
        documento=documento,
        ordem_servico=ordem_servico,
        configuracao=configuracao,
    )

    return preparar_nfse_para_envio(
        documento=documento,
        payload=payload,
    )


def preparar_nfse_para_envio(
    *,
    documento: NfseDocumento,
    payload: dict,
) -> NfseDocumento:
    """Transiciona uma DPS preparada para a fronteira de envio.

    D24F02-B7-FINAL:
    - aceita somente documento PREPARADA;
    - exige payload tecnico ja montado;
    - exige conteudo XML presente;
    - exige assinatura XMLDSIG criptograficamente valida;
    - muda somente para PENDENTE_ENVIO;
    - nao executa commit;
    - nao transmite;
    - nao assina;
    - nao acessa certificado;
    - nao realiza HTTP;
    - nao altera financeiro.
    """

    if documento is None:
        raise TransicaoStatusNfseInvalida(
            "Documento NFS-e nao informado."
        )

    if not isinstance(payload, dict):
        raise TransicaoStatusNfseInvalida(
            "Payload NFS-e deve ser um dict."
        )

    status_atual = str(
        getattr(documento, "status", "") or ""
    ).strip().upper()

    if status_atual != "PREPARADA":
        raise TransicaoStatusNfseInvalida(
            "Documento NFS-e em estado "
            f"{status_atual or '<VAZIO>'} nao pode ser "
            "marcado como PENDENTE_ENVIO."
        )

    conteudo = payload.get("conteudo")

    if not isinstance(
        conteudo,
        (bytes, bytearray),
    ) or not conteudo:
        raise TransicaoStatusNfseInvalida(
            "Payload NFS-e nao possui XML preparado para envio."
        )

    provider_payload = normalizar_codigo_provider(
        payload.get("provider")
    )

    if provider_payload in {
        None,
        "SEFIN_NACIONAL",
    }:
        try:
            validar_assinatura_xml_dps(
                bytes(conteudo)
            )
        except AssinaturaXmlDpsInvalida as exc:
            raise TransicaoStatusNfseInvalida(
                "Payload NFS-e possui assinatura XMLDSIG invalida: "
                f"{exc}"
            ) from exc

    elif provider_payload == "GEISWEB_TIETE":
        validacao_geisweb = validar_xml_envio_lote_rps(
            bytes(conteudo)
        )

        if not validacao_geisweb.valido:
            erros = "; ".join(
                str(erro)
                for erro in validacao_geisweb.erros
            )

            mensagem = (
                "Payload GeisWeb possui XML invalido perante o XSD."
            )

            if erros:
                mensagem = f"{mensagem} {erros}"

            raise TransicaoStatusNfseInvalida(
                mensagem
            )

    else:
        raise TransicaoStatusNfseInvalida(
            "Provider do payload NFS-e nao suportado no gate de envio."
        )

    documento.status = "PENDENTE_ENVIO"
    documento.mensagem_status = (
        "DPS preparada e liberada para a fronteira de transmissao. "
        "Nenhuma NFS-e foi transmitida nesta etapa."
    )

    return documento


def validar_elegibilidade_transmissao_geisweb(
    *,
    documento: NfseDocumento,
    ordem_servico: OrdemServico,
    configuracao: ConfiguracaoFiscal,
) -> dict:
    """Valida a elegibilidade tecnica para futura transmissao GeisWeb.

    H3-S5Q:
    - aceita somente documento PENDENTE_ENVIO;
    - respeita o disjuntor integracao_ativa;
    - usa somente o XML fiscal persistido;
    - revalida hash, XSD, provider e ambiente via H3-S5O;
    - nao gera novo XML;
    - nao reserva novo RPS;
    - nao altera status;
    - nao executa commit;
    - nao transmite;
    - nao realiza HTTP ou SOAP.
    """

    if documento is None:
        raise TransmissaoNfseInvalida(
            "Documento NFS-e nao informado."
        )

    if configuracao is None:
        raise TransmissaoNfseInvalida(
            "Configuracao fiscal nao informada."
        )

    status_atual = str(
        getattr(documento, "status", "") or ""
    ).strip().upper()

    if status_atual != "PENDENTE_ENVIO":
        raise TransicaoStatusNfseInvalida(
            "Documento NFS-e em estado "
            f"{status_atual or '<VAZIO>'} nao esta elegivel "
            "para transmissao."
        )

    if getattr(
        configuracao,
        "integracao_ativa",
        False,
    ) is not True:
        raise TransmissaoNfseInvalida(
            "Integracao externa NFS-e esta desativada."
        )

    return reconstruir_payload_geisweb_para_envio(
        documento=documento,
        ordem_servico=ordem_servico,
        configuracao=configuracao,
    )


def transmitir_documento_nfse_geisweb_controlado(
    *,
    documento: NfseDocumento,
    ordem_servico: OrdemServico,
    configuracao: ConfiguracaoFiscal,
    autorizar_transmissao: bool = False,
) -> tuple[NfseDocumento, dict]:
    """Orquestra de forma controlada a transmissao GeisWeb.

    H3-S5R:
    - exige autorizacao explicita por chamada;
    - preserva o disjuntor integracao_ativa do H3-S5Q;
    - usa somente o XML fiscal persistido;
    - reconstroi e revalida o payload antes da transmissao;
    - nao gera novo XML;
    - nao reserva novo RPS;
    - nao executa commit;
    - aplica somente o resultado canonico existente.

    Com autorizar_transmissao=False, nenhuma fronteira externa
    pode ser alcan?ada.
    """

    if autorizar_transmissao is not True:
        raise TransmissaoNfseInvalida(
            "Transmissao externa GeisWeb nao autorizada nesta chamada."
        )

    payload = validar_elegibilidade_transmissao_geisweb(
        documento=documento,
        ordem_servico=ordem_servico,
        configuracao=configuracao,
    )

    return transmitir_e_aplicar_nfse(
        documento=documento,
        payload=payload,
        configuracao=configuracao,
    )


def transmitir_payload_nfse(
    *,
    payload: dict,
    configuracao: ConfiguracaoFiscal,
) -> dict:
    """Executa a fronteira externa de transmissao da NFS-e.

    D24F01-C10E:
    - recebe somente payload ja preparado localmente;
    - resolve e valida o provider configurado;
    - respeita obrigatoriamente o disjuntor integracao_ativa;
    - nao prepara novo payload;
    - nao persiste alteracoes;
    - nao consome RPS;
    - nao altera financeiro.

    Neste estagio nao existe provider municipal real nem transporte HTTP.
    """

    if configuracao is None:
        raise TransmissaoNfseInvalida(
            "Configuracao fiscal nao informada."
        )

    if not isinstance(payload, dict):
        raise TransmissaoNfseInvalida(
            "Payload NFS-e deve ser um dict."
        )

    provider = resolver_provider_nfse(configuracao)

    provider.validar_integracao_externa(configuracao)

    resultado = provider.transmitir(
        payload=payload,
        configuracao=configuracao,
    )

    return _normalizar_resultado_transmissao_nfse(
        resultado
    )

def transmitir_e_aplicar_nfse(
    *,
    documento: NfseDocumento,
    payload: dict,
    configuracao: ConfiguracaoFiscal,
) -> tuple[NfseDocumento, dict]:
    """Orquestra transmissao e aplicacao do resultado NFS-e.

    D24F01-C10I:
    - valida o documento antes da fronteira externa;
    - transmite somente payload ja preparado;
    - aplica somente resultado canonico;
    - nao executa commit;
    - nao consome ou incrementa RPS;
    - nao altera financeiro.

    Erros tecnicos do provider propagam sem mutar o documento.
    """

    if documento is None:
        raise TransicaoStatusNfseInvalida(
            "Documento NFS-e nao informado."
        )

    status_atual = str(
        getattr(documento, "status", "") or ""
    ).strip().upper()

    if status_atual != "PENDENTE_ENVIO":
        raise TransicaoStatusNfseInvalida(
            "Documento NFS-e em estado "
            f"{status_atual or '<VAZIO>'} nao pode ser transmitido."
        )

    resultado = transmitir_payload_nfse(
        payload=payload,
        configuracao=configuracao,
    )

    aplicar_resultado_transmissao_nfse(
        documento=documento,
        resultado=resultado,
    )

    return documento, resultado


def _valor_fiscal_da_parcela(
    parcela: OrdemServicoParcela,
) -> Decimal:
    """Normaliza e valida o valor fiscal de uma parcela."""

    try:
        valor = Decimal(
            str(getattr(parcela, "valor", None) or "0")
        ).quantize(Decimal("0.01"))
    except (
        InvalidOperation,
        TypeError,
        ValueError,
    ) as exc:
        raise PreparacaoNfseInvalida(
            "Valor da parcela e invalido para emissao fiscal."
        ) from exc

    if valor <= Decimal("0"):
        raise PreparacaoNfseInvalida(
            "Valor da parcela deve ser maior que zero."
        )

    return valor


def _validar_documento_parcela_existente(
    documento: NfseDocumento,
    *,
    ordem_servico_id: int,
    parcela_id: int,
    configuracao_fiscal_id: int,
    ambiente: str,
    provider,
    chave_idempotencia: str,
    valor_servicos: Decimal,
) -> None:
    """Impede que uma parcela seja reutilizada em outro contexto."""

    provider_normalizado = _normalizar_provider(provider)

    try:
        valor_documento = Decimal(
            str(documento.valor_servicos or "0")
        ).quantize(Decimal("0.01"))
    except (InvalidOperation, TypeError, ValueError):
        valor_documento = Decimal("0")

    mesmo_contexto = (
        documento.ordem_servico_id == ordem_servico_id
        and documento.ordem_servico_parcela_id == parcela_id
        and documento.configuracao_fiscal_id
        == configuracao_fiscal_id
        and documento.ambiente == ambiente
        and documento.provider == provider_normalizado
        and documento.chave_idempotencia
        == chave_idempotencia
        and valor_documento == valor_servicos
    )

    if not mesmo_contexto:
        raise ConflitoIdempotencia(
            "Parcela ja associada a contexto fiscal diferente."
        )


def preparar_nfse_da_parcela(
    ordem_servico_id: int,
    parcela_id: int,
) -> tuple[NfseDocumento, bool]:
    """Cria ou recupera a intencao NFS-e de uma parcela da OS.

    D24F04:
    - exige OS concluida e decisao EMITIR_NFSE;
    - exige parcela ativa pertencente a OS;
    - usa exatamente o valor financeiro da parcela;
    - uma parcela possui no maximo uma intencao fiscal original;
    - permite varias NFS-e na mesma OS, uma por parcela;
    - adota com seguranca o rascunho legado da OS quando ele
      ainda nao consumiu RPS nem possui XML;
    - nao reserva RPS;
    - nao gera XML;
    - nao transmite;
    - nao altera financeiro.
    """

    ordem = db.session.get(
        OrdemServico,
        ordem_servico_id,
    )

    if ordem is None:
        raise PreparacaoNfseInvalida(
            f"Ordem de servico {ordem_servico_id} nao encontrada."
        )

    if ordem.status != "concluida":
        raise PreparacaoNfseInvalida(
            "A NFS-e somente pode ser criada para OS concluida."
        )

    if ordem.situacao_fiscal != "EMITIR_NFSE":
        raise PreparacaoNfseInvalida(
            "A OS nao possui decisao fiscal EMITIR_NFSE."
        )

    parcela = OrdemServicoParcela.query.filter_by(
        id=parcela_id,
        ordem_servico_id=ordem_servico_id,
        ativo=True,
    ).first()

    if parcela is None:
        raise PreparacaoNfseInvalida(
            "Parcela nao encontrada ou nao pertence a OS."
        )

    valor_servicos = _valor_fiscal_da_parcela(
        parcela
    )

    configuracoes = ConfiguracaoFiscal.query.filter_by(
        ativo=True
    ).all()

    if len(configuracoes) != 1:
        raise PreparacaoNfseInvalida(
            "Deve existir exatamente uma configuracao fiscal ativa."
        )

    configuracao = configuracoes[0]

    ambiente = (
        configuracao.ambiente or "HOMOLOGACAO"
    ).strip().upper()

    if ambiente not in AMBIENTES_NFSE:
        raise PreparacaoNfseInvalida(
            "Ambiente da configuracao fiscal e invalido."
        )

    provider = _normalizar_provider(
        configuracao.provider
    )

    chave = gerar_chave_emissao_parcela(
        ordem_servico_id,
        parcela_id,
    )

    # --------------------------------------------------------
    # 1. Idempotencia pela chave nova
    # --------------------------------------------------------

    existente = NfseDocumento.query.filter_by(
        chave_idempotencia=chave,
        ativo=True,
    ).first()

    if existente is not None:
        _validar_documento_parcela_existente(
            existente,
            ordem_servico_id=ordem_servico_id,
            parcela_id=parcela_id,
            configuracao_fiscal_id=configuracao.id,
            ambiente=ambiente,
            provider=provider,
            chave_idempotencia=chave,
            valor_servicos=valor_servicos,
        )
        return existente, False

    # --------------------------------------------------------
    # 2. Protecao pela parcela
    # --------------------------------------------------------

    existente_parcela = NfseDocumento.query.filter_by(
        ordem_servico_parcela_id=parcela_id,
        ativo=True,
    ).first()

    if existente_parcela is not None:
        _validar_documento_parcela_existente(
            existente_parcela,
            ordem_servico_id=ordem_servico_id,
            parcela_id=parcela_id,
            configuracao_fiscal_id=configuracao.id,
            ambiente=ambiente,
            provider=provider,
            chave_idempotencia=chave,
            valor_servicos=valor_servicos,
        )
        return existente_parcela, False

    # --------------------------------------------------------
    # 3. Adocao segura do rascunho legado da OS
    # --------------------------------------------------------

    chave_legada = gerar_chave_emissao_original(
        ordem_servico_id
    )

    candidatos_legados = NfseDocumento.query.filter_by(
        ordem_servico_id=ordem_servico_id,
        configuracao_fiscal_id=configuracao.id,
        status="RASCUNHO",
        ambiente=ambiente,
        provider=provider,
        ordem_servico_parcela_id=None,
        ativo=True,
    ).all()

    legados_seguros = [
        documento
        for documento in candidatos_legados
        if documento.chave_idempotencia in {
            None,
            chave_legada,
        }
        and documento.numero_rps is None
        and documento.xml_envio is None
        and documento.xml_envio_sha256 is None
        and documento.preparado_em is None
    ]

    if len(legados_seguros) > 1:
        raise PreparacaoNfseInvalida(
            "Existem multiplos rascunhos legados seguros "
            "para a mesma OS."
        )

    if len(legados_seguros) == 1:
        documento = legados_seguros[0]

        documento.ordem_servico_parcela_id = parcela.id
        documento.valor_servicos = valor_servicos
        documento.chave_idempotencia = chave
        documento.mensagem_status = (
            "Rascunho legado adotado para a parcela "
            f"{parcela.numero_parcela}. "
            "Nenhum RPS foi consumido."
        )

        try:
            db.session.commit()
            return documento, False
        except Exception:
            db.session.rollback()
            raise

    # --------------------------------------------------------
    # 4. Nova intencao fiscal da parcela
    # --------------------------------------------------------

    documento = NfseDocumento(
        ordem_servico_id=ordem_servico_id,
        ordem_servico_parcela_id=parcela.id,
        configuracao_fiscal_id=configuracao.id,
        status="RASCUNHO",
        ambiente=ambiente,
        provider=provider,
        chave_idempotencia=chave,
        valor_servicos=valor_servicos,
        mensagem_status=(
            "Rascunho fiscal criado para a parcela "
            f"{parcela.numero_parcela}. "
            "Nenhum RPS foi consumido."
        ),
    )

    try:
        db.session.add(documento)
        db.session.commit()
        return documento, True

    except IntegrityError:
        db.session.rollback()

        existente = NfseDocumento.query.filter(
            or_(
                NfseDocumento.chave_idempotencia == chave,
                NfseDocumento.ordem_servico_parcela_id
                == parcela_id,
            )
        ).first()

        if existente is None:
            raise

        _validar_documento_parcela_existente(
            existente,
            ordem_servico_id=ordem_servico_id,
            parcela_id=parcela_id,
            configuracao_fiscal_id=configuracao.id,
            ambiente=ambiente,
            provider=provider,
            chave_idempotencia=chave,
            valor_servicos=valor_servicos,
        )

        return existente, False


def preparar_nfse_parcela_geisweb(
    *,
    documento_id: int,
    ordem_servico_id: int,
    parcela_id: int,
    c_class_trib: str,
    c_class_trib_reg: str,
    ibs,
    cbs,
    pis="0.00",
    cofins="0.00",
    csll="0.00",
    irrf="0.00",
    inss="0.00",
) -> tuple[NfseDocumento, dict]:
    """Prepara RPS/XML GeisWeb de uma parcela.

    D24F04-C:
    - exige documento RASCUNHO vinculado a parcela;
    - usa exatamente o valor fiscal congelado da parcela;
    - deriva TipoLancamento e Regime GeisWeb da configuracao;
    - reserva RPS de forma idempotente;
    - gera e valida XML GeisWeb;
    - persiste o artefato fiscal;
    - nao transmite;
    - nao executa HTTP/SOAP;
    - nao altera financeiro.
    """

    from app.configuracao.configuracao_model import Configuracao

    documento = db.session.get(
        NfseDocumento,
        documento_id,
    )

    if documento is None:
        raise PreparacaoNfseInvalida(
            "Documento fiscal nao encontrado."
        )

    ordem = db.session.get(
        OrdemServico,
        ordem_servico_id,
    )

    if ordem is None:
        raise PreparacaoNfseInvalida(
            "Ordem de servico nao encontrada."
        )

    parcela = OrdemServicoParcela.query.filter_by(
        id=parcela_id,
        ordem_servico_id=ordem_servico_id,
        ativo=True,
    ).first()

    if parcela is None:
        raise PreparacaoNfseInvalida(
            "Parcela nao encontrada ou nao pertence a OS."
        )

    if documento.status != "RASCUNHO":
        raise PreparacaoNfseInvalida(
            "Somente documento RASCUNHO pode ser preparado."
        )

    if documento.ordem_servico_id != ordem.id:
        raise PreparacaoNfseInvalida(
            "Documento fiscal nao pertence a OS."
        )

    if documento.ordem_servico_parcela_id != parcela.id:
        raise PreparacaoNfseInvalida(
            "Documento fiscal nao pertence a parcela."
        )

    valor_documento = Decimal(
        str(documento.valor_servicos or "0")
    ).quantize(
        Decimal("0.01")
    )

    valor_parcela = Decimal(
        str(parcela.valor or "0")
    ).quantize(
        Decimal("0.01")
    )

    if valor_documento <= Decimal("0"):
        raise PreparacaoNfseInvalida(
            "Valor fiscal do documento deve ser maior que zero."
        )

    if valor_documento != valor_parcela:
        raise PreparacaoNfseInvalida(
            "Valor fiscal diverge do valor da parcela."
        )

    configuracoes = ConfiguracaoFiscal.query.filter_by(
        ativo=True
    ).all()

    if len(configuracoes) != 1:
        raise PreparacaoNfseInvalida(
            "Deve existir exatamente uma configuracao fiscal ativa."
        )

    configuracao_fiscal = configuracoes[0]

    if (
        documento.configuracao_fiscal_id
        != configuracao_fiscal.id
    ):
        raise PreparacaoNfseInvalida(
            "Documento pertence a outra configuracao fiscal."
        )

    configuracao_institucional = db.session.get(
        Configuracao,
        configuracao_fiscal.configuracao_id,
    )

    if configuracao_institucional is None:
        raise PreparacaoNfseInvalida(
            "Configuracao institucional nao encontrada."
        )

    provider = normalizar_codigo_provider(
        configuracao_fiscal.provider
    )

    if provider != "GEISWEB_TIETE":
        raise PreparacaoNfseInvalida(
            "D24F04-C suporta somente GEISWEB_TIETE."
        )

    regime_erp = str(
        configuracao_fiscal.regime_tributario or ""
    ).strip().upper()

    if regime_erp == "SIMPLES_NACIONAL":
        tipo_lancamento = "P"
        regime_geisweb = "1"

    elif regime_erp == "MEI":
        tipo_lancamento = "P"
        regime_geisweb = "2"

    elif regime_erp in {
        "LUCRO_PRESUMIDO",
        "LUCRO_REAL",
        "OUTRO",
    }:
        tipo_lancamento = "N"
        regime_geisweb = "6"

    else:
        raise PreparacaoNfseInvalida(
            "Regime tributario nao mapeado para GeisWeb."
        )

    def codigo_seis(valor, campo):
        codigo = str(valor or "").strip()

        if (
            len(codigo) != 6
            or not codigo.isdigit()
        ):
            raise PreparacaoNfseInvalida(
                f"{campo} deve possuir exatamente 6 digitos."
            )

        return codigo

    c_class_trib = codigo_seis(
        c_class_trib,
        "cClassTrib",
    )

    c_class_trib_reg = codigo_seis(
        c_class_trib_reg,
        "cClassTribReg",
    )

    def valor_tributo(valor, campo):
        try:
            numero = Decimal(
                str(valor)
            ).quantize(
                Decimal("0.01")
            )
        except (
            InvalidOperation,
            TypeError,
            ValueError,
        ) as exc:
            raise PreparacaoNfseInvalida(
                f"{campo} possui valor invalido."
            ) from exc

        if numero < Decimal("0"):
            raise PreparacaoNfseInvalida(
                f"{campo} nao pode ser negativo."
            )

        return numero

    ibs_valor = valor_tributo(
        ibs,
        "IBS",
    )

    cbs_valor = valor_tributo(
        cbs,
        "CBS",
    )

    outros_impostos = {
        "pis": valor_tributo(pis, "PIS"),
        "cofins": valor_tributo(
            cofins,
            "COFINS",
        ),
        "csll": valor_tributo(
            csll,
            "CSLL",
        ),
        "irrf": valor_tributo(
            irrf,
            "IRRF",
        ),
        "inss": valor_tributo(
            inss,
            "INSS",
        ),
    }

    codigo_nacional = str(
        configuracao_fiscal.codigo_lc116 or ""
    ).strip()

    if not codigo_nacional:
        raise PreparacaoNfseInvalida(
            "Codigo nacional LC116 nao configurado."
        )

    # Cada documento fiscal corresponde a um lote unitario.
    numero_lote = str(documento.id)

    return preparar_documento_nfse_com_geisweb(
        documento=documento,
        ordem_servico=ordem,
        configuracao_fiscal=configuracao_fiscal,
        configuracao_institucional=(
            configuracao_institucional
        ),
        numero_lote=numero_lote,
        data_emissao=datetime.now(
            timezone.utc
        ).replace(
            microsecond=0
        ),
        tipo_lancamento=tipo_lancamento,
        regime_geisweb=regime_geisweb,
        codigo_nacional=codigo_nacional,
        base_calculo=valor_documento,
        ibs_cbs={
            "c_class_trib": c_class_trib,
            "ibs": ibs_valor,
            "cbs": cbs_valor,
            "c_class_trib_reg": c_class_trib_reg,
        },
        outros_impostos=outros_impostos,
        ncm="",
        valores={
            "valor_servicos": valor_documento,
        },
    )


def preparar_nfse_da_os(
    ordem_servico_id: int,
) -> tuple[NfseDocumento, bool]:
    """Prepara localmente a NFS-e de uma OS concluida.

    Tambem adota, de forma segura, um unico RASCUNHO legado
    da fundacao fiscal criado antes da chave de idempotencia.

    Esta funcao NAO:
    - transmite NFS-e;
    - gera ou consome RPS;
    - incrementa proximo_rps;
    - cria lancamento financeiro;
    - usa o modulo legado NotaFiscalServico.
    """

    ordem = db.session.get(
        OrdemServico,
        ordem_servico_id,
    )

    if ordem is None:
        raise PreparacaoNfseInvalida(
            f"Ordem de servico {ordem_servico_id} nao encontrada."
        )

    if ordem.status != "concluida":
        raise PreparacaoNfseInvalida(
            "A NFS-e somente pode ser preparada para OS concluida."
        )

    if ordem.situacao_fiscal != "EMITIR_NFSE":
        raise PreparacaoNfseInvalida(
            "A OS nao possui decisao fiscal EMITIR_NFSE."
        )

    configuracoes = ConfiguracaoFiscal.query.filter_by(
        ativo=True
    ).all()

    if len(configuracoes) != 1:
        raise PreparacaoNfseInvalida(
            "Deve existir exatamente uma configuracao fiscal ativa."
        )

    configuracao = configuracoes[0]

    ambiente = (
        configuracao.ambiente or "HOMOLOGACAO"
    ).strip().upper()

    if ambiente not in AMBIENTES_NFSE:
        raise PreparacaoNfseInvalida(
            "Ambiente da configuracao fiscal e invalido."
        )

    provider = _normalizar_provider(
        configuracao.provider
    )

    chave = gerar_chave_emissao_original(
        ordem_servico_id
    )

    # 1. Caminho normal: intencao ja possui chave idempotente.
    existente = NfseDocumento.query.filter_by(
        chave_idempotencia=chave
    ).first()

    if existente is not None:
        _validar_documento_existente(
            existente,
            ordem_servico_id=ordem_servico_id,
            configuracao_fiscal_id=configuracao.id,
            ambiente=ambiente,
            provider=provider,
        )
        return existente, False

    # 2. Compatibilidade com rascunhos criados antes do C7.
    rascunhos_sem_chave = NfseDocumento.query.filter_by(
        ordem_servico_id=ordem_servico_id,
        configuracao_fiscal_id=configuracao.id,
        status="RASCUNHO",
        ambiente=ambiente,
        provider=provider,
        chave_idempotencia=None,
        ativo=True,
    ).all()

    if len(rascunhos_sem_chave) > 1:
        raise PreparacaoNfseInvalida(
            "Existem multiplos rascunhos sem chave de idempotencia "
            "para a mesma intencao fiscal."
        )

    if len(rascunhos_sem_chave) == 1:
        documento = rascunhos_sem_chave[0]

        documento.chave_idempotencia = chave
        documento.mensagem_status = (
            "Rascunho preexistente adotado pela camada "
            "idempotente da fundacao fiscal."
        )

        try:
            db.session.commit()
            return documento, False

        except Exception:
            db.session.rollback()
            raise

    # 3. Nenhum documento anterior: cria de forma idempotente.
    try:
        documento, criado = obter_ou_criar_rascunho(
            ordem_servico_id=ordem_servico_id,
            configuracao_fiscal_id=configuracao.id,
            chave_idempotencia=chave,
            ambiente=ambiente,
            provider=provider,
        )

        db.session.commit()

        return documento, criado

    except Exception:
        db.session.rollback()
        raise
