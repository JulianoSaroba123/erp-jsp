from datetime import date
from decimal import Decimal

import pytest

from app import create_app
from app.extensoes import db
from app.cliente.cliente_model import Cliente
from app.configuracao.configuracao_model import Configuracao
from app.fiscal.configuracao_fiscal_model import ConfiguracaoFiscal
from app.fiscal.nfse_documento_model import NfseDocumento
from app.fiscal.nfse_service import (
    PreparacaoNfseInvalida,
    gerar_chave_emissao_original,
    gerar_chave_emissao_parcela,
    preparar_nfse_da_parcela,
)
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
            numero="OS-PARCELA-001",
            titulo="NFSe parcelada",
            cliente_id=cliente.id,
            tipo_os="comercial",
            status="concluida",
            situacao_fiscal="EMITIR_NFSE",
            condicao_pagamento="parcelado",
            numero_parcelas=2,
            valor_total=Decimal("2300.00"),
            ativo=True,
        )
        db.session.add(ordem)
        db.session.flush()

        parcela_1 = OrdemServicoParcela(
            ordem_servico_id=ordem.id,
            numero_parcela=0,
            data_vencimento=date(2026, 9, 19),
            valor=Decimal("1150.00"),
            pago=True,
            data_pagamento=date(2026, 9, 19),
            ativo=True,
        )

        parcela_2 = OrdemServicoParcela(
            ordem_servico_id=ordem.id,
            numero_parcela=1,
            data_vencimento=date(2026, 11, 1),
            valor=Decimal("1150.00"),
            pago=False,
            ativo=True,
        )

        db.session.add_all([
            parcela_1,
            parcela_2,
        ])
        db.session.commit()

        return (
            app,
            ordem.id,
            parcela_1.id,
            parcela_2.id,
        )


def test_chave_idempotencia_por_parcela():
    assert (
        gerar_chave_emissao_parcela(620, 23)
        == "nfse:os:620:parcela:23:emissao:original"
    )


def test_duas_parcelas_geram_duas_intencoes_independentes():
    app, os_id, p1_id, p2_id = _cenario()

    with app.app_context():
        doc_1, criado_1 = preparar_nfse_da_parcela(
            os_id,
            p1_id,
        )

        doc_1_repetido, criado_repetido = (
            preparar_nfse_da_parcela(
                os_id,
                p1_id,
            )
        )

        doc_2, criado_2 = preparar_nfse_da_parcela(
            os_id,
            p2_id,
        )

        assert criado_1 is True
        assert criado_repetido is False
        assert criado_2 is True

        assert doc_1.id == doc_1_repetido.id
        assert doc_1.id != doc_2.id

        assert doc_1.ordem_servico_parcela_id == p1_id
        assert doc_2.ordem_servico_parcela_id == p2_id

        assert Decimal(str(doc_1.valor_servicos)) == Decimal(
            "1150.00"
        )
        assert Decimal(str(doc_2.valor_servicos)) == Decimal(
            "1150.00"
        )

        assert NfseDocumento.query.filter_by(
            ordem_servico_id=os_id
        ).count() == 2

        assert doc_1.numero_rps is None
        assert doc_2.numero_rps is None
        assert doc_1.xml_envio is None
        assert doc_2.xml_envio is None


def test_adota_rascunho_legado_sem_consumir_rps():
    app, os_id, p1_id, _ = _cenario()

    with app.app_context():
        fiscal = ConfiguracaoFiscal.query.one()

        legado = NfseDocumento(
            ordem_servico_id=os_id,
            configuracao_fiscal_id=fiscal.id,
            status="RASCUNHO",
            ambiente="HOMOLOGACAO",
            provider="GEISWEB_TIETE",
            chave_idempotencia=gerar_chave_emissao_original(
                os_id
            ),
            ativo=True,
        )
        db.session.add(legado)
        db.session.commit()

        legado_id = legado.id

        documento, criado = preparar_nfse_da_parcela(
            os_id,
            p1_id,
        )

        assert criado is False
        assert documento.id == legado_id
        assert documento.ordem_servico_parcela_id == p1_id
        assert Decimal(str(documento.valor_servicos)) == Decimal(
            "1150.00"
        )

        assert documento.chave_idempotencia == (
            gerar_chave_emissao_parcela(
                os_id,
                p1_id,
            )
        )

        assert documento.numero_rps is None
        assert documento.xml_envio is None
        assert documento.preparado_em is None

        assert NfseDocumento.query.filter_by(
            ordem_servico_id=os_id
        ).count() == 1


def test_nao_aceita_parcela_de_outra_os():
    app, os_id, _, _ = _cenario()

    with app.app_context():
        cliente = Cliente(
            nome="Outro cliente",
            ativo=True,
        )
        db.session.add(cliente)
        db.session.flush()

        outra_os = OrdemServico(
            numero="OS-PARCELA-002",
            titulo="Outra OS",
            cliente_id=cliente.id,
            tipo_os="comercial",
            status="concluida",
            situacao_fiscal="EMITIR_NFSE",
            ativo=True,
        )
        db.session.add(outra_os)
        db.session.flush()

        outra_parcela = OrdemServicoParcela(
            ordem_servico_id=outra_os.id,
            numero_parcela=1,
            data_vencimento=date(2026, 10, 1),
            valor=Decimal("500.00"),
            pago=False,
            ativo=True,
        )
        db.session.add(outra_parcela)
        db.session.commit()

        with pytest.raises(
            PreparacaoNfseInvalida,
            match="nao pertence",
        ):
            preparar_nfse_da_parcela(
                os_id,
                outra_parcela.id,
            )
