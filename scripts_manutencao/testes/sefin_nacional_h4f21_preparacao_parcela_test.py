"""H4-F21 - preparação local da DPS Nacional por parcela."""

from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
import hashlib
import inspect
from pathlib import Path

from cryptography import x509
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID
import pytest

from app import create_app
from app.extensoes import db
from app.cliente.cliente_model import Cliente
from app.configuracao.configuracao_model import Configuracao
from app.fiscal.configuracao_fiscal_model import ConfiguracaoFiscal
from app.fiscal.nfse_documento_model import NfseDocumento
from app.fiscal.certificado_a1 import MaterialCertificadoA1
from app.fiscal import dps_erp_adapter as adapter
from app.fiscal import nfse_service as service
from app.fiscal.providers import sefin_nacional_dps as dps_model
from app.ordem_servico.ordem_servico_model import (
    OrdemServico,
    OrdemServicoItem,
    OrdemServicoParcela,
)


TEMPLATE = Path(
    "app/ordem_servico/templates/os/_painel_fiscal_parcelas.html"
)
ROUTES = Path(
    "app/ordem_servico/ordem_servico_routes.py"
)
CONFIG_ROUTES = Path(
    "app/configuracao/configuracao_routes.py"
)
CONFIG_TEMPLATE = Path(
    "app/configuracao/templates/configuracao/form_configuracao_fiscal.html"
)


def _material():
    chave = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
    )

    agora = datetime.now(
        timezone.utc
    )

    nome = x509.Name(
        [
            x509.NameAttribute(
                NameOID.COUNTRY_NAME,
                "BR",
            ),
            x509.NameAttribute(
                NameOID.ORGANIZATION_NAME,
                "ERP JSP H4-F21 TESTE",
            ),
            x509.NameAttribute(
                NameOID.COMMON_NAME,
                "H4-F21",
            ),
        ]
    )

    certificado = (
        x509.CertificateBuilder()
        .subject_name(
            nome
        )
        .issuer_name(
            nome
        )
        .public_key(
            chave.public_key()
        )
        .serial_number(
            x509.random_serial_number()
        )
        .not_valid_before(
            (
                agora
                - timedelta(
                    days=1
                )
            ).replace(
                tzinfo=None
            )
        )
        .not_valid_after(
            (
                agora
                + timedelta(
                    days=30
                )
            ).replace(
                tzinfo=None
            )
        )
        .sign(
            chave,
            hashes.SHA256(),
        )
    )

    return MaterialCertificadoA1(
        chave_privada=chave,
        certificado=certificado,
        cadeia=(),
        caminho=Path(
            "h4-f21-teste.pfx"
        ),
    )


def test_h4f21_001_tpemit_1_omite_im_do_prestador():
    configuracao = type(
        "Config",
        (),
        {
            "id": 1,
            "cnpj": "66298788000172",
            "razao_social": "SAROBA SOLAR LTDA",
        },
    )()

    fiscal = type(
        "Fiscal",
        (),
        {
            "configuracao_id": 1,
            "inscricao_municipal": "14180",
            "municipio_ibge": "3554508",
            "op_simp_nac": "3",
            "reg_ap_trib_sn": "1",
            "reg_esp_trib": "0",
        },
    )()

    prestador = dps_model.montar_prestador_canonico(
        configuracao,
        fiscal,
        tipo_emitente="1",
    )

    assert prestador[
        "inscricao_municipal"
    ] is None


def test_h4f21_002_aliquota_none_nao_cai_no_padrao():
    fiscal = type(
        "Fiscal",
        (),
        {
            "aliquota_iss_padrao": Decimal(
                "2.31"
            ),
        },
    )()

    iss = dps_model.montar_iss_canonico(
        iss={
            "tributacao_issqn": "1",
            "tipo_retencao": "1",
            "aliquota": None,
        },
        configuracao_fiscal=fiscal,
    )

    assert iss[
        "aliquota"
    ] is None


def test_h4f21_003_adapter_usa_classificacao_e_valor_explicitos():
    ordem = type(
        "Ordem",
        (),
        {
            "descricao": "Servico controlado",
            "titulo": "Servico",
            "valor_total_servicos": Decimal(
                "1000.00"
            ),
            "valor_desconto": Decimal(
                "0.00"
            ),
        },
    )()

    fiscal = type(
        "Fiscal",
        (),
        {
            "codigo_lc116": "140601",
            "codigo_servico_municipal": "1406",
        },
    )()

    servico = adapter.montar_servico_da_os(
        ordem,
        fiscal,
        municipio_incidencia_ibge="3554508",
        municipio_prestacao_ibge="3541653",
        codigo_tributacao_nacional="140101",
        codigo_nbs="101061900",
        codigo_tributacao_municipal="",
    )

    valores = adapter.montar_valores_da_os(
        ordem,
        valor_servicos_fiscal=Decimal(
            "250.00"
        ),
    )

    assert servico[
        "codigo_lista_nacional"
    ] == "140101"
    assert servico[
        "codigo_tributacao_municipal"
    ] is None
    assert servico[
        "nbs"
    ] == "101061900"
    assert valores[
        "valor_servicos"
    ] == Decimal(
        "250.00"
    )


def _cenario():
    app = create_app(
        "testing"
    )

    with app.app_context():
        db.create_all()

        institucional = Configuracao(
            nome_fantasia="JSP",
            razao_social="SAROBA SOLAR LTDA",
            cnpj="66.298.788/0001-72",
        )
        db.session.add(
            institucional
        )
        db.session.flush()

        fiscal = ConfiguracaoFiscal(
            configuracao_id=institucional.id,
            inscricao_municipal="14180",
            regime_tributario="SIMPLES_NACIONAL",
            optante_simples_nacional=True,
            codigo_servico_municipal="1406",
            codigo_lc116="140601",
            aliquota_iss_padrao=Decimal(
                "2.31"
            ),
            municipio_ibge="3554508",
            op_simp_nac="3",
            reg_ap_trib_sn="1",
            reg_esp_trib="0",
            ambiente="HOMOLOGACAO",
            provider="SEFIN_NACIONAL",
            serie_rps="9999",
            proximo_rps=1,
            integracao_ativa=False,
            ativo=True,
        )
        db.session.add(
            fiscal
        )

        cliente = Cliente(
            nome="CLIENTE TESTE",
            nome_fantasia="CLIENTE TESTE",
            razao_social="CLIENTE TESTE LTDA",
            tipo="PJ",
            cpf_cnpj="12345678000190",
            email="fiscal@cliente.test",
            cep="18530000",
            endereco="Rua Teste",
            numero="100",
            bairro="Centro",
            cidade="Quadra",
            estado="SP",
            pais="Brasil",
            ativo=True,
        )
        db.session.add(
            cliente
        )
        db.session.flush()

        ordem = OrdemServico(
            numero="OS-H4-F21-001",
            titulo="Atendimento emergencial em grupo gerador",
            descricao="Atendimento emergencial para manutencao de grupo gerador",
            cliente_id=cliente.id,
            tipo_os="comercial",
            status="concluida",
            situacao_fiscal="EMITIR_NFSE",
            data_conclusao=datetime(
                2026,
                11,
                11,
                12,
                0,
            ),
            valor_desconto=Decimal(
                "0.00"
            ),
            ativo=True,
        )
        db.session.add(
            ordem
        )
        db.session.flush()

        item = OrdemServicoItem(
            ordem_servico_id=ordem.id,
            descricao="Servico total da OS",
            tipo_servico="fechado",
            quantidade=Decimal(
                "1.00"
            ),
            valor_unitario=Decimal(
                "1000.00"
            ),
            valor_total=Decimal(
                "1000.00"
            ),
            ativo=True,
        )

        parcela = OrdemServicoParcela(
            ordem_servico_id=ordem.id,
            numero_parcela=1,
            data_vencimento=date(
                2026,
                11,
                20,
            ),
            valor=Decimal(
                "250.00"
            ),
            pago=False,
            ativo=True,
        )

        db.session.add_all(
            [
                item,
                parcela,
            ]
        )
        db.session.flush()

        documento = NfseDocumento(
            ordem_servico_id=ordem.id,
            ordem_servico_parcela_id=parcela.id,
            configuracao_fiscal_id=fiscal.id,
            status="RASCUNHO",
            ambiente="HOMOLOGACAO",
            provider="SEFIN_NACIONAL",
            chave_idempotencia=(
                "nfse:h4f21:parcela:1"
            ),
            valor_servicos=Decimal(
                "250.00"
            ),
            ativo=True,
        )
        db.session.add(
            documento
        )
        db.session.commit()

        return (
            app,
            documento.id,
            ordem.id,
            parcela.id,
        )


def test_h4f21_004_prepara_dps_real_local_por_parcela(
    monkeypatch,
):
    (
        app,
        documento_id,
        ordem_id,
        parcela_id,
    ) = _cenario()

    material = _material()

    monkeypatch.setattr(
        service,
        "carregar_certificado_a1_do_ambiente",
        lambda: material,
    )

    with app.app_context():
        documento, payload = service.preparar_nfse_parcela_sefin(
            documento_id=documento_id,
            ordem_servico_id=ordem_id,
            parcela_id=parcela_id,
            codigo_tributacao_nacional="140101",
            codigo_nbs="101061900",
            codigo_tributacao_municipal="",
            municipio_incidencia_ibge="3554508",
            municipio_prestacao_ibge="3541653",
            percentual_tot_trib_sn="2.31",
            tributacao_issqn="1",
            tipo_retencao_issqn="1",
        )

        xml = bytes(
            payload[
                "conteudo"
            ]
        )

        assert documento.status == "PREPARADA"
        assert documento.numero_rps == 1
        assert documento.serie_rps == "9999"
        assert documento.xml_envio == xml
        assert documento.xml_envio_sha256 == hashlib.sha256(
            xml
        ).hexdigest()

        assert b"<cTribNac>140101</cTribNac>" in xml
        assert b"<cNBS>101061900</cNBS>" in xml
        assert b"<cLocPrestacao>3541653</cLocPrestacao>" in xml
        assert b"<pTotTribSN>2.31</pTotTribSN>" in xml
        assert b"<vServPrest>" in xml
        assert b"<vServ>250.00</vServ>" in xml

        assert b"<IM>" not in xml
        assert b"<pAliq>" not in xml
        assert b"<cTribMun>" not in xml


def test_h4f21_005_rota_despacha_por_provider():
    fonte = ROUTES.read_text(
        encoding="utf-8-sig"
    )

    inicio = fonte.index(
        "def preparar_nfse_parcela_xml"
    )
    fim = fonte.index(
        "def liberar_nfse_parcela_para_envio",
        inicio,
    )
    bloco = fonte[
        inicio:fim
    ]

    assert "provider == 'GEISWEB_TIETE'" in bloco
    assert "provider == 'SEFIN_NACIONAL'" in bloco
    assert "preparar_nfse_parcela_geisweb(" in bloco
    assert "preparar_nfse_parcela_sefin(" in bloco
    assert "codigo_tributacao_nacional" in bloco
    assert "municipio_prestacao_ibge" in bloco
    assert "percentual_tot_trib_sn" in bloco


def test_h4f21_006_ui_expoe_formulario_nacional_controlado():
    fonte = TEMPLATE.read_text(
        encoding="utf-8"
    )

    assert "Preparar DPS Nacional" in fonte
    assert 'name="codigo_tributacao_nacional"' in fonte
    assert 'value="140101"' in fonte
    assert 'name="codigo_nbs"' in fonte
    assert 'value="101061900"' in fonte
    assert 'name="municipio_prestacao_ibge"' in fonte
    assert 'name="percentual_tot_trib_sn"' in fonte
    assert 'value="2.31"' in fonte
    assert "Nenhuma NFS-e ser&aacute; transmitida" in fonte


def test_h4f21_007_configuracao_expoe_e_persiste_regime_nacional():
    rota = CONFIG_ROUTES.read_text(
        encoding="utf-8-sig"
    )
    template = CONFIG_TEMPLATE.read_text(
        encoding="utf-8"
    )

    for campo in (
        "op_simp_nac",
        "reg_ap_trib_sn",
        "reg_esp_trib",
    ):
        assert (
            f"config_fiscal.{campo}"
            in rota
        )
        assert (
            f'name="{campo}"'
            in template
        )


def test_h4f21_008_helper_nao_tem_fronteira_de_rede():
    fonte = inspect.getsource(
        service.preparar_nfse_parcela_sefin
    )

    proibidos = (
        "requests.",
        "executar_consulta_convenio_http",
        "executar_emissao_nfse_http",
        "transmitir_payload_nfse",
        "transmitir_e_aplicar_nfse",
        'method="POST"',
        ".post(",
    )

    for termo in proibidos:
        assert termo not in fonte
