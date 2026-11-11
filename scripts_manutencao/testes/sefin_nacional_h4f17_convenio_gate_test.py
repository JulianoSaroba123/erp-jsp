"""H4-F17 - contrato do gate local de convênio municipal."""

import json

import pytest

from app.fiscal.providers.sefin_nacional_config import (
    ROTAS_SEFIN_NACIONAL,
)
from app.fiscal.providers.sefin_nacional_convenio import (
    RespostaConvenioInvalida,
    interpretar_resposta_convenio,
    validar_convenio_ativo,
)


def test_h4f17_001_rota_parametrizacao_usa_endpoint_real():
    rota = ROTAS_SEFIN_NACIONAL[
        "parametros_convenio"
    ]

    assert rota[
        "metodo"
    ] == "GET"
    assert rota[
        "servico"
    ] == "PARAMETRIZACAO"
    assert rota[
        "rota"
    ] == (
        "/parametrizacao/"
        "{codigo_municipio}/convenio"
    )


def test_h4f17_002_producao_200_e_ativo():
    resultado = interpretar_resposta_convenio(
        ambiente="PRODUCAO",
        codigo_municipio="3554508",
        status_code=200,
        conteudo=json.dumps(
            {
                "mensagem": (
                    "Parâmetros do convênio recuperados com sucesso."
                ),
                "parametrosConvenio": {},
            },
            ensure_ascii=False,
        ).encode(
            "utf-8"
        ),
    )

    assert resultado.ativo is True
    assert resultado.bloqueio_ambiental is False
    validar_convenio_ativo(
        resultado
    )


def test_h4f17_003_prodrest_404_e_bloqueio_ambiental():
    resultado = interpretar_resposta_convenio(
        ambiente="HOMOLOGACAO",
        codigo_municipio="3554508",
        status_code=404,
        conteudo=json.dumps(
            {
                "mensagem": (
                    "O convênio do o município <Tietê/SP> ainda "
                    "não está ativo no Sistema Nacional da NFS-e"
                ),
                "parametrosConvenio": None,
            },
            ensure_ascii=False,
        ).encode(
            "utf-8"
        ),
    )

    assert resultado.ativo is False
    assert resultado.bloqueio_ambiental is True

    with pytest.raises(
        RespostaConvenioInvalida,
        match="bloqueada antes do POST",
    ):
        validar_convenio_ativo(
            resultado
        )


def test_h4f17_004_404_generico_nao_e_confundido_com_convenio_inativo():
    resultado = interpretar_resposta_convenio(
        ambiente="HOMOLOGACAO",
        codigo_municipio="3554508",
        status_code=404,
        conteudo=json.dumps(
            {
                "mensagem": "Recurso não encontrado.",
            },
            ensure_ascii=False,
        ).encode(
            "utf-8"
        ),
    )

    assert resultado.ativo is False
    assert resultado.bloqueio_ambiental is False


def test_h4f17_005_preserva_mensagem_oficial():
    mensagem = (
        "O convênio do o município <Tietê/SP> ainda "
        "não está ativo no Sistema Nacional da NFS-e"
    )

    resultado = interpretar_resposta_convenio(
        ambiente="HOMOLOGACAO",
        codigo_municipio="3554508",
        status_code=404,
        conteudo=json.dumps(
            {
                "mensagem": mensagem,
                "parametrosConvenio": None,
            },
            ensure_ascii=False,
        ).encode(
            "utf-8"
        ),
    )

    assert resultado.mensagem == mensagem


def test_h4f17_006_json_invalido_falha_controlada():
    with pytest.raises(
        RespostaConvenioInvalida,
        match="JSON válido",
    ):
        interpretar_resposta_convenio(
            ambiente="HOMOLOGACAO",
            codigo_municipio="3554508",
            status_code=404,
            conteudo=b"<html>erro</html>",
        )


def test_h4f17_007_gate_nao_realiza_http_ou_banco():
    import inspect
    import app.fiscal.providers.sefin_nacional_convenio as modulo

    texto = inspect.getsource(
        modulo
    ).lower()

    assert "requests" not in texto
    assert "sqlalchemy" not in texto
    assert "db.session" not in texto
    assert "create_app" not in texto
