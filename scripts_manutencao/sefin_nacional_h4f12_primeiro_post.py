"""H4-F12 - primeiro POST /nfse na SEFIN Produção Restrita.

Executa, mediante confirmação explícita, UMA única transmissão real.
Não usa Flask nem banco. Não possui retry automático.

Proteção contra duplicidade:
- cria marcador local ANTES da chamada de rede;
- se o marcador já existir, bloqueia novo POST;
- em timeout/falha de comunicação, considera resultado ambíguo e não repete.
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


RAIZ = Path(__file__).resolve().parents[1]
SCRIPT_H4F11 = (
    Path(__file__).resolve().parent
    / "sefin_nacional_h4f11_dry_run_dps.py"
)
ARQUIVO_RESPOSTA = (
    RAIZ
    / "app"
    / "fiscal"
    / "providers"
    / "sefin_nacional_resposta.py"
)

CONFIRMACAO_EXIGIDA = "POST_UNICO_PRODREST"
ENDPOINT_ESPERADO = (
    "https://sefin.producaorestrita.nfse.gov.br"
    "/API/SefinNacional/nfse"
)
TIMEOUT = (
    10,
    30,
)


class PrimeiroPostSefinInvalido(RuntimeError):
    """Falha controlada no primeiro POST da Produção Restrita."""


class ResultadoPrimeiroPost:
    def __init__(
        self,
        *,
        status_code,
        sucesso_http,
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
        self.sucesso_http = bool(
            sucesso_http
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


def _carregar_modulo(
    nome: str,
    caminho: Path,
):
    spec = importlib.util.spec_from_file_location(
        nome,
        caminho,
    )

    if spec is None or spec.loader is None:
        raise PrimeiroPostSefinInvalido(
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


h4f11 = _carregar_modulo(
    "h4f11_dry_run_h4f12",
    SCRIPT_H4F11,
)
resposta_model = _carregar_modulo(
    "sefin_resposta_h4f12",
    ARQUIVO_RESPOSTA,
)


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
    *,
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


def _caminho_marcador_padrao(
    id_dps: str,
) -> Path:
    identificador = hashlib.sha256(
        id_dps.encode(
            "utf-8"
        )
    ).hexdigest()[:16]

    return (
        Path(
            tempfile.gettempdir()
        )
        / (
            "erp_jsp_h4f12_post_unico_"
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
        raise PrimeiroPostSefinInvalido(
            "Marcador H4-F12 ja existe. "
            "Novo POST foi bloqueado para evitar duplicidade."
        )

    _escrever_json_atomico(
        caminho,
        {
            "fase": "PRE_REDE",
            "ambiente": "PRODUCAO_RESTRITA",
            "metodo": "POST",
            "rota": "/nfse",
            "id_dps_mascarado": _mascarar(
                id_dps
            ),
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


def _classificar_status(
    status_code: int,
) -> str:
    if status_code == 201:
        return "NFSE_GERADA"

    if status_code == 400:
        return "REJEICAO_NEGOCIO"

    if status_code in {
        401,
        403,
    }:
        return "AUTENTICACAO_REJEITADA"

    if status_code in {
        408,
        425,
        429,
    } or 500 <= status_code <= 599:
        return "SERVICO_INDISPONIVEL_OU_TRANSITORIO"

    if 200 <= status_code <= 299:
        return "SUCESSO_HTTP_FORA_DO_CONTRATO"

    return "STATUS_HTTP_INESPERADO"


def _extrair_resposta_erro_segura(
    *,
    status_code: int,
    conteudo: bytes,
):
    if status_code < 400 or status_code > 599:
        return None

    try:
        dados = json.loads(
            bytes(
                conteudo
            ).decode(
                "utf-8"
            )
        )
    except (
        UnicodeDecodeError,
        json.JSONDecodeError,
        TypeError,
        ValueError,
    ):
        return None

    if not isinstance(
        dados,
        dict,
    ):
        return None

    permitidos = {
        "tipoAmbiente",
        "versaoAplicativo",
        "dataHoraProcessamento",
        "idDPS",
        "idDps",
        "erros",
    }

    return {
        chave: valor
        for chave, valor in dados.items()
        if chave in permitidos
    }


def _normalizar_quando_suportado(
    *,
    status_code: int,
    conteudo: bytes,
):
    if status_code not in {
        201,
        400,
        403,
        500,
    }:
        return None

    try:
        return (
            resposta_model.normalizar_resposta_emissao_sefin(
                status_code=status_code,
                conteudo=conteudo,
            )
        )
    except resposta_model.RespostaEmissaoSefinInvalida:
        return None


def executar_post_unico(
    *,
    confirmacao: str,
    session=None,
    caminho_marcador: Path | None = None,
    agora=None,
    material_a1=None,
    percentual_tot_trib_sn: str | None = None,
) -> ResultadoPrimeiroPost:
    """Executa exatamente uma chamada POST /nfse sem retry."""

    if str(
        confirmacao or ""
    ).strip() != CONFIRMACAO_EXIGIDA:
        raise PrimeiroPostSefinInvalido(
            "Confirmacao explicita do H4-F12 ausente ou invalida."
        )

    dry_run = h4f11.executar_dry_run(
        agora=agora,
        material_a1=material_a1,
        percentual_tot_trib_sn=percentual_tot_trib_sn,
    )

    endpoint = (
        h4f11.h4f9._validar_endpoint()
    )

    if endpoint != ENDPOINT_ESPERADO:
        raise PrimeiroPostSefinInvalido(
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
        h4f11.h4f9._carregar_material_a1()
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
        with h4f11.h4f9._materializar_mtls(
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
        requests.Timeout,
        requests.ConnectionError,
        requests.RequestException,
    ) as exc:
        _atualizar_marcador(
            caminho=marcador,
            fase="RESULTADO_AMBIGUO",
            classificacao=(
                "FALHA_COMUNICACAO_SEM_RETRY"
            ),
            detalhe=type(
                exc
            ).__name__,
        )

        raise PrimeiroPostSefinInvalido(
            "Falha de comunicacao apos armar a tentativa unica. "
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
            classificacao=(
                "STATUS_HTTP_INVALIDO_SEM_RETRY"
            ),
        )

        raise PrimeiroPostSefinInvalido(
            "Resposta HTTP sem status valido. "
            "NAO retransmitir."
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

    classificacao = _classificar_status(
        status_code
    )

    normalizada = _normalizar_quando_suportado(
        status_code=status_code,
        conteudo=conteudo,
    )

    resposta_erro = _extrair_resposta_erro_segura(
        status_code=status_code,
        conteudo=conteudo,
    )

    _atualizar_marcador(
        caminho=marcador,
        fase="RESPOSTA_RECEBIDA",
        status_code=status_code,
        resposta_sha256=resposta_sha256,
        classificacao=classificacao,
        resposta_erro=resposta_erro,
    )

    return ResultadoPrimeiroPost(
        status_code=status_code,
        sucesso_http=(
            status_code == 201
        ),
        classificacao=classificacao,
        resposta_normalizada=normalizada,
        resposta_bytes=conteudo,
        id_dps=dry_run.id_dps,
        corpo_sha256=corpo_sha256,
        resposta_sha256=resposta_sha256,
        caminho_marcador=marcador,
    )


def _imprimir_mensagens(
    titulo: str,
    mensagens,
) -> None:
    itens = tuple(
        mensagens or ()
    )

    print(
        f"{titulo}: {len(itens)}"
    )

    for indice, item in enumerate(
        itens,
        start=1,
    ):
        codigo = str(
            getattr(
                item,
                "codigo",
                None,
            )
            or ""
        ).strip()

        descricao = str(
            getattr(
                item,
                "descricao",
                None,
            )
            or getattr(
                item,
                "mensagem",
                None,
            )
            or ""
        ).strip()

        complemento = str(
            getattr(
                item,
                "complemento",
                None,
            )
            or ""
        ).strip()

        texto = (
            f"  {indice}. "
            + (
                f"[{codigo}] "
                if codigo
                else ""
            )
            + (
                descricao
                if descricao
                else "<sem descricao>"
            )
        )

        if complemento:
            texto += (
                " | "
                + complemento
            )

        print(
            texto
        )


def executar() -> int:
    confirmacao = os.environ.get(
        "NFSE_H4F12_AUTORIZACAO",
        "",
    )

    resultado = executar_post_unico(
        confirmacao=confirmacao,
    )

    print(
        "=== H4-F12 | PRIMEIRO POST SEFIN PRODREST ==="
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

    normalizada = (
        resultado.resposta_normalizada
    )

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
            _imprimir_mensagens(
                "ALERTAS",
                normalizada.alertas,
            )
        else:
            print(
                "NFSE GERADA: False"
            )
            _imprimir_mensagens(
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
        PrimeiroPostSefinInvalido,
        h4f11.DryRunDpsInvalido,
        h4f11.h4f9.PreflightStandaloneInvalido,
        h4f11.dps_model.DpsCanonicaInvalida,
        h4f11.serializer.SerializacaoDpsInvalida,
        h4f11.signer.AssinaturaXmlDpsInvalida,
        h4f11.validator.ValidacaoXsdDpsInvalida,
    ) as exc:
        print(
            "=== H4-F12 | PRIMEIRO POST SEFIN PRODREST ==="
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
