import builtins
from types import SimpleNamespace

import pytest

from app.fiscal.providers.base import IntegracaoFiscalDesativada
from app.fiscal.providers.geisweb_tiete import GeisWebTieteProvider


def test_h3_s5f_disjuntor_bloqueia_antes_do_modulo_de_transmissao(
    monkeypatch,
):
    provider = GeisWebTieteProvider()

    configuracao = SimpleNamespace(
        provider="GEISWEB_TIETE",
        ambiente="HOMOLOGACAO",
        municipio_ibge="3554508",
        integracao_ativa=False,
    )

    payload = {
        "provider": "GEISWEB_TIETE",
        "conteudo": b"<xml/>",
    }

    import_original = builtins.__import__
    tentativas_transmissao = []

    def import_vigiado(
        name,
        globals=None,
        locals=None,
        fromlist=(),
        level=0,
    ):
        if name == (
            "app.fiscal.providers."
            "geisweb_tiete_transmissao"
        ):
            tentativas_transmissao.append(name)

            raise AssertionError(
                "Disjuntor falhou: modulo de transmissao "
                "GeisWeb foi alcancado."
            )

        return import_original(
            name,
            globals,
            locals,
            fromlist,
            level,
        )

    monkeypatch.setattr(
        builtins,
        "__import__",
        import_vigiado,
    )

    with pytest.raises(
        IntegracaoFiscalDesativada,
        match="Integracao fiscal externa esta desativada",
    ):
        provider.transmitir(
            payload=payload,
            configuracao=configuracao,
        )

    assert tentativas_transmissao == []
