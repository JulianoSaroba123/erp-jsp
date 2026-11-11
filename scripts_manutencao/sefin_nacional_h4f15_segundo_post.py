"""H4-F15 - segundo POST /nfse controlado na Produção Restrita.

Usa exclusivamente a DPS corrigida do H4-F14.
Executa no máximo UMA chamada POST /nfse, sem retry automático.
Não usa Flask nem banco.

Proteções:
- confirmação explícita própria do H4-F15;
- pré-gate estrutural do XML assinado;
- marcador local criado ANTES da rede;
- marcador distinto do H4-F12;
- timeout/falha de comunicação vira resultado ambíguo e bloqueia retransmissão.
"""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys
import tempfile

import requests


PASTA = Path(__file__).resolve().parent
SCRIPT_H4F12 = (
    PASTA
    / "sefin_nacional_h4f12_primeiro_post.py"
)
SCRIPT_H4F14 = (
    PASTA
    / "sefin_nacional_h4f14_dry_run_corrigido.py"
)

CONFIRMACAO_EXIGIDA = "POST_UNICO_PRODREST_H4F15"
ENV_AUTORIZACAO = "NFSE_H4F15_AUTORIZACAO"
ENDPOINT_ESPERADO = (
    "https://sefin.producaorestrita.nfse.gov.br"
    "/API/SefinNacional/nfse"
)
TIMEOUT = (
    10,
    30,
)


class SegundoPostSefinInvalido(RuntimeError):
    """Falha controlada no segundo POST da Produção Restrita."""


def _carregar_modulo(
    nome: str,
    caminho: Path,
):
    spec = importlib.util.spec_from_file_location(
        nome,
        caminho,
    )

    if spec is None or spec.loader is None:
        raise SegundoPostSefinInvalido(
            f"Nao foi possivel carregar modulo local: {nome}."
        )

    modulo = importlib.util.module_from_spec(
        spec
    )
    sys.modules[
        nome
    ] = modulo
    spec.loader.exec_module(
        modulo
    )
    return modulo


h4f12 = _carregar_modulo(
    "h4f12_base_h4f15",
    SCRIPT_H4F12,
)
h4f14 = _carregar_modulo(
    "h4f14_dry_run_h4f15",
    SCRIPT_H4F14,
)


class ResultadoSegundoPost:
    def __init__(
        self,
        *,
        status_code,
        classificacao,
        resposta_normalizada,
        resposta_bytes,
        id_dps,
        corpo_sha256,
        resposta_sha256,
        caminho_marcador,
    ):
        self.status_code = int(
            status_code
        )
        self.classificacao = str(
            classificacao
        )
        self.resposta_normalizada = (
            resposta_normalizada
        )
        self.resposta_bytes = bytes(
            resposta_bytes
        )
        self.id_dps = str(
            id_dps
        )
        self.corpo_sha256 = str(
            corpo_sha256
        )
        self.resposta_sha256 = str(
            resposta_sha256
        )
        self.caminho_marcador = Path(
            caminho_marcador
        )
        self.rede_utilizada = True
        self.post_nfse_executado = True
        self.retry_automatico = False
        self.banco_acessado = False
        self.flask_inicializado = False


def _sha256(
    dados: bytes,
) -> str:
    return hashlib.sha256(
        bytes(
            dados
        )
    ).hexdigest().upper()


def _mascarar(
    valor: str,
    inicio=10,
    fim=8,
) -> str:
    texto = str(
        valor or ""
    ).strip()

    if len(texto) <= inicio + fim:
        return texto

    return (
        texto[:inicio]
        + "..."
        + texto[-fim:]
    )


def _validar_xml_corrigido(
    xml_assinado: bytes,
) -> None:
    try:
        xml = bytes(
            xml_assinado
        ).decode(
            "utf-8"
        )
    except UnicodeDecodeError as exc:
        raise SegundoPostSefinInvalido(
            "XML assinado do H4-F14 nao esta em UTF-8 valido."
        ) from exc

    obrigatorios = (
        "<nDPS>"
        + h4f14.NUMERO_DPS_H4F14
        + "</nDPS>",
        "<pTotTribSN>"
        + h4f14.PTOTTRIBSN_CONFIRMADO
        + "</pTotTribSN>",
        "<cTribNac>140101</cTribNac>",
        "<cNBS>101061900</cNBS>",
        "<cLocPrestacao>3541653</cLocPrestacao>",
        "<opSimpNac>3</opSimpNac>",
        "<regApTribSN>1</regApTribSN>",
        "<regEspTrib>0</regEspTrib>",
        "<tpRetISSQN>1</tpRetISSQN>",
        "<tribISSQN>1</tribISSQN>",
    )

    ausentes = (
        "<indTotTrib>",
        "<pAliq>",
        "<IM>",
        "<xNome>",
    )

    faltantes = [
        item
        for item in obrigatorios
        if item not in xml
    ]

    proibidos = [
        item
        for item in ausentes
        if item in xml
    ]

    if faltantes:
        raise SegundoPostSefinInvalido(
            "Pre-gate H4-F15 falhou. Campos obrigatorios ausentes: "
            + ", ".join(
                faltantes
            )
        )

    if proibidos:
        raise SegundoPostSefinInvalido(
            "Pre-gate H4-F15 falhou. Campos proibidos presentes: "
            + ", ".join(
                proibidos
            )
        )

    numero_antigo = (
        "<nDPS>"
        + h4f14.h4f11.NUMERO_DPS_DRY_RUN
        + "</nDPS>"
    )

    if numero_antigo in xml:
        raise SegundoPostSefinInvalido(
            "Pre-gate H4-F15 detectou o numero DPS do primeiro POST."
        )


def _caminho_marcador_padrao(
    id_dps: str,
) -> Path:
    identificador = hashlib.sha256(
        str(
            id_dps
        ).encode(
            "utf-8"
        )
    ).hexdigest()[:16]

    return (
        Path(
            tempfile.gettempdir()
        )
        / (
            "erp_jsp_h4f15_post_unico_"
            + identificador
            + ".json"
        )
    )


def _escrever_json_atomico(
    caminho: Path,
    dados: dict,
) -> None:
    caminho.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    temporario = caminho.with_suffix(
        caminho.suffix + ".tmp"
    )

    temporario.write_text(
        json.dumps(
            dados,
            ensure_ascii=False,
            sort_keys=True,
            indent=2,
        ),
        encoding="utf-8",
    )

    temporario.replace(
        caminho
    )


def _criar_marcador_pre_rede(
    *,
    caminho: Path,
    id_dps: str,
    corpo_sha256: str,
) -> None:
    if caminho.exists():
        raise SegundoPostSefinInvalido(
            "Marcador H4-F15 ja existe. "
            "Novo POST foi bloqueado para evitar duplicidade."
        )

    _escrever_json_atomico(
        caminho,
        {
            "fase": "PRE_REDE",
            "etapa": "H4-F15",
            "ambiente": "PRODUCAO_RESTRITA",
            "metodo": "POST",
            "rota": "/nfse",
            "id_dps_mascarado": _mascarar(
                id_dps
            ),
            "numero_dps": h4f14.NUMERO_DPS_H4F14,
            "ptottribsn": h4f14.PTOTTRIBSN_CONFIRMADO,
            "corpo_sha256": corpo_sha256,
            "criado_em_utc": (
                datetime.now(
                    timezone.utc
                )
                .replace(
                    microsecond=0
                )
                .isoformat()
            ),
            "retry_automatico": False,
        },
    )


def _atualizar_marcador(
    *,
    caminho: Path,
    fase: str,
    status_code=None,
    resposta_sha256=None,
    classificacao=None,
    detalhe=None,
    resposta_erro=None,
    chave_acesso_mascarada=None,
) -> None:
    try:
        dados = json.loads(
            caminho.read_text(
                encoding="utf-8"
            )
        )
    except (
        OSError,
        ValueError,
        TypeError,
    ):
        dados = {}

    dados.update(
        {
            "fase": fase,
            "status_code": status_code,
            "resposta_sha256": resposta_sha256,
            "classificacao": classificacao,
            "detalhe": detalhe,
            "resposta_erro": resposta_erro,
            "chave_acesso_mascarada": chave_acesso_mascarada,
            "atualizado_em_utc": (
                datetime.now(
                    timezone.utc
                )
                .replace(
                    microsecond=0
                )
                .isoformat()
            ),
            "retry_automatico": False,
        }
    )

    _escrever_json_atomico(
        caminho,
        dados,
    )


def executar_post_unico(
    *,
    confirmacao: str,
    session=None,
    caminho_marcador: Path | None = None,
    agora=None,
    material_a1=None,
) -> ResultadoSegundoPost:
    """Executa no máximo uma chamada real POST /nfse."""

    if str(
        confirmacao or ""
    ).strip() != CONFIRMACAO_EXIGIDA:
        raise SegundoPostSefinInvalido(
            "Confirmacao explicita do H4-F15 ausente ou invalida."
        )

    dry_run = h4f14.executar_dry_run_corrigido(
        agora=agora,
        material_a1=material_a1,
    )

    _validar_xml_corrigido(
        dry_run.xml_assinado
    )

    endpoint = (
        h4f14.h4f11.h4f9._validar_endpoint()
    )

    if endpoint != ENDPOINT_ESPERADO:
        raise SegundoPostSefinInvalido(
            "Endpoint diverge da Producao Restrita oficial."
        )

    corpo = dry_run.corpo_json
    corpo_sha256 = _sha256(
        corpo
    )

    marcador = (
        Path(
            caminho_marcador
        )
        if caminho_marcador is not None
        else _caminho_marcador_padrao(
            dry_run.id_dps
        )
    )

    _criar_marcador_pre_rede(
        caminho=marcador,
        id_dps=dry_run.id_dps,
        corpo_sha256=corpo_sha256,
    )

    cliente = (
        session
        if session is not None
        else requests.Session()
    )

    (
        chave_privada,
        certificado,
        cadeia,
        _,
    ) = (
        h4f14.h4f11.h4f9._carregar_material_a1()
        if material_a1 is None
        else (
            material_a1.chave_privada,
            material_a1.certificado,
            tuple(
                getattr(
                    material_a1,
                    "cadeia",
                    (),
                )
                or ()
            ),
            "MATERIAL_INJETADO",
        )
    )

    try:
        with h4f14.h4f11.h4f9._materializar_mtls(
            chave_privada,
            certificado,
            cadeia,
        ) as caminhos:
            resposta = cliente.request(
                method="POST",
                url=endpoint,
                headers={
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                },
                data=corpo,
                timeout=TIMEOUT,
                verify=True,
                allow_redirects=False,
                cert=caminhos,
            )
    except (
        requests.exceptions.Timeout,
        requests.exceptions.ConnectionError,
        requests.exceptions.RequestException,
    ) as exc:
        _atualizar_marcador(
            caminho=marcador,
            fase="RESULTADO_AMBIGUO",
            classificacao="FALHA_COMUNICACAO_SEM_RETRY",
            detalhe=type(
                exc
            ).__name__,
        )

        raise SegundoPostSefinInvalido(
            "Falha de comunicacao apos armar H4-F15. "
            "NAO retransmitir. Consultar a DPS antes de qualquer acao."
        ) from exc

    try:
        status_code = int(
            resposta.status_code
        )
    except (
        TypeError,
        ValueError,
    ) as exc:
        _atualizar_marcador(
            caminho=marcador,
            fase="RESULTADO_AMBIGUO",
            classificacao="STATUS_HTTP_INVALIDO_SEM_RETRY",
        )

        raise SegundoPostSefinInvalido(
            "Resposta HTTP sem status valido. NAO retransmitir."
        ) from exc

    conteudo = bytes(
        getattr(
            resposta,
            "content",
            b"",
        )
        or b""
    )

    resposta_sha256 = _sha256(
        conteudo
    )

    classificacao = h4f12._classificar_status(
        status_code
    )

    normalizada = h4f12._normalizar_quando_suportado(
        status_code=status_code,
        conteudo=conteudo,
    )

    resposta_erro = h4f12._extrair_resposta_erro_segura(
        status_code=status_code,
        conteudo=conteudo,
    )

    chave_mascarada = None

    if (
        normalizada is not None
        and normalizada.sucesso
        and normalizada.chave_acesso
    ):
        chave_mascarada = _mascarar(
            normalizada.chave_acesso,
            inicio=8,
            fim=8,
        )

    _atualizar_marcador(
        caminho=marcador,
        fase="RESPOSTA_RECEBIDA",
        status_code=status_code,
        resposta_sha256=resposta_sha256,
        classificacao=classificacao,
        resposta_erro=resposta_erro,
        chave_acesso_mascarada=chave_mascarada,
    )

    return ResultadoSegundoPost(
        status_code=status_code,
        classificacao=classificacao,
        resposta_normalizada=normalizada,
        resposta_bytes=conteudo,
        id_dps=dry_run.id_dps,
        corpo_sha256=corpo_sha256,
        resposta_sha256=resposta_sha256,
        caminho_marcador=marcador,
    )


def executar() -> int:
    confirmacao = os.environ.get(
        ENV_AUTORIZACAO,
        "",
    )

    resultado = executar_post_unico(
        confirmacao=confirmacao,
    )

    print(
        "=== H4-F15 | SEGUNDO POST SEFIN PRODREST ==="
    )
    print(
        "STATUS OPERACIONAL: RESPOSTA_RECEBIDA"
    )
    print(
        "OPERACAO: POST /nfse"
    )
    print(
        "AMBIENTE: PRODUCAO_RESTRITA"
    )
    print(
        "NUMERO DPS: "
        + h4f14.NUMERO_DPS_H4F14
    )
    print(
        "PTOTTRIBSN: "
        + h4f14.PTOTTRIBSN_CONFIRMADO
    )
    print(
        "HTTP STATUS: "
        + str(
            resultado.status_code
        )
    )
    print(
        "CLASSIFICACAO: "
        + resultado.classificacao
    )
    print(
        "DPS ID: "
        + _mascarar(
            resultado.id_dps
        )
    )
    print(
        "CORPO SHA256: "
        + resultado.corpo_sha256
    )
    print(
        "RESPOSTA SHA256: "
        + resultado.resposta_sha256
    )

    normalizada = resultado.resposta_normalizada

    if normalizada is not None:
        print(
            "RESPOSTA NORMALIZADA: True"
        )
        print(
            "TIPO AMBIENTE RETORNO: "
            + str(
                normalizada.tipo_ambiente
            )
        )
        print(
            "VERSAO APLICATIVO SEFIN: "
            + str(
                normalizada.versao_aplicativo
            )
        )

        if normalizada.sucesso:
            print(
                "NFSE GERADA: True"
            )
            print(
                "CHAVE ACESSO: "
                + _mascarar(
                    normalizada.chave_acesso,
                    inicio=8,
                    fim=8,
                )
            )
            print(
                "NFSE XML SHA256: "
                + _sha256(
                    normalizada.nfse_xml
                )
            )
            h4f12._imprimir_mensagens(
                "ALERTAS",
                normalizada.alertas,
            )
        else:
            print(
                "NFSE GERADA: False"
            )
            h4f12._imprimir_mensagens(
                "ERROS",
                normalizada.erros,
            )
    else:
        print(
            "RESPOSTA NORMALIZADA: False"
        )
        print(
            "RESPOSTA BYTES: "
            + str(
                len(
                    resultado.resposta_bytes
                )
            )
        )

    print(
        "REDE UTILIZADA: True"
    )
    print(
        "POST /nfse EXECUTADO: True"
    )
    print(
        "RETRY AUTOMATICO: False"
    )
    print(
        "FLASK INICIALIZADO: False"
    )
    print(
        "BANCO ACESSADO: False"
    )
    print(
        "MARCADOR LOCAL: "
        + str(
            resultado.caminho_marcador
        )
    )

    return (
        0
        if resultado.status_code == 201
        else 2
    )


def main() -> int:
    try:
        return executar()
    except (
        SegundoPostSefinInvalido,
        h4f14.DryRunH4F14Invalido,
        h4f14.h4f11.DryRunDpsInvalido,
        h4f14.h4f11.h4f9.PreflightStandaloneInvalido,
        h4f14.h4f11.dps_model.DpsCanonicaInvalida,
        h4f14.h4f11.serializer.SerializacaoDpsInvalida,
        h4f14.h4f11.signer.AssinaturaXmlDpsInvalida,
        h4f14.h4f11.validator.ValidacaoXsdDpsInvalida,
    ) as exc:
        print(
            "=== H4-F15 | SEGUNDO POST SEFIN PRODREST ==="
        )
        print(
            "STATUS OPERACIONAL: FALHA"
        )
        print(
            "MOTIVO: "
            + str(
                exc
            )
        )
        print(
            "RETRY AUTOMATICO: False"
        )
        print(
            "FLASK INICIALIZADO: False"
        )
        print(
            "BANCO ACESSADO: False"
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(
        main()
    )
