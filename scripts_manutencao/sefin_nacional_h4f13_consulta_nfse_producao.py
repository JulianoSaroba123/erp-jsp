"""H4-F13 - consulta somente leitura de NFS-e existente em Produção.

Executa UMA chamada GET /nfse/{chaveAcesso} na SEFIN Nacional de Produção.
Não emite, não cancela, não registra evento, não usa Flask e não acessa banco.
A resposta é analisada somente em memória para inspecionar campos tributários.
"""

from __future__ import annotations

import base64
import gzip
import importlib.util
import json
import os
from pathlib import Path
import sys

from lxml import etree
import requests


RAIZ = Path(__file__).resolve().parents[1]
SCRIPT_H4F9 = (
    Path(__file__).resolve().parent
    / "sefin_nacional_h4f9_preflight_real.py"
)

BASE_PRODUCAO = (
    "https://sefin.nfse.gov.br/SefinNacional"
)
ENV_CHAVE = "NFSE_H4F13_CHAVE_ACESSO"
TIMEOUT = (
    10,
    30,
)


class ConsultaNfseProducaoInvalida(RuntimeError):
    """Falha controlada na consulta read-only da NFS-e de Produção."""


def _carregar_h4f9():
    nome = "h4f9_preflight_real_h4f13"
    spec = importlib.util.spec_from_file_location(
        nome,
        SCRIPT_H4F9,
    )

    if spec is None or spec.loader is None:
        raise ConsultaNfseProducaoInvalida(
            "Nao foi possivel carregar utilitarios A1 do H4-F9."
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


h4f9 = _carregar_h4f9()


def _chave_acesso(
    valor=None,
) -> str:
    chave = str(
        valor
        if valor is not None
        else os.environ.get(
            ENV_CHAVE,
            "",
        )
    ).strip()

    if (
        len(chave) != 50
        or not chave.isdigit()
    ):
        raise ConsultaNfseProducaoInvalida(
            "Chave de acesso da NFS-e deve possuir 50 digitos."
        )

    return chave


def _mascarar(
    valor: str,
    inicio=8,
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


def _extrair_xml(
    *,
    conteudo: bytes,
    content_type: str | None,
) -> bytes:
    bruto = bytes(
        conteudo or b""
    )

    if not bruto:
        raise ConsultaNfseProducaoInvalida(
            "Consulta retornou corpo vazio."
        )

    inicio = bruto.lstrip()[:1]

    if inicio == b"<":
        return bruto

    try:
        dados = json.loads(
            bruto.decode(
                "utf-8"
            )
        )
    except (
        UnicodeDecodeError,
        json.JSONDecodeError,
    ) as exc:
        raise ConsultaNfseProducaoInvalida(
            "Resposta nao e XML nem JSON reconhecivel."
        ) from exc

    if not isinstance(
        dados,
        dict,
    ):
        raise ConsultaNfseProducaoInvalida(
            "Resposta JSON da consulta deve ser objeto."
        )

    candidatos = (
        "nfseXmlGZipB64",
        "NFSeXmlGZipB64",
        "xmlGZipB64",
        "XmlGZipB64",
    )

    valor = None

    for chave in candidatos:
        if chave in dados:
            valor = dados.get(
                chave
            )
            break

    if not isinstance(
        valor,
        str,
    ) or not valor.strip():
        raise ConsultaNfseProducaoInvalida(
            "Resposta JSON nao contem XML NFS-e compactado reconhecido. "
            "Chaves recebidas: "
            + ", ".join(
                sorted(
                    str(
                        item
                    )
                    for item in dados.keys()
                )
            )
        )

    try:
        compactado = base64.b64decode(
            valor,
            validate=True,
        )
        xml = gzip.decompress(
            compactado
        )
    except (
        ValueError,
        OSError,
    ) as exc:
        raise ConsultaNfseProducaoInvalida(
            "Falha ao recuperar XML NFS-e do envelope GZip/Base64."
        ) from exc

    return xml


def _texto_primeiro(
    raiz,
    nome_local: str,
):
    resultado = raiz.xpath(
        "//*[local-name()=$nome][1]/text()",
        nome=nome_local,
    )

    if not resultado:
        return None

    valor = str(
        resultado[
            0
        ]
    ).strip()

    return valor or None


def _inspecionar_xml(
    xml: bytes,
) -> dict:
    parser = etree.XMLParser(
        resolve_entities=False,
        no_network=True,
        load_dtd=False,
        recover=False,
    )

    try:
        raiz = etree.fromstring(
            bytes(
                xml
            ),
            parser=parser,
        )
    except etree.XMLSyntaxError as exc:
        raise ConsultaNfseProducaoInvalida(
            "XML retornado pela SEFIN e invalido."
        ) from exc

    campos = (
        "pTotTribSN",
        "indTotTrib",
        "pAliq",
        "IM",
        "xNome",
        "cTribNac",
        "cNBS",
        "cLocPrestacao",
        "opSimpNac",
        "regApTribSN",
        "regEspTrib",
        "tpRetISSQN",
        "tribISSQN",
        "vServ",
    )

    return {
        campo: _texto_primeiro(
            raiz,
            campo,
        )
        for campo in campos
    }


def consultar_nfse(
    *,
    chave_acesso=None,
    session=None,
    material_a1=None,
):
    """Executa uma única consulta GET, sem retry e sem qualquer mutação."""

    chave = _chave_acesso(
        chave_acesso
    )

    url = (
        BASE_PRODUCAO
        + "/nfse/"
        + chave
    )

    if material_a1 is None:
        (
            chave_privada,
            certificado,
            cadeia,
            _,
        ) = h4f9._carregar_material_a1()
    else:
        chave_privada = (
            material_a1.chave_privada
        )
        certificado = (
            material_a1.certificado
        )
        cadeia = tuple(
            getattr(
                material_a1,
                "cadeia",
                (),
            )
            or ()
        )

    cliente = (
        session
        if session is not None
        else requests.Session()
    )

    try:
        with h4f9._materializar_mtls(
            chave_privada,
            certificado,
            cadeia,
        ) as caminhos:
            resposta = cliente.request(
                method="GET",
                url=url,
                headers={
                    "Accept": "application/json, application/xml, text/xml",
                },
                timeout=TIMEOUT,
                verify=True,
                allow_redirects=False,
                cert=caminhos,
            )
    except requests.SSLError as exc:
        raise ConsultaNfseProducaoInvalida(
            "Falha TLS/mTLS na consulta de Produção."
        ) from exc
    except requests.Timeout as exc:
        raise ConsultaNfseProducaoInvalida(
            "Timeout na consulta de Produção."
        ) from exc
    except requests.RequestException as exc:
        raise ConsultaNfseProducaoInvalida(
            "Falha HTTP na consulta de Produção."
        ) from exc

    try:
        status_code = int(
            resposta.status_code
        )
    except (
        TypeError,
        ValueError,
    ) as exc:
        raise ConsultaNfseProducaoInvalida(
            "Status HTTP invalido na consulta."
        ) from exc

    conteudo = bytes(
        getattr(
            resposta,
            "content",
            b"",
        )
        or b""
    )

    if status_code != 200:
        raise ConsultaNfseProducaoInvalida(
            "Consulta retornou HTTP "
            + str(
                status_code
            )
            + ". Nenhuma nova tentativa automatica foi realizada."
        )

    headers = getattr(
        resposta,
        "headers",
        {},
    ) or {}

    xml = _extrair_xml(
        conteudo=conteudo,
        content_type=headers.get(
            "Content-Type"
        ),
    )

    campos = _inspecionar_xml(
        xml
    )

    return {
        "status_code": status_code,
        "chave_mascarada": _mascarar(
            chave
        ),
        "campos": campos,
        "xml_bytes": len(
            xml
        ),
        "rede_utilizada": True,
        "metodo": "GET",
        "post_executado": False,
        "evento_executado": False,
        "banco_acessado": False,
        "flask_inicializado": False,
    }


def executar() -> int:
    resultado = consultar_nfse()

    print(
        "=== H4-F13 | CONSULTA READ-ONLY NFSE PRODUCAO ==="
    )
    print(
        "STATUS: OK"
    )
    print(
        "OPERACAO: GET /nfse/{chaveAcesso}"
    )
    print(
        "AMBIENTE: PRODUCAO"
    )
    print(
        "HTTP STATUS: "
        + str(
            resultado[
                "status_code"
            ]
        )
    )
    print(
        "CHAVE: "
        + resultado[
            "chave_mascarada"
        ]
    )
    print(
        "XML BYTES: "
        + str(
            resultado[
                "xml_bytes"
            ]
        )
    )

    print(
        "--- CAMPOS TRIBUTARIOS RECUPERADOS ---"
    )

    for nome, valor in resultado[
        "campos"
    ].items():
        print(
            nome
            + ": "
            + (
                str(
                    valor
                )
                if valor is not None
                else "<ausente>"
            )
        )

    print(
        "REDE UTILIZADA: True"
    )
    print(
        "METODO: GET"
    )
    print(
        "POST /nfse: NAO EXECUTADO"
    )
    print(
        "EVENTO/CANCELAMENTO: NAO EXECUTADO"
    )
    print(
        "FLASK INICIALIZADO: False"
    )
    print(
        "BANCO ACESSADO: False"
    )

    return 0


def main() -> int:
    try:
        return executar()
    except (
        ConsultaNfseProducaoInvalida,
        h4f9.PreflightStandaloneInvalido,
    ) as exc:
        print(
            "=== H4-F13 | CONSULTA READ-ONLY NFSE PRODUCAO ==="
        )
        print(
            "STATUS: FALHA"
        )
        print(
            "MOTIVO: "
            + str(
                exc
            )
        )
        print(
            "POST /nfse: NAO EXECUTADO"
        )
        print(
            "EVENTO/CANCELAMENTO: NAO EXECUTADO"
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
