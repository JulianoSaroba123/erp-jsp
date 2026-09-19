from types import SimpleNamespace

import pytest

from app.fiscal import nfse_service as service
from app.fiscal.xml.dps_signer import AssinaturaXmlDpsInvalida


def _resultado_xsd(valido=True, erros=None):
    return SimpleNamespace(
        valido=valido,
        erros=list(erros or []),
    )


def _kwargs(*, material_certificado=None):
    return {
        "documento": SimpleNamespace(),
        "ordem_servico": SimpleNamespace(),
        "configuracao_fiscal": SimpleNamespace(),
        "configuracao_institucional": SimpleNamespace(),
        "versao_layout": "1.01",
        "tipo_emitente": 1,
        "municipio_incidencia_ibge": "3554508",
        "iss": {},
        "totais_tributos": {},
        "material_certificado": material_certificado,
    }


def _mock_base(monkeypatch):
    monkeypatch.setattr(
        service,
        "preparar_payload_nfse",
        lambda **kwargs: {
            "conteudo": None,
            "provider": "SEFIN_NACIONAL",
        },
    )

    monkeypatch.setattr(
        service,
        "montar_dps_canonica_da_os",
        lambda **kwargs: {
            "identificacao": {
                "id": "IDTESTE",
            }
        },
    )

    monkeypatch.setattr(
        service,
        "montar_xml_dps_serializado",
        lambda dps: b"<DPS>ORIGINAL</DPS>",
    )

    monkeypatch.setattr(
        service,
        "obter_caminho_xsd_dps",
        lambda versao: "DPS_v1.01.xsd",
    )


def test_b8a2_pipeline_001_sem_certificado_preserva_b7(
    monkeypatch,
):
    _mock_base(monkeypatch)

    chamadas_xsd = []

    def validar(xml, caminho):
        chamadas_xsd.append(xml)
        return _resultado_xsd()

    monkeypatch.setattr(
        service,
        "validar_xml_dps_xsd",
        validar,
    )

    def nao_assinar(*args, **kwargs):
        raise AssertionError(
            "Assinador nao deve ser chamado sem certificado."
        )

    monkeypatch.setattr(
        service,
        "assinar_xml_dps",
        nao_assinar,
    )

    payload = service.preparar_payload_nfse_com_dps(
        **_kwargs()
    )

    assert payload["conteudo"] == b"<DPS>ORIGINAL</DPS>"
    assert chamadas_xsd == [
        b"<DPS>ORIGINAL</DPS>",
    ]


def test_b8a2_pipeline_002_com_certificado_assina_e_revalida(
    monkeypatch,
):
    _mock_base(monkeypatch)

    material = object()
    chamadas_xsd = []
    chamadas_assinatura = []

    def validar(xml, caminho):
        chamadas_xsd.append(xml)
        return _resultado_xsd()

    def assinar(xml, *, material_certificado):
        chamadas_assinatura.append(
            (
                xml,
                material_certificado,
            )
        )
        return b"<DPS>ASSINADA</DPS>"

    monkeypatch.setattr(
        service,
        "validar_xml_dps_xsd",
        validar,
    )

    monkeypatch.setattr(
        service,
        "assinar_xml_dps",
        assinar,
    )

    payload = service.preparar_payload_nfse_com_dps(
        **_kwargs(
            material_certificado=material,
        )
    )

    assert payload["conteudo"] == b"<DPS>ASSINADA</DPS>"

    assert chamadas_xsd == [
        b"<DPS>ORIGINAL</DPS>",
        b"<DPS>ASSINADA</DPS>",
    ]

    assert chamadas_assinatura == [
        (
            b"<DPS>ORIGINAL</DPS>",
            material,
        )
    ]


def test_b8a2_pipeline_003_normaliza_falha_assinatura(
    monkeypatch,
):
    _mock_base(monkeypatch)

    monkeypatch.setattr(
        service,
        "validar_xml_dps_xsd",
        lambda xml, caminho: _resultado_xsd(),
    )

    def falhar(*args, **kwargs):
        raise AssinaturaXmlDpsInvalida(
            "assinatura invalida de teste"
        )

    monkeypatch.setattr(
        service,
        "assinar_xml_dps",
        falhar,
    )

    with pytest.raises(
        service.PreparacaoNfseInvalida,
        match="Falha ao assinar XML da DPS",
    ):
        service.preparar_payload_nfse_com_dps(
            **_kwargs(
                material_certificado=object(),
            )
        )


def test_b8a2_pipeline_004_bloqueia_xsd_assinado_invalido(
    monkeypatch,
):
    _mock_base(monkeypatch)

    resultados = iter(
        [
            _resultado_xsd(),
            _resultado_xsd(
                False,
                ["Signature fora do schema"],
            ),
        ]
    )

    monkeypatch.setattr(
        service,
        "validar_xml_dps_xsd",
        lambda xml, caminho: next(resultados),
    )

    monkeypatch.setattr(
        service,
        "assinar_xml_dps",
        lambda xml, **kwargs: b"<DPS>ASSINADA</DPS>",
    )

    with pytest.raises(
        service.PreparacaoNfseInvalida,
        match="XML assinado da DPS invalido",
    ):
        service.preparar_payload_nfse_com_dps(
            **_kwargs(
                material_certificado=object(),
            )
        )


def test_b8a2_pipeline_005_orquestrador_repassa_certificado(
    monkeypatch,
):
    documento = SimpleNamespace(
        status="RASCUNHO",
        mensagem_status=None,
    )

    material = object()
    capturado = {}
    commits = []
    rollbacks = []

    monkeypatch.setattr(
        service,
        "reservar_rps_nfse",
        lambda **kwargs: (
            documento,
            True,
        ),
    )

    def preparar(**kwargs):
        capturado.update(kwargs)
        return {
            "conteudo": b"<DPS>ASSINADA</DPS>",
        }

    monkeypatch.setattr(
        service,
        "preparar_payload_nfse_com_dps",
        preparar,
    )

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

    argumentos = _kwargs(
        material_certificado=material,
    )
    argumentos["documento"] = documento

    documento_final, payload = (
        service.preparar_documento_nfse_com_dps(
            **argumentos
        )
    )

    assert (
        capturado["material_certificado"]
        is material
    )

    assert documento_final is documento
    assert documento_final.status == "PREPARADA"

    assert (
        "assinada digitalmente"
        in documento_final.mensagem_status
    )

    assert payload["conteudo"] == b"<DPS>ASSINADA</DPS>"
    assert commits == [True]
    assert rollbacks == []


def test_b8a2_pipeline_006_sem_certificado_preserva_status_b7(
    monkeypatch,
):
    documento = SimpleNamespace(
        status="RASCUNHO",
        mensagem_status=None,
    )

    monkeypatch.setattr(
        service,
        "reservar_rps_nfse",
        lambda **kwargs: (
            documento,
            False,
        ),
    )

    monkeypatch.setattr(
        service,
        "preparar_payload_nfse_com_dps",
        lambda **kwargs: {
            "conteudo": b"<DPS/>",
        },
    )

    monkeypatch.setattr(
        service,
        "_commit_preparacao_local_nfse",
        lambda: None,
    )

    monkeypatch.setattr(
        service,
        "_rollback_preparacao_local_nfse",
        lambda: None,
    )

    argumentos = _kwargs()
    argumentos["documento"] = documento

    documento_final, _ = (
        service.preparar_documento_nfse_com_dps(
            **argumentos
        )
    )

    assert documento_final.status == "PREPARADA"

    assert documento_final.mensagem_status == (
        "DPS preparada localmente e validada contra o XSD. "
        "Nenhuma NFS-e foi transmitida."
    )
