from __future__ import annotations

import pytest

from app.fiscal.providers.geisweb_tiete_resultado import (
    GeisWebResultadoError,
    interpretar_resultado_envio_geisweb,
)


def test_f2g1_interpreta_sucesso_com_numero_nfse():
    xml = """
    <EnviaLoteRpsResposta>
      <NumeroLote>123</NumeroLote>
      <Nfse>
        <IdentificacaoNfse>
          <NumeroNfse>4567</NumeroNfse>
          <CodigoVerificacao>ABC123</CodigoVerificacao>
        </IdentificacaoNfse>
      </Nfse>
    </EnviaLoteRpsResposta>
    """

    resultado = interpretar_resultado_envio_geisweb(xml)

    assert resultado.status == "ACEITA"
    assert resultado.numero_lote == "123"
    assert resultado.numero_nfse == "4567"
    assert resultado.codigo_verificacao == "ABC123"
    assert resultado.chave_nacional is None


def test_f2g1_interpreta_campos_geisweb_101():
    xml = """
    <EnviaLoteRpsResposta>
      <NumeroLote>10</NumeroLote>
      <Nfse>
        <IdentificacaoNfse>
          <NumeroRps>99</NumeroRps>
          <NumeroNfse>5001</NumeroNfse>
          <CodigoVerificacao>XYZ999</CodigoVerificacao>
          <ChaveNotaNacional>CHAVE-NACIONAL-001</ChaveNotaNacional>
        </IdentificacaoNfse>
      </Nfse>
    </EnviaLoteRpsResposta>
    """

    resultado = interpretar_resultado_envio_geisweb(xml)

    assert resultado.status == "ACEITA"
    assert resultado.numero_nfse == "5001"
    assert resultado.chave_nacional == "CHAVE-NACIONAL-001"

    assert resultado.nfse[0].numero_rps == "99"


def test_f2g1_interpreta_rejeicao_msg():
    xml = """
    <EnviaLoteRpsResposta>
      <Msg>
        <Erro>100</Erro>
        <Status>Inscricao municipal invalida.</Status>
      </Msg>
    </EnviaLoteRpsResposta>
    """

    resultado = interpretar_resultado_envio_geisweb(xml)

    assert resultado.status == "REJEITADA"
    assert resultado.numero_nfse is None
    assert resultado.mensagens[0].erro == 100
    assert (
        resultado.mensagens[0].status
        == "Inscricao municipal invalida."
    )


def test_f2g1_preserva_multiplas_mensagens():
    xml = """
    <EnviaLoteRpsResposta>
      <Msg>
        <Erro>10</Erro>
        <Status>Erro A</Status>
      </Msg>
      <Msg>
        <Erro>20</Erro>
        <Status>Erro B</Status>
      </Msg>
    </EnviaLoteRpsResposta>
    """

    resultado = interpretar_resultado_envio_geisweb(xml)

    assert resultado.status == "REJEITADA"
    assert resultado.mensagem == "Erro A; Erro B"
    assert len(resultado.mensagens) == 2


def test_f2g1_preserva_multiplas_nfse():
    xml = """
    <EnviaLoteRpsResposta>
      <NumeroLote>777</NumeroLote>
      <Nfse>
        <IdentificacaoNfse>
          <NumeroNfse>1001</NumeroNfse>
          <CodigoVerificacao>A1</CodigoVerificacao>
        </IdentificacaoNfse>
      </Nfse>
      <Nfse>
        <IdentificacaoNfse>
          <NumeroNfse>1002</NumeroNfse>
          <CodigoVerificacao>A2</CodigoVerificacao>
        </IdentificacaoNfse>
      </Nfse>
    </EnviaLoteRpsResposta>
    """

    resultado = interpretar_resultado_envio_geisweb(xml)

    assert resultado.status == "ACEITA"
    assert resultado.numero_nfse == "1001"
    assert len(resultado.nfse) == 2
    assert resultado.nfse[1].numero_nfse == "1002"


def test_f2g1_retorno_sem_nfse_e_sem_msg_vira_erro():
    xml = """
    <EnviaLoteRpsResposta>
      <NumeroLote>88</NumeroLote>
    </EnviaLoteRpsResposta>
    """

    resultado = interpretar_resultado_envio_geisweb(xml)

    assert resultado.status == "ERRO"
    assert resultado.numero_nfse is None


def test_f2g1_rejeita_xml_invalido():
    with pytest.raises(
        GeisWebResultadoError,
        match="XML invalido",
    ):
        interpretar_resultado_envio_geisweb(
            "<EnviaLoteRpsResposta>"
        )
