"""Servicos da nova fundacao NFS-e.

Nenhuma funcao deste modulo transmite NFS-e.
Nenhuma funcao deste modulo gera lancamento financeiro.
"""

from sqlalchemy.exc import IntegrityError

from app.extensoes import db
from app.fiscal.configuracao_fiscal_model import ConfiguracaoFiscal
from app.fiscal.nfse_documento_model import (
    AMBIENTES_NFSE,
    NfseDocumento,
)
from app.ordem_servico.ordem_servico_model import OrdemServico
from app.fiscal.providers.registry import normalizar_codigo_provider
from app.fiscal.providers.resolver import resolver_provider_nfse
from app.fiscal.dps_erp_adapter import montar_dps_canonica_da_os
from app.fiscal.xml.dps_serializer import montar_xml_dps_serializado
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
    """Chave deterministica para a primeira intencao NFS-e de uma OS."""
    return f"nfse:os:{ordem_servico_id}:emissao:original"


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
) -> dict:
    """Integra ERP -> DPS -> XML -> XSD ao payload tecnico NFS-e.

    D24F02-B7-A3:
    - preserva a preparacao tecnica existente do provider;
    - nao transmite;
    - nao assina digitalmente;
    - nao acessa certificado;
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

    payload["conteudo"] = xml_dps

    return payload


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

    # Todas as validacoes ocorrem antes de qualquer mutacao.
    documento.status = novo_status
    documento.mensagem_status = resultado_normalizado["mensagem"]

    protocolo = resultado_normalizado["protocolo"]

    if protocolo is not None:
        documento.protocolo = protocolo

    if novo_status == "AUTORIZADA":
        documento.numero_nfse = numero_nfse

    return documento


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
