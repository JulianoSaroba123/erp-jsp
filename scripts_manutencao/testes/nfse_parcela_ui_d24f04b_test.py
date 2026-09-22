from datetime import date
from decimal import Decimal
from types import SimpleNamespace

from flask import g

from app import create_app
from app.extensoes import db
from app.cliente.cliente_model import Cliente
from app.configuracao.configuracao_model import Configuracao
from app.fiscal.configuracao_fiscal_model import (
    ConfiguracaoFiscal,
)
from app.fiscal.nfse_documento_model import (
    NfseDocumento,
)
from app.ordem_servico.ordem_servico_model import (
    OrdemServico,
    OrdemServicoParcela,
)


def _login_admin(app):
    client = app.test_client()

    admin = SimpleNamespace(
        id=1,
        tipo_usuario="admin",
        is_authenticated=True,
    )

    @app.before_request
    def load_test_admin():
        g._login_user = admin

    return client


def _criar_cenario():
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
            numero="OS-PARCELA-UI-001",
            titulo="Teste fiscal por parcela",
            cliente_id=cliente.id,
            tipo_os="comercial",
            status="concluida",
            situacao_fiscal="EMITIR_NFSE",
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


def test_rota_cria_rascunho_sem_reservar_rps():
    (
        app,
        ordem_id,
        parcela_id,
        _,
    ) = _criar_cenario()

    client = _login_admin(app)

    response = client.post(
        (
            f"/ordem_servico/{ordem_id}"
            f"/fiscal/parcela/{parcela_id}/rascunho"
        ),
        follow_redirects=False,
    )

    assert response.status_code in (302, 303)

    with app.app_context():
        documentos = (
            NfseDocumento.query
            .filter_by(
                ordem_servico_id=ordem_id,
                ativo=True,
            )
            .all()
        )

        assert len(documentos) == 1

        documento = documentos[0]

        assert (
            documento.ordem_servico_parcela_id
            == parcela_id
        )

        assert Decimal(
            str(documento.valor_servicos)
        ) == Decimal("1150.00")

        assert documento.status == "RASCUNHO"
        assert documento.numero_rps is None
        assert documento.xml_envio is None
        assert documento.preparado_em is None


def test_duas_parcelas_podem_ter_documentos_independentes():
    (
        app,
        ordem_id,
        parcela_1_id,
        parcela_2_id,
    ) = _criar_cenario()

    client = _login_admin(app)

    response_1 = client.post(
        (
            f"/ordem_servico/{ordem_id}"
            f"/fiscal/parcela/{parcela_1_id}/rascunho"
        )
    )

    response_2 = client.post(
        (
            f"/ordem_servico/{ordem_id}"
            f"/fiscal/parcela/{parcela_2_id}/rascunho"
        )
    )

    assert response_1.status_code in (302, 303)
    assert response_2.status_code in (302, 303)

    with app.app_context():

        documentos = (
            NfseDocumento.query
            .filter_by(
                ordem_servico_id=ordem_id,
                ativo=True,
            )
            .order_by(
                NfseDocumento.id
            )
            .all()
        )

        assert len(documentos) == 2

        assert {
            documento.ordem_servico_parcela_id
            for documento in documentos
        } == {
            parcela_1_id,
            parcela_2_id,
        }

        assert all(
            Decimal(
                str(documento.valor_servicos)
            ) == Decimal("1150.00")
            for documento in documentos
        )

        assert all(
            documento.numero_rps is None
            for documento in documentos
        )

        assert all(
            documento.xml_envio is None
            for documento in documentos
        )
