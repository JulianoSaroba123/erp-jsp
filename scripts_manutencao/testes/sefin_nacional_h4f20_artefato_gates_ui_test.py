"""H4-F20 - artefato SEFIN persistido e gates provider-aware."""

from contextlib import contextmanager
from datetime import datetime, timezone
import hashlib
import inspect
from pathlib import Path
from types import SimpleNamespace

import pytest

from app.fiscal import nfse_service as service


ROUTES = Path(
    "app/ordem_servico/ordem_servico_routes.py"
)

TEMPLATE = Path(
    "app/ordem_servico/templates/os/_painel_fiscal_parcelas.html"
)


def _documento(
    *,
    status="PREPARADA",
    provider="SEFIN_NACIONAL",
    ambiente="HOMOLOGACAO",
    xml=b"<DPS>ASSINADA</DPS>",
):
    return SimpleNamespace(
        id=10,
        status=status,
        provider=provider,
        ambiente=ambiente,
        xml_envio=xml,
        xml_envio_sha256=hashlib.sha256(
            xml
        ).hexdigest(),
        mensagem_status=None,
        serie_rps="9999",
        numero_rps=123,
        preparado_em=None,
    )


def _config(
    *,
    provider="SEFIN_NACIONAL",
    ambiente="HOMOLOGACAO",
):
    return SimpleNamespace(
        id=1,
        provider=provider,
        ambiente=ambiente,
        integracao_ativa=False,
    )


def _ordem():
    return SimpleNamespace(
        id=20,
    )


def test_h4f20_001_preparacao_sefin_persiste_xml_hash_e_data(
    monkeypatch,
):
    documento = _documento(
        status="RASCUNHO",
        xml=b"",
    )
    documento.xml_envio = None
    documento.xml_envio_sha256 = None

    xml = b"<DPS>ASSINADA-CONTROLADA</DPS>"

    monkeypatch.setattr(
        service,
        "reservar_rps_nfse",
        lambda **kwargs: (
            documento,
            True,
        ),
    )

    monkeypatch.setattr(
        service,
        "preparar_payload_nfse_com_dps",
        lambda **kwargs: {
            "provider": "SEFIN_NACIONAL",
            "conteudo": xml,
        },
    )

    commits = []
    rollbacks = []

    monkeypatch.setattr(
        service,
        "_commit_preparacao_local_nfse",
        lambda: commits.append(
            True
        ),
    )
    monkeypatch.setattr(
        service,
        "_rollback_preparacao_local_nfse",
        lambda: rollbacks.append(
            True
        ),
    )

    resultado, payload = service.preparar_documento_nfse_com_dps(
        documento=documento,
        ordem_servico=_ordem(),
        configuracao_fiscal=SimpleNamespace(),
        configuracao_institucional=SimpleNamespace(),
        versao_layout="1.01",
        tipo_emitente="1",
        municipio_incidencia_ibge="3554508",
        iss={},
        totais_tributos={},
        material_certificado=object(),
    )

    assert resultado is documento
    assert payload[
        "conteudo"
    ] == xml
    assert documento.xml_envio == xml
    assert documento.xml_envio_sha256 == hashlib.sha256(
        xml
    ).hexdigest()
    assert isinstance(
        documento.preparado_em,
        datetime,
    )
    assert documento.preparado_em.tzinfo is not None
    assert documento.status == "PREPARADA"
    assert commits == [
        True
    ]
    assert rollbacks == []


def test_h4f20_002_reconstroi_sefin_sem_gerar_nova_dps(
    monkeypatch,
):
    documento = _documento()
    configuracao = _config()
    ordem = _ordem()

    assinatura = []
    xsd = []

    monkeypatch.setattr(
        service,
        "validar_assinatura_xml_dps",
        lambda xml: assinatura.append(
            xml
        ),
    )

    monkeypatch.setattr(
        service,
        "obter_caminho_xsd_dps",
        lambda versao, *, ambiente=None: (
            versao,
            ambiente,
        ),
    )

    monkeypatch.setattr(
        service,
        "validar_xml_dps_xsd",
        lambda xml, caminho: (
            xsd.append(
                (
                    xml,
                    caminho,
                )
            )
            or SimpleNamespace(
                valido=True,
                erros=(),
            )
        ),
    )

    class ProviderFake:
        def preparar_payload(
            self,
            **kwargs,
        ):
            return {
                "provider": "SEFIN_NACIONAL",
                "ambiente": "HOMOLOGACAO",
                "layout": {
                    "versao": "1.01",
                },
                "conteudo": None,
            }

    monkeypatch.setattr(
        service,
        "resolver_provider_nfse",
        lambda configuracao: ProviderFake(),
    )

    payload = service.reconstruir_payload_sefin_para_envio(
        documento=documento,
        ordem_servico=ordem,
        configuracao=configuracao,
    )

    assert payload[
        "conteudo"
    ] == documento.xml_envio
    assert assinatura == [
        documento.xml_envio
    ]
    assert xsd == [
        (
            documento.xml_envio,
            (
                "1.01",
                "HOMOLOGACAO",
            ),
        )
    ]


def test_h4f20_003_reconstrucao_bloqueia_hash_divergente():
    documento = _documento()
    documento.xml_envio_sha256 = "0" * 64

    with pytest.raises(
        service.TransmissaoNfseInvalida,
        match="Integridade do XML SEFIN",
    ):
        service.reconstruir_payload_sefin_para_envio(
            documento=documento,
            ordem_servico=_ordem(),
            configuracao=_config(),
        )


def test_h4f20_004_liberacao_generica_despacha_sefin(
    monkeypatch,
):
    documento = _documento()
    chamadas = []

    monkeypatch.setattr(
        service,
        "reconstruir_payload_sefin_para_envio",
        lambda **kwargs: {
            "provider": "SEFIN_NACIONAL",
            "conteudo": b"<DPS/>",
        },
    )

    def liberar(
        *,
        documento,
        payload,
    ):
        chamadas.append(
            payload[
                "provider"
            ]
        )
        documento.status = "PENDENTE_ENVIO"
        return documento

    monkeypatch.setattr(
        service,
        "preparar_nfse_para_envio",
        liberar,
    )

    resultado = service.liberar_documento_nfse_para_envio(
        documento=documento,
        ordem_servico=_ordem(),
        configuracao=_config(),
    )

    assert resultado is documento
    assert chamadas == [
        "SEFIN_NACIONAL",
    ]


def test_h4f20_005_liberacao_generica_preserva_geisweb(
    monkeypatch,
):
    documento = _documento(
        provider="GEISWEB_TIETE",
    )
    configuracao = _config(
        provider="GEISWEB_TIETE",
    )
    chamadas = []

    monkeypatch.setattr(
        service,
        "liberar_documento_nfse_geisweb_para_envio",
        lambda **kwargs: (
            chamadas.append(
                "GEISWEB_TIETE"
            )
            or documento
        ),
    )

    resultado = service.liberar_documento_nfse_para_envio(
        documento=documento,
        ordem_servico=_ordem(),
        configuracao=configuracao,
    )

    assert resultado is documento
    assert chamadas == [
        "GEISWEB_TIETE",
    ]


def test_h4f20_006_precheck_sefin_e_local_sem_rede(
    monkeypatch,
):
    documento = _documento(
        status="PENDENTE_ENVIO",
    )

    monkeypatch.setattr(
        service,
        "reconstruir_payload_sefin_para_envio",
        lambda **kwargs: {
            "provider": "SEFIN_NACIONAL",
            "conteudo": b"<DPS>OK</DPS>",
        },
    )

    certificado = SimpleNamespace(
        not_valid_before_utc=datetime(
            2026,
            1,
            1,
            tzinfo=timezone.utc,
        ),
        not_valid_after_utc=datetime(
            2027,
            1,
            1,
            tzinfo=timezone.utc,
        ),
    )

    material = SimpleNamespace(
        certificado=certificado,
    )

    monkeypatch.setattr(
        service,
        "carregar_certificado_a1_do_ambiente",
        lambda: material,
    )

    materializados = []

    @contextmanager
    def mtls_fake(material_recebido):
        materializados.append(
            material_recebido
        )
        yield (
            "cert.pem",
            "key.pem",
        )

    monkeypatch.setattr(
        service,
        "materializar_mtls_sefin",
        mtls_fake,
    )

    resultado = service.precheck_transmissao_sefin(
        documento=documento,
        ordem_servico=_ordem(),
        configuracao=_config(),
    )

    assert resultado[
        "ok"
    ] is True
    assert resultado[
        "provider"
    ] == "SEFIN_NACIONAL"
    assert resultado[
        "mtls_pronto"
    ] is True
    assert resultado[
        "integracao_ativa"
    ] is False
    assert resultado[
        "xml_bytes"
    ] == len(
        b"<DPS>OK</DPS>"
    )
    assert materializados == [
        material
    ]


def test_h4f20_007_precheck_generico_despacha_por_provider(
    monkeypatch,
):
    chamadas = []

    monkeypatch.setattr(
        service,
        "precheck_transmissao_sefin",
        lambda **kwargs: (
            chamadas.append(
                "SEFIN_NACIONAL"
            )
            or {
                "ok": True,
            }
        ),
    )

    service.precheck_transmissao_nfse(
        documento=_documento(
            status="PENDENTE_ENVIO"
        ),
        ordem_servico=_ordem(),
        configuracao=_config(),
    )

    assert chamadas == [
        "SEFIN_NACIONAL",
    ]


def test_h4f20_008_rotas_usam_gates_genericos():
    fonte = ROUTES.read_text(
        encoding="utf-8-sig"
    )

    bloco_liberar = fonte[
        fonte.index(
            "def liberar_nfse_parcela_para_envio"
        ):
        fonte.index(
            "def precheck_nfse_parcela_transmissao"
        )
    ]

    bloco_precheck = fonte[
        fonte.index(
            "def precheck_nfse_parcela_transmissao"
        ):
        fonte.index(
            "def transmitir_nfse_parcela_homologacao"
        )
    ]

    assert "liberar_documento_nfse_para_envio" in bloco_liberar
    assert "liberar_documento_nfse_geisweb_para_envio" not in bloco_liberar

    assert "precheck_transmissao_nfse" in bloco_precheck
    assert "precheck_transmissao_geisweb" not in bloco_precheck
    assert "PRE-CHECK NFS-E" in bloco_precheck


def test_h4f20_009_ui_nao_oferece_transmissao_sefin():
    fonte = TEMPLATE.read_text(
        encoding="utf-8"
    )

    assert (
        "documento.provider == 'GEISWEB_TIETE'"
        in fonte
    )
    assert (
        "documento.provider == 'SEFIN_NACIONAL'"
        in fonte
    )
    assert (
        "Transmiss&atilde;o SEFIN Nacional ainda"
        in fonte
    )
    assert (
        "nenhum POST ser&aacute; executado"
        in fonte
    )


def test_h4f20_010_precheck_sefin_nao_tem_fronteira_http():
    fonte = inspect.getsource(
        service.precheck_transmissao_sefin
    )

    proibidos = (
        "requests.",
        "ClienteHttpSefin",
        "executar_consulta_convenio_http",
        "executar_emissao_nfse_http",
        "transmitir_payload_nfse",
        "transmitir_e_aplicar_nfse",
        "db.session",
        ".commit(",
    )

    for termo in proibidos:
        assert termo not in fonte
