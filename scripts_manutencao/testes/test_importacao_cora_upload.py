# -*- coding: utf-8 -*-
"""Regressão da rota de importação bancária Cora (OFX/CSV)."""

import io
import os
import sys
from decimal import Decimal
from types import SimpleNamespace

sys.path.insert(
    0,
    os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")),
)

os.environ["FLASK_CONFIG"] = "testing"
os.environ["FLASK_ENV"] = "testing"

from flask import g

from app.app import create_app
from app.extensoes import db
from app.financeiro.financeiro_model import ContaBancaria, ExtratoBancario


CSV_CORA = """Data,Transação,Tipo Transação,Identificação,Valor
11/09/2026,Transf Pix recebida,CRÉDITO,CLIENTE TESTE,800
11/09/2026,Compra no débito,DÉBITO,SPVIAS                   ,-20.4
11/09/2026,Compra no débito,DÉBITO,SPVIAS                   ,-20.4
10/09/2026,Pgto QR Code Pix,DÉBITO,FORNECEDOR TESTE,-100
""".encode("utf-8")

OFX_CORA = b"""OFXHEADER:100
DATA:OFXSGML
VERSION:102
ENCODING:UTF-8
<OFX>
<BANKTRANLIST>
<STMTTRN>
<TRNTYPE>CREDIT</TRNTYPE>
<DTPOSTED>20260911000000[0:GMT]</DTPOSTED>
<TRNAMT>800.00</TRNAMT>
<FITID>fitid-001</FITID>
<MEMO>Transf Pix recebida - CLIENTE TESTE - 00.000.000/0001-00</MEMO>
</STMTTRN>
<STMTTRN>
<TRNTYPE>DEBIT</TRNTYPE>
<DTPOSTED>20260911000000[0:GMT]</DTPOSTED>
<TRNAMT>-20.40</TRNAMT>
<FITID>fitid-002</FITID>
<MEMO>Compra no d\xc3\xa9bito - SPVIAS                    - </MEMO>
</STMTTRN>
<STMTTRN>
<TRNTYPE>DEBIT</TRNTYPE>
<DTPOSTED>20260911000000[0:GMT]</DTPOSTED>
<TRNAMT>-20.40</TRNAMT>
<FITID>fitid-003</FITID>
<MEMO>Compra no d\xc3\xa9bito - SPVIAS                    - </MEMO>
</STMTTRN>
<STMTTRN>
<TRNTYPE>DEBIT</TRNTYPE>
<DTPOSTED>20260910000000[0:GMT]</DTPOSTED>
<TRNAMT>-100.00</TRNAMT>
<FITID>fitid-004</FITID>
<MEMO>Pgto QR Code Pix - FORNECEDOR TESTE - 11.111.111/0001-11</MEMO>
</STMTTRN>
</BANKTRANLIST>
</OFX>
"""


def _login_admin(app):
    client = app.test_client()
    admin = SimpleNamespace(
        id=1,
        tipo_usuario="admin",
        is_authenticated=True,
        tem_permissao=lambda *args, **kwargs: True,
    )

    @app.before_request
    def load_test_admin():
        g._login_user = admin

    return client


def _nova_conta(nome):
    conta = ContaBancaria(
        nome=nome,
        tipo="conta_corrente",
        saldo_inicial=Decimal("0.00"),
        saldo_atual=Decimal("0.00"),
        limite_credito=Decimal("0.00"),
        ativa=True,
        principal=False,
        ativo=True,
    )
    db.session.add(conta)
    db.session.commit()
    return conta.id


def _post_extrato(client, conta_id, nome, conteudo):
    return client.post(
        "/financeiro/conciliacao-bancaria/upload",
        data={
            "conta_bancaria_id": str(conta_id),
            "arquivo": (io.BytesIO(conteudo), nome),
        },
        content_type="multipart/form-data",
        follow_redirects=False,
    )


def _flashes(client):
    with client.session_transaction() as sess:
        mensagens = [mensagem for _, mensagem in sess.get("_flashes", [])]
        sess["_flashes"] = []
    return " | ".join(mensagens)


def _qtd_conta(conta_id):
    return ExtratoBancario.query.filter_by(conta_bancaria_id=conta_id).count()


def test_upload_idempotente_nos_dois_sentidos():
    app = create_app("testing")

    with app.app_context():
        db.drop_all()
        db.create_all()
        conta_ofx = _nova_conta("Cora OFX Primeiro")
        conta_csv = _nova_conta("Cora CSV Primeiro")

    client = _login_admin(app)

    response = _post_extrato(client, conta_ofx, "cora.ofx", OFX_CORA)
    assert response.status_code == 302
    mensagens = _flashes(client)
    assert "Importados: 4" in mensagens
    assert "Já existentes/ignorados: 0" in mensagens
    assert "Erros: 0" in mensagens

    with app.app_context():
        assert _qtd_conta(conta_ofx) == 4

    response = _post_extrato(client, conta_ofx, "cora.ofx", OFX_CORA)
    assert response.status_code == 302
    mensagens = _flashes(client)
    assert "Importados: 0" in mensagens
    assert "Já existentes/ignorados: 4" in mensagens
    assert "Erros: 0" in mensagens

    with app.app_context():
        assert _qtd_conta(conta_ofx) == 4

    response = _post_extrato(client, conta_ofx, "cora.csv", CSV_CORA)
    assert response.status_code == 302
    mensagens = _flashes(client)
    assert "Importados: 0" in mensagens
    assert "Já existentes/ignorados: 4" in mensagens

    with app.app_context():
        assert _qtd_conta(conta_ofx) == 4

    response = _post_extrato(client, conta_csv, "cora.csv", CSV_CORA)
    assert response.status_code == 302
    mensagens = _flashes(client)
    assert "Importados: 4" in mensagens
    assert "Erros: 0" in mensagens

    with app.app_context():
        assert _qtd_conta(conta_csv) == 4

    response = _post_extrato(client, conta_csv, "cora.ofx", OFX_CORA)
    assert response.status_code == 302
    mensagens = _flashes(client)
    assert "Importados: 0" in mensagens
    assert "Já existentes/ignorados: 4" in mensagens

    with app.app_context():
        assert _qtd_conta(conta_csv) == 4


if __name__ == "__main__":
    test_upload_idempotente_nos_dois_sentidos()
    print("IMPORTACAO CORA UPLOAD: OK")
