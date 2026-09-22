import hashlib
import inspect
from types import SimpleNamespace

import pytest

from app.fiscal import nfse_service as service


XML_PERSISTIDO = b"<EnviarLoteRpsEnvio>artefato-persistido</EnviarLoteRpsEnvio>"


def _documento(
    *,
    status="PREPARADA",
    provider="GEISWEB_TIETE",
    ambiente="HOMOLOGACAO",
    xml_envio=XML_PERSISTIDO,
    xml_envio_sha256=None,
):
    if xml_envio_sha256 is None:
        xml_envio_sha256 = hashlib.sha256(xml_envio).hexdigest()

    return SimpleNamespace(
        id=123,
        status=status,
        mensagem_status=None,
        provider=provider,
        ambiente=ambiente,
        xml_envio=xml_envio,
        xml_envio_sha256=xml_envio_sha256,
        numero_rps=77,
        serie_rps="TESTE",
    )


def _configuracao(
    *,
    provider="GEISWEB_TIETE",
    ambiente="HOMOLOGACAO",
):
    return SimpleNamespace(
        provider=provider,
        ambiente=ambiente,
        integracao_ativa=False,
        proximo_rps=88,
    )


def _ordem_servico():
    return SimpleNamespace(
        id=456,
    )


class ProviderFake:
    def __init__(self):
        self.preparar_payload_calls = 0

    def preparar_payload(
        self,
        *,
        documento,
        ordem_servico,
        configuracao,
    ):
        self.preparar_payload_calls += 1

        return {
            "provider": "GEISWEB_TIETE",
            "ambiente": configuracao.ambiente,
            # Este conteudo deve ser substituido pelo XML persistido.
            "conteudo": b"CONTEUDO_NAO_PERSISTIDO",
        }

    def transmitir(self, *args, **kwargs):
        raise AssertionError(
            "H3-S5P nao pode chamar provider.transmitir()."
        )


def test_h3_s5p_libera_xml_persistido_sem_transmitir(
    monkeypatch,
):
    documento = _documento()
    configuracao = _configuracao()
    ordem_servico = _ordem_servico()

    provider = ProviderFake()
    xmls_validados = []

    def validar_xml(xml):
        xmls_validados.append(bytes(xml))

        return SimpleNamespace(
            valido=True,
            erros=[],
        )

    monkeypatch.setattr(
        service,
        "validar_xml_envio_lote_rps",
        validar_xml,
    )

    monkeypatch.setattr(
        service,
        "resolver_provider_nfse",
        lambda configuracao_recebida: provider,
    )

    xml_antes = documento.xml_envio
    hash_antes = documento.xml_envio_sha256
    numero_rps_antes = documento.numero_rps
    proximo_rps_antes = configuracao.proximo_rps

    retorno = service.liberar_documento_nfse_geisweb_para_envio(
        documento=documento,
        ordem_servico=ordem_servico,
        configuracao=configuracao,
    )

    assert retorno is documento

    assert documento.status == "PENDENTE_ENVIO"
    assert (
        "Nenhuma NFS-e foi transmitida"
        in documento.mensagem_status
    )

    # O mesmo artefato persistido atravessa reconstru??o e gate.
    assert documento.xml_envio == xml_antes
    assert documento.xml_envio_sha256 == hash_antes

    assert xmls_validados == [
        XML_PERSISTIDO,
        XML_PERSISTIDO,
    ]

    # Apenas metadados de transporte s?o reconstru?dos.
    assert provider.preparar_payload_calls == 1

    # Nenhuma nova reserva de RPS.
    assert documento.numero_rps == numero_rps_antes
    assert configuracao.proximo_rps == proximo_rps_antes

    # Integra??o continua bloqueada.
    assert configuracao.integracao_ativa is False


def test_h3_s5p_hash_invalido_nao_ultrapassa_gate(
    monkeypatch,
):
    documento = _documento(
        xml_envio_sha256="0" * 64,
    )

    configuracao = _configuracao()
    ordem_servico = _ordem_servico()

    def nao_deveria_validar_xsd(*args, **kwargs):
        raise AssertionError(
            "XSD nao deveria ser consultado apos falha de hash."
        )

    def nao_deveria_resolver_provider(*args, **kwargs):
        raise AssertionError(
            "Provider nao deveria ser resolvido apos falha de hash."
        )

    monkeypatch.setattr(
        service,
        "validar_xml_envio_lote_rps",
        nao_deveria_validar_xsd,
    )

    monkeypatch.setattr(
        service,
        "resolver_provider_nfse",
        nao_deveria_resolver_provider,
    )

    with pytest.raises(
        service.TransmissaoNfseInvalida,
        match="Integridade do XML fiscal persistido",
    ):
        service.liberar_documento_nfse_geisweb_para_envio(
            documento=documento,
            ordem_servico=ordem_servico,
            configuracao=configuracao,
        )

    assert documento.status == "PREPARADA"


def test_h3_s5p_xsd_invalido_nao_ultrapassa_gate(
    monkeypatch,
):
    documento = _documento()
    configuracao = _configuracao()
    ordem_servico = _ordem_servico()

    monkeypatch.setattr(
        service,
        "validar_xml_envio_lote_rps",
        lambda xml: SimpleNamespace(
            valido=False,
            erros=["XML rejeitado pelo XSD de teste"],
        ),
    )

    def nao_deveria_resolver_provider(*args, **kwargs):
        raise AssertionError(
            "Provider nao deveria ser resolvido com XSD invalido."
        )

    monkeypatch.setattr(
        service,
        "resolver_provider_nfse",
        nao_deveria_resolver_provider,
    )

    with pytest.raises(
        service.TransmissaoNfseInvalida,
        match="nao e mais valido",
    ):
        service.liberar_documento_nfse_geisweb_para_envio(
            documento=documento,
            ordem_servico=ordem_servico,
            configuracao=configuracao,
        )

    assert documento.status == "PREPARADA"


@pytest.mark.parametrize(
    (
        "provider_documento",
        "provider_configuracao",
        "ambiente_documento",
        "ambiente_configuracao",
    ),
    [
        (
            "SEFIN_NACIONAL",
            "GEISWEB_TIETE",
            "HOMOLOGACAO",
            "HOMOLOGACAO",
        ),
        (
            "GEISWEB_TIETE",
            "SEFIN_NACIONAL",
            "HOMOLOGACAO",
            "HOMOLOGACAO",
        ),
        (
            "GEISWEB_TIETE",
            "GEISWEB_TIETE",
            "PRODUCAO",
            "HOMOLOGACAO",
        ),
    ],
)
def test_h3_s5p_divergencia_fiscal_mantem_preparada(
    monkeypatch,
    provider_documento,
    provider_configuracao,
    ambiente_documento,
    ambiente_configuracao,
):
    documento = _documento(
        provider=provider_documento,
        ambiente=ambiente_documento,
    )

    configuracao = _configuracao(
        provider=provider_configuracao,
        ambiente=ambiente_configuracao,
    )

    ordem_servico = _ordem_servico()

    def nao_deveria_resolver_provider(*args, **kwargs):
        raise AssertionError(
            "Provider tecnico nao deveria ser resolvido "
            "apos divergencia fiscal."
        )

    monkeypatch.setattr(
        service,
        "resolver_provider_nfse",
        nao_deveria_resolver_provider,
    )

    with pytest.raises(
        (
            service.TransmissaoNfseInvalida,
            service.TransicaoStatusNfseInvalida,
        )
    ):
        service.liberar_documento_nfse_geisweb_para_envio(
            documento=documento,
            ordem_servico=ordem_servico,
            configuracao=configuracao,
        )

    assert documento.status == "PREPARADA"


def test_h3_s5p_orquestrador_nao_possui_io_de_transmissao_ou_commit():
    fonte = inspect.getsource(
        service.liberar_documento_nfse_geisweb_para_envio
    )

    assert "reconstruir_payload_geisweb_para_envio(" in fonte
    assert "preparar_nfse_para_envio(" in fonte

    assert "db.session" not in fonte
    assert ".commit(" not in fonte
    assert ".flush(" not in fonte
    assert ".transmitir(" not in fonte

    assert "preparar_documento_nfse_com_geisweb(" not in fonte
    assert "reservar" not in fonte.lower()
