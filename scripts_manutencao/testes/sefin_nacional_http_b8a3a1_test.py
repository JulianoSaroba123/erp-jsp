from types import SimpleNamespace

import pytest
import requests

from app.fiscal.providers.base import (
    ErroAutenticacaoNfse,
    ErroComunicacaoNfse,
    ErroTransmissaoNfse,
    IndisponibilidadeNfse,
)
from app.fiscal.providers.sefin_nacional_http import (
    ClienteHttpSefin,
)


class SessaoFake:
    def __init__(
        self,
        *,
        resposta=None,
        erro=None,
    ):
        self.resposta = resposta
        self.erro = erro
        self.chamadas = []

    def request(self, **kwargs):
        self.chamadas.append(
            kwargs
        )

        if self.erro is not None:
            raise self.erro

        return self.resposta


def _resposta(
    status_code=200,
    conteudo=b"OK",
):
    return SimpleNamespace(
        status_code=status_code,
        headers={
            "Content-Type": "application/json",
        },
        content=conteudo,
    )


def test_b8a3a1_001_post_https_com_timeout():
    sessao = SessaoFake(
        resposta=_resposta(
            200,
            b'{"ok":true}',
        )
    )

    cliente = ClienteHttpSefin(
        session=sessao,
        timeout_conexao=5,
        timeout_leitura=20,
    )

    resposta = cliente.requisitar(
        metodo="POST",
        url="https://sefin.teste/nfse",
        headers={
            "Content-Type": "application/json",
        },
        conteudo=b'{"dps":"teste"}',
    )

    assert resposta.status_code == 200
    assert resposta.conteudo == b'{"ok":true}'

    assert len(
        sessao.chamadas
    ) == 1

    chamada = sessao.chamadas[0]

    assert chamada["method"] == "POST"
    assert chamada["timeout"] == (
        5.0,
        20.0,
    )
    assert chamada["verify"] is True
    assert chamada["allow_redirects"] is False


def test_b8a3a1_002_bloqueia_http_sem_tls():
    cliente = ClienteHttpSefin(
        session=SessaoFake()
    )

    with pytest.raises(
        ValueError,
        match="HTTPS",
    ):
        cliente.requisitar(
            metodo="GET",
            url="http://sefin.teste/nfse",
        )


@pytest.mark.parametrize(
    "metodo",
    [
        "",
        "PUT",
        "DELETE",
        "PATCH",
    ],
)
def test_b8a3a1_003_bloqueia_metodo_invalido(
    metodo,
):
    cliente = ClienteHttpSefin(
        session=SessaoFake()
    )

    with pytest.raises(
        ValueError,
        match="Metodo HTTP",
    ):
        cliente.requisitar(
            metodo=metodo,
            url="https://sefin.teste/nfse",
        )


def test_b8a3a1_004_timeout_vira_erro_comunicacao():
    sessao = SessaoFake(
        erro=requests.Timeout(
            "timeout teste"
        )
    )

    cliente = ClienteHttpSefin(
        session=sessao
    )

    with pytest.raises(
        ErroComunicacaoNfse,
        match="Timeout",
    ):
        cliente.requisitar(
            metodo="POST",
            url="https://sefin.teste/nfse",
        )


def test_b8a3a1_005_connectionerror_vira_erro_comunicacao():
    sessao = SessaoFake(
        erro=requests.ConnectionError(
            "conexao teste"
        )
    )

    cliente = ClienteHttpSefin(
        session=sessao
    )

    with pytest.raises(
        ErroComunicacaoNfse,
        match="conexao",
    ):
        cliente.requisitar(
            metodo="POST",
            url="https://sefin.teste/nfse",
        )


@pytest.mark.parametrize(
    "status",
    [
        401,
        403,
    ],
)
def test_b8a3a1_006_autenticacao(
    status,
):
    cliente = ClienteHttpSefin(
        session=SessaoFake(
            resposta=_resposta(
                status
            )
        )
    )

    with pytest.raises(
        ErroAutenticacaoNfse,
    ):
        cliente.requisitar(
            metodo="POST",
            url="https://sefin.teste/nfse",
        )


@pytest.mark.parametrize(
    "status",
    [
        408,
        425,
        429,
        500,
        503,
    ],
)
def test_b8a3a1_007_indisponibilidade(
    status,
):
    cliente = ClienteHttpSefin(
        session=SessaoFake(
            resposta=_resposta(
                status
            )
        )
    )

    with pytest.raises(
        IndisponibilidadeNfse,
    ):
        cliente.requisitar(
            metodo="POST",
            url="https://sefin.teste/nfse",
        )


@pytest.mark.parametrize(
    "status",
    [
        400,
        404,
        422,
    ],
)
def test_b8a3a1_008_erro_http_funcional(
    status,
):
    cliente = ClienteHttpSefin(
        session=SessaoFake(
            resposta=_resposta(
                status
            )
        )
    )

    with pytest.raises(
        ErroTransmissaoNfse,
    ):
        cliente.requisitar(
            metodo="POST",
            url="https://sefin.teste/nfse",
        )


def test_b8a3a1_009_redirecionamento_bloqueado():
    cliente = ClienteHttpSefin(
        session=SessaoFake(
            resposta=_resposta(
                302
            )
        )
    )

    with pytest.raises(
        ErroComunicacaoNfse,
        match="Redirecionamento",
    ):
        cliente.requisitar(
            metodo="GET",
            url="https://sefin.teste/nfse",
        )


@pytest.mark.parametrize(
    "conexao, leitura",
    [
        (0, 30),
        (10, 0),
        (-1, 30),
        ("abc", 30),
    ],
)
def test_b8a3a1_010_timeout_invalido(
    conexao,
    leitura,
):
    with pytest.raises(
        ValueError,
        match="Timeout",
    ):
        ClienteHttpSefin(
            session=SessaoFake(),
            timeout_conexao=conexao,
            timeout_leitura=leitura,
        )
