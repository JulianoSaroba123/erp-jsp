import pytest

from app.fiscal.providers.base import (
    ErroAutenticacaoNfse,
    ErroTransmissaoNfse,
    IndisponibilidadeNfse,
)
from app.fiscal.providers.sefin_nacional_http import (
    ClienteHttpSefin,
)


class RespostaFake:
    def __init__(
        self,
        status_code,
        conteudo,
    ):
        self.status_code = status_code
        self.content = conteudo
        self.headers = {
            "Content-Type": "application/json",
            "X-Teste": "B8-A3.5A",
        }


class SessaoFake:
    def __init__(
        self,
        resposta,
    ):
        self.resposta = resposta
        self.chamadas = []

    def request(
        self,
        **kwargs,
    ):
        self.chamadas.append(
            kwargs
        )

        return self.resposta


def _executar(
    *,
    status_code,
    conteudo,
):
    sessao = SessaoFake(
        RespostaFake(
            status_code,
            conteudo,
        )
    )

    cliente = ClienteHttpSefin(
        session=sessao
    )

    cliente.requisitar(
        metodo="POST",
        url="https://sefin.teste/nfse",
        conteudo=b"{}",
    )


def test_b8a3a5a_001_preserva_corpo_no_400():
    corpo = (
        b'{"erros":[{"codigo":"E001"}]}'
    )

    with pytest.raises(
        ErroTransmissaoNfse,
    ) as captura:
        _executar(
            status_code=400,
            conteudo=corpo,
        )

    exc = captura.value

    assert exc.status_code == 400
    assert exc.metodo == "POST"
    assert exc.url == "https://sefin.teste/nfse"
    assert exc.conteudo == corpo

    assert exc.headers[
        "Content-Type"
    ] == "application/json"


def test_b8a3a5a_002_preserva_corpo_no_403():
    corpo = (
        b'{"erros":[{"codigo":"AUT001"}]}'
    )

    with pytest.raises(
        ErroAutenticacaoNfse,
    ) as captura:
        _executar(
            status_code=403,
            conteudo=corpo,
        )

    exc = captura.value

    assert exc.status_code == 403
    assert exc.conteudo == corpo
    assert exc.headers[
        "X-Teste"
    ] == "B8-A3.5A"


def test_b8a3a5a_003_preserva_corpo_no_500():
    corpo = (
        b'{"erros":[{"codigo":"SYS001"}]}'
    )

    with pytest.raises(
        IndisponibilidadeNfse,
    ) as captura:
        _executar(
            status_code=500,
            conteudo=corpo,
        )

    exc = captura.value

    assert exc.status_code == 500
    assert exc.conteudo == corpo


def test_b8a3a5a_004_mantem_classificacao_404():
    with pytest.raises(
        ErroTransmissaoNfse,
    ) as captura:
        _executar(
            status_code=404,
            conteudo=b'{"erro":"nao encontrado"}',
        )

    assert captura.value.status_code == 404


def test_b8a3a5a_005_mantem_classificacao_503():
    with pytest.raises(
        IndisponibilidadeNfse,
    ) as captura:
        _executar(
            status_code=503,
            conteudo=b'{"erro":"indisponivel"}',
        )

    assert captura.value.status_code == 503
