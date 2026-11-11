"""H4-F18 - gate operacional de convênio antes do POST /nfse."""

from contextlib import contextmanager
import json
from types import SimpleNamespace

import pytest

from app.fiscal.providers import sefin_nacional as provider_modulo
from app.fiscal.providers import (
    sefin_nacional_parametrizacao as parametrizacao,
)
from app.fiscal.providers.base import (
    ErroTransmissaoNfse,
    IntegracaoFiscalDesativada,
)
from app.fiscal.providers.sefin_nacional import (
    SefinNacionalProvider,
)


def _configuracao(
    *,
    ativa=True,
    ambiente="HOMOLOGACAO",
):
    return SimpleNamespace(
        provider="SEFIN_NACIONAL",
        ambiente=ambiente,
        integracao_ativa=ativa,
    )


def _payload(
    *,
    ambiente="HOMOLOGACAO",
):
    return {
        "provider": "SEFIN_NACIONAL",
        "ambiente": ambiente,
        "conteudo": b"<DPS-assinada/>",
    }


def _resposta_http(
    status_code,
    conteudo,
):
    return SimpleNamespace(
        status_code=status_code,
        conteudo=conteudo,
        headers={},
        metodo="GET",
        url="https://teste/convenio",
    )


def _erro_http(
    status_code,
    conteudo,
):
    erro = ErroTransmissaoNfse(
        "erro http controlado"
    )
    erro.status_code = status_code
    erro.conteudo = conteudo
    return erro


@contextmanager
def _mtls_fake(material):
    yield (
        "cert-teste.pem",
        "key-teste.pem",
    )


def test_h4f18_001_consulta_usa_get_parametrizacao_e_mtls(
    monkeypatch,
):
    monkeypatch.setenv(
        "NFSE_PARAMETRIZACAO_BASE_URL_HOMOLOGACAO",
        "https://adn.producaorestrita.nfse.gov.br",
    )

    monkeypatch.setattr(
        parametrizacao,
        "materializar_mtls_sefin",
        _mtls_fake,
    )

    chamadas = []

    class ClienteFake:
        def requisitar(self, **kwargs):
            chamadas.append(
                kwargs
            )
            return _resposta_http(
                200,
                json.dumps(
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

    resultado = parametrizacao.executar_consulta_convenio_http(
        ambiente="HOMOLOGACAO",
        codigo_municipio="3554508",
        material_certificado=object(),
        cliente_http=ClienteFake(),
    )

    assert resultado.ativo is True
    assert len(
        chamadas
    ) == 1

    chamada = chamadas[
        0
    ]

    assert chamada[
        "metodo"
    ] == "GET"
    assert chamada[
        "url"
    ] == (
        "https://adn.producaorestrita.nfse.gov.br"
        "/parametrizacao/3554508/convenio"
    )
    assert chamada[
        "conteudo"
    ] is None
    assert chamada[
        "certificado_cliente"
    ] == (
        "cert-teste.pem",
        "key-teste.pem",
    )


def test_h4f18_002_404_convenio_inativo_bloqueia(
    monkeypatch,
):
    monkeypatch.setenv(
        "NFSE_PARAMETRIZACAO_BASE_URL_HOMOLOGACAO",
        "https://adn.producaorestrita.nfse.gov.br",
    )

    monkeypatch.setattr(
        parametrizacao,
        "materializar_mtls_sefin",
        _mtls_fake,
    )

    corpo = json.dumps(
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
    )

    class ClienteFake:
        def requisitar(self, **kwargs):
            raise _erro_http(
                404,
                corpo,
            )

    with pytest.raises(
        parametrizacao.ValidacaoConvenioSefinInvalida,
        match="antes do POST",
    ) as exc_info:
        parametrizacao.executar_consulta_convenio_http(
            ambiente="HOMOLOGACAO",
            codigo_municipio="3554508",
            material_certificado=object(),
            cliente_http=ClienteFake(),
        )

    erro = exc_info.value
    assert erro.status_code == 404
    assert erro.resultado_convenio.ativo is False
    assert erro.resultado_convenio.bloqueio_ambiental is True


def test_h4f18_003_500_continua_erro_tecnico(
    monkeypatch,
):
    monkeypatch.setenv(
        "NFSE_PARAMETRIZACAO_BASE_URL_HOMOLOGACAO",
        "https://adn.producaorestrita.nfse.gov.br",
    )

    monkeypatch.setattr(
        parametrizacao,
        "materializar_mtls_sefin",
        _mtls_fake,
    )

    erro = _erro_http(
        500,
        b'{"mensagem":"indisponivel"}',
    )

    class ClienteFake:
        def requisitar(self, **kwargs):
            raise erro

    with pytest.raises(
        ErroTransmissaoNfse,
    ) as exc_info:
        parametrizacao.executar_consulta_convenio_http(
            ambiente="HOMOLOGACAO",
            codigo_municipio="3554508",
            material_certificado=object(),
            cliente_http=ClienteFake(),
        )

    assert exc_info.value is erro


def test_h4f18_004_provider_valida_convenio_antes_do_post(
    monkeypatch,
):
    provider = SefinNacionalProvider()
    eventos = []
    material = object()

    monkeypatch.setattr(
        provider_modulo,
        "carregar_certificado_a1_do_ambiente",
        lambda: material,
    )

    def consultar(**kwargs):
        eventos.append(
            "GET_CONVENIO"
        )
        assert kwargs[
            "ambiente"
        ] == "HOMOLOGACAO"
        assert kwargs[
            "codigo_municipio"
        ] == "3554508"
        assert kwargs[
            "material_certificado"
        ] is material

        return SimpleNamespace(
            ativo=True
        )

    def emitir(**kwargs):
        eventos.append(
            "POST_NFSE"
        )

        erro = ErroTransmissaoNfse(
            "HTTP 400 controlado"
        )
        erro.status_code = 400
        erro.conteudo = json.dumps(
            {
                "tipoAmbiente": 2,
                "versaoAplicativo": "SEFIN-TESTE",
                "dataHoraProcessamento": (
                    "2026-11-11T20:00:00-03:00"
                ),
                "idDPS": "DPS123",
                "erros": [
                    {
                        "Codigo": "E-TESTE",
                        "Descricao": "Rejeição controlada",
                    }
                ],
            },
            ensure_ascii=False,
        ).encode(
            "utf-8"
        )
        raise erro

    monkeypatch.setattr(
        provider_modulo,
        "executar_consulta_convenio_http",
        consultar,
    )

    monkeypatch.setattr(
        provider_modulo,
        "executar_emissao_nfse_http",
        emitir,
    )

    resultado = provider.transmitir(
        payload=_payload(),
        configuracao=_configuracao(),
    )

    assert resultado[
        "status"
    ] == "REJEITADA"
    assert eventos == [
        "GET_CONVENIO",
        "POST_NFSE",
    ]


def test_h4f18_005_convenio_inativo_impede_post(
    monkeypatch,
):
    provider = SefinNacionalProvider()
    material = object()
    post_chamado = False

    monkeypatch.setattr(
        provider_modulo,
        "carregar_certificado_a1_do_ambiente",
        lambda: material,
    )

    def consultar(**kwargs):
        raise parametrizacao.ValidacaoConvenioSefinInvalida(
            "Município sem convênio ativo no ambiente HOMOLOGACAO. "
            "Emissão deve ser bloqueada antes do POST /nfse."
        )

    def emitir(**kwargs):
        nonlocal post_chamado
        post_chamado = True
        raise AssertionError(
            "POST não deveria ser executado."
        )

    monkeypatch.setattr(
        provider_modulo,
        "executar_consulta_convenio_http",
        consultar,
    )

    monkeypatch.setattr(
        provider_modulo,
        "executar_emissao_nfse_http",
        emitir,
    )

    with pytest.raises(
        parametrizacao.ValidacaoConvenioSefinInvalida,
        match="antes do POST",
    ):
        provider.transmitir(
            payload=_payload(),
            configuracao=_configuracao(),
        )

    assert post_chamado is False


def test_h4f18_006_disjuntor_impede_certificado_get_e_post(
    monkeypatch,
):
    provider = SefinNacionalProvider()
    eventos = []

    monkeypatch.setattr(
        provider_modulo,
        "carregar_certificado_a1_do_ambiente",
        lambda: eventos.append(
            "CERTIFICADO"
        ),
    )

    monkeypatch.setattr(
        provider_modulo,
        "executar_consulta_convenio_http",
        lambda **kwargs: eventos.append(
            "GET_CONVENIO"
        ),
    )

    monkeypatch.setattr(
        provider_modulo,
        "executar_emissao_nfse_http",
        lambda **kwargs: eventos.append(
            "POST_NFSE"
        ),
    )

    with pytest.raises(
        IntegracaoFiscalDesativada,
    ):
        provider.transmitir(
            payload=_payload(),
            configuracao=_configuracao(
                ativa=False
            ),
        )

    assert eventos == []


def test_h4f18_007_payload_invalido_impede_get_convenio(
    monkeypatch,
):
    provider = SefinNacionalProvider()
    eventos = []

    monkeypatch.setattr(
        provider_modulo,
        "carregar_certificado_a1_do_ambiente",
        lambda: eventos.append(
            "CERTIFICADO"
        ),
    )

    monkeypatch.setattr(
        provider_modulo,
        "executar_consulta_convenio_http",
        lambda **kwargs: eventos.append(
            "GET_CONVENIO"
        ),
    )

    payload = _payload()
    payload[
        "conteudo"
    ] = None

    with pytest.raises(
        ErroTransmissaoNfse,
        match="XML DPS assinado",
    ):
        provider.transmitir(
            payload=payload,
            configuracao=_configuracao(),
        )

    assert eventos == []


def test_h4f18_008_producao_propaga_ambiente_ao_gate(
    monkeypatch,
):
    provider = SefinNacionalProvider()
    material = object()
    ambientes = []

    monkeypatch.setattr(
        provider_modulo,
        "carregar_certificado_a1_do_ambiente",
        lambda: material,
    )

    def consultar(**kwargs):
        ambientes.append(
            kwargs[
                "ambiente"
            ]
        )
        return SimpleNamespace(
            ativo=True
        )

    def emitir(**kwargs):
        raise ErroTransmissaoNfse(
            "parada controlada após gate"
        )

    monkeypatch.setattr(
        provider_modulo,
        "executar_consulta_convenio_http",
        consultar,
    )
    monkeypatch.setattr(
        provider_modulo,
        "executar_emissao_nfse_http",
        emitir,
    )

    with pytest.raises(
        ErroTransmissaoNfse,
        match="parada controlada",
    ):
        provider.transmitir(
            payload=_payload(
                ambiente="PRODUCAO"
            ),
            configuracao=_configuracao(
                ambiente="PRODUCAO"
            ),
        )

    assert ambientes == [
        "PRODUCAO",
    ]


def test_h4f18_009_gate_nao_executa_post():
    import inspect

    texto = inspect.getsource(
        parametrizacao
    ).lower()

    assert 'metodo="get"' in texto
    assert 'metodo="post"' not in texto
    assert ".post(" not in texto
    assert "sqlalchemy" not in texto
    assert "db.session" not in texto
