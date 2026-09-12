# -*- coding: utf-8 -*-
"""Regressao dos parsers CSV/OFX da importacao bancaria Cora."""

import os
import sys
from decimal import Decimal

sys.path.insert(
    0,
    os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")),
)

from app.financeiro.extrato_importacao_service import (
    gerar_fingerprints,
    parse_csv,
    parse_ofx,
    resumir_movimentos,
)


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

CSV_LEGADO = """data,descricao,documento,valor,tipo
01/09/2026,Pagamento fornecedor,DOC001,"1.234,56",debito
02/09/2026,Recebimento cliente,DOC002,"2.000,00",credito
""".encode("utf-8")


def test_csv_cora_parseia_e_preserva_duplicata_legitima():
    resultado = parse_csv(CSV_CORA)
    gerar_fingerprints(resultado.movimentos, conta_chave="conta-cora-teste")
    resumo = resumir_movimentos(resultado.movimentos)

    assert resultado.formato == "cora_csv"
    assert resultado.erros == []
    assert resumo["movimentos"] == 4
    assert resumo["creditos"] == 1
    assert resumo["debitos"] == 3
    assert resumo["total_creditos"] == Decimal("800.00")
    assert resumo["total_debitos"] == Decimal("140.80")
    assert len({m["fingerprint"] for m in resultado.movimentos}) == 4


def test_ofx_e_csv_geram_o_mesmo_conjunto_de_fingerprints():
    csv_resultado = parse_csv(CSV_CORA)
    ofx_resultado = parse_ofx(OFX_CORA)

    gerar_fingerprints(csv_resultado.movimentos, conta_chave="conta-cora-teste")
    gerar_fingerprints(ofx_resultado.movimentos, conta_chave="conta-cora-teste")

    fingerprints_csv = {m["fingerprint"] for m in csv_resultado.movimentos}
    fingerprints_ofx = {m["fingerprint"] for m in ofx_resultado.movimentos}

    assert ofx_resultado.formato == "cora_ofx"
    assert ofx_resultado.erros == []
    assert fingerprints_csv == fingerprints_ofx
    assert len(fingerprints_ofx) == 4
    assert all(m["identificador_externo"] for m in ofx_resultado.movimentos)


def test_csv_legado_continua_compativel():
    resultado = parse_csv(CSV_LEGADO)
    resumo = resumir_movimentos(resultado.movimentos)

    assert resultado.formato == "csv_legado"
    assert resultado.erros == []
    assert resumo["movimentos"] == 2
    assert resumo["total_creditos"] == Decimal("2000.00")
    assert resumo["total_debitos"] == Decimal("1234.56")
    assert resumo["liquido"] == Decimal("765.44")


def test_csv_invalido_retorna_erro_sem_sumir_com_a_linha():
    conteudo = """Data,Transação,Tipo Transação,Identificação,Valor
11/09/2026,Compra no débito,DÉBITO,TESTE,-10
DATA-RUIM,Compra no débito,DÉBITO,TESTE,-20
""".encode("utf-8")

    resultado = parse_csv(conteudo)

    assert len(resultado.movimentos) == 1
    assert len(resultado.erros) == 1
    assert resultado.erros[0]["linha"] == 3
    assert "data" in resultado.erros[0]["erro"].lower()


if __name__ == "__main__":
    test_csv_cora_parseia_e_preserva_duplicata_legitima()
    test_ofx_e_csv_geram_o_mesmo_conjunto_de_fingerprints()
    test_csv_legado_continua_compativel()
    test_csv_invalido_retorna_erro_sem_sumir_com_a_linha()
    print("IMPORTACAO CORA PARSERS: OK")
