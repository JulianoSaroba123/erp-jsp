import base64
import gzip
import json

import pytest

from app.fiscal.providers.sefin_nacional_resposta import (
    RespostaEmissaoSefinInvalida,
    normalizar_resposta_emissao_sefin,
)


def _json_bytes(dados):
    return json.dumps(
        dados,
        separators=(",", ":"),
    ).encode(
        "utf-8"
    )


def _nfse_b64(xml=b"<NFSe>OK</NFSe>"):
    return base64.b64encode(
        gzip.compress(
            xml,
            mtime=0,
        )
    ).decode(
        "ascii"
    )


def _sucesso():
    return {
        "tipoAmbiente": 2,
        "versaoAplicativo": "SEFIN-TESTE",
        "dataHoraProcessamento": "2026-09-19T00:00:00-03:00",
        "idDps": "DPS123",
        "chaveAcesso": "1234567890",
        "nfseXmlGZipB64": _nfse_b64(),
    }


def test_b8a3a4_001_normaliza_sucesso_201():
    resposta = normalizar_resposta_emissao_sefin(
        status_code=201,
        conteudo=_json_bytes(
            _sucesso()
        ),
    )

    assert resposta.sucesso is True
    assert resposta.status_code == 201
    assert resposta.tipo_ambiente == 2
    assert resposta.id_dps == "DPS123"
    assert resposta.chave_acesso == "1234567890"
    assert resposta.nfse_xml == b"<NFSe>OK</NFSe>"
    assert resposta.erros == ()


def test_b8a3a4_002_preserva_alertas():
    dados = _sucesso()

    dados["alertas"] = [
        {
            "codigo": "A001",
            "mensagem": "Alerta de teste",
            "descricao": "Descricao",
            "complemento": "Complemento",
        }
    ]

    resposta = normalizar_resposta_emissao_sefin(
        status_code=201,
        conteudo=_json_bytes(
            dados
        ),
    )

    assert len(
        resposta.alertas
    ) == 1

    alerta = resposta.alertas[0]

    assert alerta.codigo == "A001"
    assert alerta.mensagem == "Alerta de teste"


def test_b8a3a4_003_bloqueia_json_invalido():
    with pytest.raises(
        RespostaEmissaoSefinInvalida,
        match="JSON valido",
    ):
        normalizar_resposta_emissao_sefin(
            status_code=201,
            conteudo=b"{",
        )


def test_b8a3a4_004_bloqueia_campo_obrigatorio_ausente():
    dados = _sucesso()
    dados.pop(
        "chaveAcesso"
    )

    with pytest.raises(
        RespostaEmissaoSefinInvalida,
        match="chaveAcesso",
    ):
        normalizar_resposta_emissao_sefin(
            status_code=201,
            conteudo=_json_bytes(
                dados
            ),
        )


def test_b8a3a4_005_bloqueia_base64_invalido():
    dados = _sucesso()

    dados["nfseXmlGZipB64"] = "***"

    with pytest.raises(
        RespostaEmissaoSefinInvalida,
        match="Base64 invalido",
    ):
        normalizar_resposta_emissao_sefin(
            status_code=201,
            conteudo=_json_bytes(
                dados
            ),
        )


def test_b8a3a4_006_bloqueia_gzip_invalido():
    dados = _sucesso()

    dados["nfseXmlGZipB64"] = base64.b64encode(
        b"nao-e-gzip"
    ).decode(
        "ascii"
    )

    with pytest.raises(
        RespostaEmissaoSefinInvalida,
        match="GZip invalido",
    ):
        normalizar_resposta_emissao_sefin(
            status_code=201,
            conteudo=_json_bytes(
                dados
            ),
        )


@pytest.mark.parametrize(
    "status_code",
    [
        400,
        403,
        500,
    ],
)
def test_b8a3a4_007_normaliza_resposta_de_erro(
    status_code,
):
    dados = {
        "tipoAmbiente": 2,
        "versaoAplicativo": "SEFIN-TESTE",
        "dataHoraProcessamento": "2026-09-19T00:00:00-03:00",
        "idDPS": "DPS123",
        "erros": [
            {
                "codigo": "E001",
                "mensagem": "Erro de teste",
                "descricao": "Descricao do erro",
                "complemento": "Complemento",
            }
        ],
    }

    resposta = normalizar_resposta_emissao_sefin(
        status_code=status_code,
        conteudo=_json_bytes(
            dados
        ),
    )

    assert resposta.sucesso is False
    assert resposta.status_code == status_code
    assert resposta.id_dps == "DPS123"
    assert len(resposta.erros) == 1
    assert resposta.erros[0].codigo == "E001"


def test_b8a3a4_008_exige_erros_na_resposta_de_falha():
    dados = {
        "tipoAmbiente": 2,
        "versaoAplicativo": "SEFIN-TESTE",
        "dataHoraProcessamento": "2026-09-19T00:00:00-03:00",
    }

    with pytest.raises(
        RespostaEmissaoSefinInvalida,
        match="erros",
    ):
        normalizar_resposta_emissao_sefin(
            status_code=400,
            conteudo=_json_bytes(
                dados
            ),
        )


def test_b8a3a4_009_bloqueia_status_nao_documentado():
    with pytest.raises(
        RespostaEmissaoSefinInvalida,
        match="Status HTTP inesperado",
    ):
        normalizar_resposta_emissao_sefin(
            status_code=200,
            conteudo=_json_bytes(
                _sucesso()
            ),
        )
