from datetime import date
from decimal import Decimal

import pytest

from app import create_app
from app.extensoes import db
from app.cliente.cliente_model import Cliente
from app.configuracao.configuracao_model import Configuracao
from app.fiscal.configuracao_fiscal_model import ConfiguracaoFiscal
from app.fiscal.nfse_service import (
    PreparacaoNfseInvalida,
    preparar_nfse_da_parcela,
    preparar_nfse_parcela_geisweb,
)
from app.fiscal import nfse_service as service
from app.ordem_servico.ordem_servico_model import (
    OrdemServico,
    OrdemServicoParcela,
)


def _cenario():
    app = create_app("testing")

    with app.app_context():
        db.create_all()

        institucional = Configuracao(
            nome_fantasia="JSP",
            razao_social="SAROBA SOLAR LTDA",
            cnpj="66298788000172",
        )
        db.session.add(institucional)
        db.session.flush()

        fiscal = ConfiguracaoFiscal(
            configuracao_id=institucional.id,
            inscricao_municipal="14180",
            regime_tributario="SIMPLES_NACIONAL",
            optante_simples_nacional=True,
            codigo_servico_municipal="1406",
            codigo_lc116="140601",
            aliquota_iss_padrao=Decimal("2.31"),
            municipio_ibge="3554508",
            ambiente="HOMOLOGACAO",
            provider="GEISWEB_TIETE",
            serie_rps="1",
            proximo_rps=1,
            integracao_ativa=False,
            ativo=True,
        )
        db.session.add(fiscal)

        cliente = Cliente(
            nome="MSTI",
            ativo=True,
        )
        db.session.add(cliente)
        db.session.flush()

        ordem = OrdemServico(
            numero="OS-D24F04C",
            titulo="Teste XML parcelado",
            cliente_id=cliente.id,
            tipo_os="comercial",
            status="concluida",
            situacao_fiscal="EMITIR_NFSE",
            ativo=True,
        )
        db.session.add(ordem)
        db.session.flush()

        parcela = OrdemServicoParcela(
            ordem_servico_id=ordem.id,
            numero_parcela=0,
            data_vencimento=date(2026, 9, 22),
            valor=Decimal("1150.00"),
            pago=True,
            ativo=True,
        )
        db.session.add(parcela)
        db.session.commit()

        documento, _ = preparar_nfse_da_parcela(
            ordem.id,
            parcela.id,
        )

        return (
            app,
            ordem.id,
            parcela.id,
            documento.id,
        )


def test_preparacao_geisweb_usa_valor_exato_da_parcela(
    monkeypatch,
):
    (
        app,
        ordem_id,
        parcela_id,
        documento_id,
    ) = _cenario()

    chamadas = {}

    def fake_preparar(**kwargs):
        chamadas.update(kwargs)

        documento = kwargs["documento"]
        documento.status = "PREPARADA"
        documento.serie_rps = "1"
        documento.numero_rps = 1

        return documento, {
            "provider": "GEISWEB_TIETE",
            "conteudo": b"<xml/>",
        }

    monkeypatch.setattr(
        service,
        "preparar_documento_nfse_com_geisweb",
        fake_preparar,
    )

    with app.app_context():

        documento, payload = preparar_nfse_parcela_geisweb(
            documento_id=documento_id,
            ordem_servico_id=ordem_id,
            parcela_id=parcela_id,
            c_class_trib="000001",
            c_class_trib_reg="000001",
            ibs="1.15",
            cbs="10.35",
        )

        assert documento.status == "PREPARADA"

        assert Decimal(
            str(chamadas["base_calculo"])
        ) == Decimal("1150.00")

        assert Decimal(
            str(
                chamadas["valores"][
                    "valor_servicos"
                ]
            )
        ) == Decimal("1150.00")

        assert chamadas["tipo_lancamento"] == "P"
        assert chamadas["regime_geisweb"] == "1"
        assert chamadas["codigo_nacional"] == "140601"

        assert chamadas["ibs_cbs"][
            "c_class_trib"
        ] == "000001"

        assert chamadas["ibs_cbs"][
            "c_class_trib_reg"
        ] == "000001"

        assert Decimal(
            str(
                chamadas["ibs_cbs"]["ibs"]
            )
        ) == Decimal("1.15")

        assert Decimal(
            str(
                chamadas["ibs_cbs"]["cbs"]
            )
        ) == Decimal("10.35")

        assert payload["conteudo"] == b"<xml/>"


def test_preparacao_rejeita_cclasstrib_invalido(
    monkeypatch,
):
    (
        app,
        ordem_id,
        parcela_id,
        documento_id,
    ) = _cenario()

    monkeypatch.setattr(
        service,
        "preparar_documento_nfse_com_geisweb",
        lambda **kwargs: pytest.fail(
            "Nao deveria chegar a preparacao XML."
        ),
    )

    with app.app_context():

        with pytest.raises(
            PreparacaoNfseInvalida,
            match="6 digitos",
        ):
            preparar_nfse_parcela_geisweb(
                documento_id=documento_id,
                ordem_servico_id=ordem_id,
                parcela_id=parcela_id,
                c_class_trib="1",
                c_class_trib_reg="000001",
                ibs="1.15",
                cbs="10.35",
            )
