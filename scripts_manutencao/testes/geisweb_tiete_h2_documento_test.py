import hashlib
from types import SimpleNamespace

import pytest

from app.fiscal import nfse_service as service


def _objetos():
    documento = SimpleNamespace(
        status="RASCUNHO",
        mensagem_status=None,
    )

    return (
        documento,
        SimpleNamespace(),
        SimpleNamespace(),
        SimpleNamespace(),
    )


def test_h2_prepara_documento_geisweb_sem_rede(
    monkeypatch,
):
    (
        documento,
        ordem,
        configuracao,
        institucional,
    ) = _objetos()

    chamadas = {}

    def reservar(**kwargs):
        chamadas["reservar"] = kwargs
        return documento, True

    def preparar(**kwargs):
        chamadas["preparar"] = kwargs

        return {
            "provider": "GEISWEB_TIETE",
            "conteudo": b"<EnviaLoteRps/>",
            "validacao_xsd": {
                "valido": True,
                "erros": (),
            },
        }

    monkeypatch.setattr(
        service,
        "reservar_rps_nfse",
        reservar,
    )

    monkeypatch.setattr(
        service,
        "preparar_payload_nfse_com_geisweb",
        preparar,
    )

    commits = []
    rollbacks = []

    monkeypatch.setattr(
        service,
        "_commit_preparacao_local_nfse",
        lambda: commits.append(True),
    )

    monkeypatch.setattr(
        service,
        "_rollback_preparacao_local_nfse",
        lambda: rollbacks.append(True),
    )

    documento_resultado, payload = (
        service.preparar_documento_nfse_com_geisweb(
            documento=documento,
            ordem_servico=ordem,
            configuracao_fiscal=configuracao,
            configuracao_institucional=institucional,
            numero_lote="10",
            data_emissao="2026-09-21",
            tipo_lancamento="1",
            regime_geisweb="SIMPLES_NACIONAL",
            codigo_nacional="1406",
            base_calculo="2800.00",
            ibs_cbs={
                "c_class_trib": "TESTE",
                "ibs": "2.80",
                "cbs": "25.20",
                "c_class_trib_reg": "",
            },
            outros_impostos={
                "pis": "0.00",
                "cofins": "0.00",
                "csll": "0.00",
                "irrf": "0.00",
                "inss": "0.00",
            },
        )
    )

    # H3-S5N-C: artefato fiscal persistido
    conteudo = bytes(payload["conteudo"])

    assert documento_resultado is documento
    assert documento.xml_envio == conteudo

    hash_esperado = hashlib.sha256(
        conteudo
    ).hexdigest()

    assert documento.xml_envio_sha256 == hash_esperado
    assert len(documento.xml_envio_sha256) == 64

    assert documento.preparado_em is not None
    assert documento.preparado_em.tzinfo is not None

    assert documento.status == "PREPARADA"

    assert documento_resultado is documento
    assert documento.status == "PREPARADA"
    assert payload["provider"] == "GEISWEB_TIETE"

    assert len(commits) == 1
    assert rollbacks == []

    assert chamadas["preparar"]["documento"] is documento
    assert chamadas["preparar"]["ordem_servico"] is ordem


def test_h2_falha_faz_rollback(
    monkeypatch,
):
    (
        documento,
        ordem,
        configuracao,
        institucional,
    ) = _objetos()

    monkeypatch.setattr(
        service,
        "reservar_rps_nfse",
        lambda **kwargs: (documento, True),
    )

    def falhar(**kwargs):
        raise RuntimeError("falha controlada")

    monkeypatch.setattr(
        service,
        "preparar_payload_nfse_com_geisweb",
        falhar,
    )

    commits = []
    rollbacks = []

    monkeypatch.setattr(
        service,
        "_commit_preparacao_local_nfse",
        lambda: commits.append(True),
    )

    monkeypatch.setattr(
        service,
        "_rollback_preparacao_local_nfse",
        lambda: rollbacks.append(True),
    )

    with pytest.raises(
        RuntimeError,
        match="falha controlada",
    ):
        service.preparar_documento_nfse_com_geisweb(
            documento=documento,
            ordem_servico=ordem,
            configuracao_fiscal=configuracao,
            configuracao_institucional=institucional,
            numero_lote="10",
            data_emissao="2026-09-21",
            tipo_lancamento="1",
            regime_geisweb="TESTE",
            codigo_nacional="1406",
            base_calculo="100.00",
            ibs_cbs={},
            outros_impostos={},
        )

    assert commits == []
    assert rollbacks == [True]


def test_h2_nao_transmite(
    monkeypatch,
):
    (
        documento,
        ordem,
        configuracao,
        institucional,
    ) = _objetos()

    monkeypatch.setattr(
        service,
        "reservar_rps_nfse",
        lambda **kwargs: (documento, True),
    )

    monkeypatch.setattr(
        service,
        "preparar_payload_nfse_com_geisweb",
        lambda **kwargs: {
            "provider": "GEISWEB_TIETE",
            "conteudo": b"<xml/>",
        },
    )

    monkeypatch.setattr(
        service,
        "_commit_preparacao_local_nfse",
        lambda: None,
    )

    def rede_proibida(*args, **kwargs):
        raise AssertionError(
            "H2 nao pode transmitir."
        )

    monkeypatch.setattr(
        service,
        "transmitir_payload_nfse",
        rede_proibida,
    )

    service.preparar_documento_nfse_com_geisweb(
        documento=documento,
        ordem_servico=ordem,
        configuracao_fiscal=configuracao,
        configuracao_institucional=institucional,
        numero_lote="10",
        data_emissao="2026-09-21",
        tipo_lancamento="1",
        regime_geisweb="TESTE",
        codigo_nacional="1406",
        base_calculo="100.00",
        ibs_cbs={},
        outros_impostos={},
    )

    assert documento.status == "PREPARADA"
