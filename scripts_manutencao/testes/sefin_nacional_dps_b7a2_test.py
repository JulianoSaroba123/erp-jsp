from datetime import datetime
from decimal import Decimal
from types import SimpleNamespace

import pytest

from app.fiscal import dps_erp_adapter as adapter


def _cliente():
    return SimpleNamespace(
        tipo="PJ",
        cpf_cnpj="12.345.678/0001-90",
        nome="Cliente Teste",
        nome_fantasia="Cliente Teste",
        razao_social="Cliente Teste LTDA",
        email="fiscal@cliente.test",
        email_financeiro=None,
        cep="18530-000",
        endereco="Rua Teste",
        numero="100",
        complemento=None,
        bairro="Centro",
        cidade="Tiete",
        estado="SP",
        pais="Brasil",
    )


def _ordem(**alteracoes):
    dados = {
        "cliente": _cliente(),
        "titulo": "Manutencao eletrica",
        "descricao": "Manutencao eletrica industrial",
        "data_conclusao": datetime(2026, 9, 18, 10, 30),
        "valor_total_servicos": Decimal("450.00"),
        "valor_total_produtos": Decimal("999.00"),
        "valor_desconto": Decimal("0.00"),
    }
    dados.update(alteracoes)
    return SimpleNamespace(**dados)


def _documento(**alteracoes):
    dados = {
        "numero_rps": 7,
        "serie_rps": None,
        "ambiente": "HOMOLOGACAO",
        "criado_em": datetime(2026, 9, 18, 11, 0),
    }
    dados.update(alteracoes)
    return SimpleNamespace(**dados)


def _configuracao_fiscal(**alteracoes):
    dados = {
        "serie_rps": "1",
        "municipio_ibge": "3554508",
        "codigo_lc116": "14.01",
        "codigo_servico_municipal": "001",
        "proximo_rps": 99,
    }
    dados.update(alteracoes)
    return SimpleNamespace(**dados)


def _capturar_dps(monkeypatch):
    capturado = {}

    def fake_montar_dps_canonica(**kwargs):
        capturado.update(kwargs)
        return kwargs

    monkeypatch.setattr(
        adapter,
        "montar_dps_canonica",
        fake_montar_dps_canonica,
    )

    return capturado


def test_b7a2_001_mapeia_os_para_dps_sem_produtos(monkeypatch):
    capturado = _capturar_dps(monkeypatch)

    configuracao = SimpleNamespace(id=1)
    config_fiscal = _configuracao_fiscal()

    resultado = adapter.montar_dps_canonica_da_os(
        documento=_documento(),
        ordem_servico=_ordem(),
        configuracao=configuracao,
        configuracao_fiscal=config_fiscal,
        versao_layout="1.01",
        tipo_emitente="1",
        municipio_incidencia_ibge="3554508",
        iss={
            "tributacao_issqn": "1",
            "tipo_retencao": "1",
        },
        totais_tributos={
            "indicador": "0",
        },
    )

    assert resultado == capturado
    assert capturado["serie"] == "1"
    assert capturado["numero_dps"] == 7
    assert capturado["competencia"].isoformat() == "2026-09-18"

    assert (
        capturado["valores"]["valor_servicos"]
        == Decimal("450.00")
    )

    assert capturado["servico"]["descricao"] == (
        "Manutencao eletrica industrial"
    )

    assert capturado["tomador"]["tipo_documento"] == "CNPJ"
    assert capturado["tomador"]["endereco"]["pais"] == "BR"

    assert "valor_total_produtos" not in capturado["valores"]


def test_b7a2_002_nao_inventa_numero_dps(monkeypatch):
    _capturar_dps(monkeypatch)

    with pytest.raises(
        adapter.AdaptacaoDpsErpInvalida,
        match="nao possui numero",
    ):
        adapter.montar_dps_canonica_da_os(
            documento=_documento(numero_rps=None),
            ordem_servico=_ordem(),
            configuracao=SimpleNamespace(id=1),
            configuracao_fiscal=_configuracao_fiscal(),
            versao_layout="1.01",
            tipo_emitente="1",
            municipio_incidencia_ibge="3554508",
            iss={
                "tributacao_issqn": "1",
                "tipo_retencao": "1",
            },
            totais_tributos={
                "indicador": "0",
            },
        )


def test_b7a2_003_bloqueia_desconto_global_ambiguo(monkeypatch):
    _capturar_dps(monkeypatch)

    with pytest.raises(
        adapter.AdaptacaoDpsErpInvalida,
        match="desconto global",
    ):
        adapter.montar_dps_canonica_da_os(
            documento=_documento(),
            ordem_servico=_ordem(
                valor_desconto=Decimal("25.00")
            ),
            configuracao=SimpleNamespace(id=1),
            configuracao_fiscal=_configuracao_fiscal(),
            versao_layout="1.01",
            tipo_emitente="1",
            municipio_incidencia_ibge="3554508",
            iss={
                "tributacao_issqn": "1",
                "tipo_retencao": "1",
            },
            totais_tributos={
                "indicador": "0",
            },
        )


def test_b7a2_004_nao_consumir_proximo_rps(monkeypatch):
    _capturar_dps(monkeypatch)

    config_fiscal = _configuracao_fiscal(
        proximo_rps=321
    )

    adapter.montar_dps_canonica_da_os(
        documento=_documento(numero_rps=12),
        ordem_servico=_ordem(),
        configuracao=SimpleNamespace(id=1),
        configuracao_fiscal=config_fiscal,
        versao_layout="1.01",
        tipo_emitente="1",
        municipio_incidencia_ibge="3554508",
        iss={
            "tributacao_issqn": "1",
            "tipo_retencao": "1",
        },
        totais_tributos={
            "indicador": "0",
        },
    )

    assert config_fiscal.proximo_rps == 321


def test_b7a2_005_pf_vira_cpf():
    cliente = _cliente()
    cliente.tipo = "PF"
    cliente.cpf_cnpj = "123.456.789-00"
    cliente.nome = "Pessoa Teste"

    ordem = _ordem(cliente=cliente)

    tomador = adapter.montar_tomador_da_os(
        ordem
    )

    assert tomador["tipo_documento"] == "CPF"
    assert tomador["documento"] == "123.456.789-00"
    assert tomador["nome"] == "Pessoa Teste"