# -*- coding: utf-8 -*-
"""Marco financeiro 01/09/2026: classificação consultiva, sem alterar saldos."""
import importlib.util
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
from types import SimpleNamespace as NS

import pytest

SERVICE = Path(__file__).resolve().parents[2] / "app/financeiro/conciliacao_comercial_service.py"


@pytest.fixture
def service():
    spec = importlib.util.spec_from_file_location("marco_financeiro_puro", SERVICE)
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


def proposta(i, emissao, status="aprovada"):
    return NS(
        id=i, codigo=f"PROP-DEMO-{i}", cliente_id=1,
        cliente=NS(nome="Cliente Exemplo"), ativo=True,
        status=status, valor_total=Decimal("100.00"),
        data_emissao=emissao,
    )


def ordem(i, abertura, proposta_id=None):
    return NS(
        id=i, numero=f"OS-DEMO-{i}", proposta_id=proposta_id,
        cliente_id=1, cliente=NS(nome="Cliente Exemplo"),
        ativo=True, status="concluida", tipo_os="comercial",
        valor_total=Decimal("100.00"), data_abertura=abertura,
    )


def lancamento(i, *, proposta_id=None, pagamento=None, vencimento=None):
    return NS(
        id=i, ativo=True, tipo="conta_receber", status="recebido" if pagamento else "pendente",
        cliente_id=1, proposta_id=proposta_id, ordem_servico_id=None,
        pedido_id=None, valor=Decimal("100.00"),
        data_pagamento=pagamento, data_vencimento=vencimento,
    )


def test_marco_aprovado(service):
    assert service.MARCO_IMPLANTACAO_FINANCEIRA == date(2026, 9, 1)


def test_proposta_antiga_sem_indicio_pos_marco_e_legado_nao_quitado(service):
    resultado = service.montar_conciliacao(
        [proposta(1, date(2026, 8, 31))], [], [], [], situacao="revisar"
    )
    assert resultado["total_filtrado"] == 1
    assert resultado["linhas"][0]["periodo"] == "legado"
    assert resultado["linhas"][0]["situacao"] == "revisar"
    assert resultado["totais"]["legado_revisar"] == 1


def test_proposta_em_primeiro_de_setembro_e_operacao(service):
    resultado = service.montar_conciliacao(
        [proposta(1, date(2026, 9, 1))], [], [], []
    )
    assert resultado["linhas"][0]["periodo"] == "operacao"


def test_data_anterior_com_recebimento_de_setembro_e_transicao(service):
    resultado = service.montar_conciliacao(
        [proposta(1, date(2026, 7, 22))], [], [],
        [lancamento(7, proposta_id=1, pagamento=datetime(2026, 9, 5, 10, 30))]
    )
    assert resultado["linhas"][0]["periodo"] == "transicao"
    assert resultado["totais"]["transicao_revisar"] == 0


def test_antiga_com_vencimento_pos_marco_transicao(service):
    resultado = service.montar_conciliacao(
        [proposta(1, date(2026, 8, 15))], [], [],
        [lancamento(7, proposta_id=1, vencimento=date(2026, 9, 20))]
    )
    assert resultado["linhas"][0]["periodo"] == "transicao"


def test_parcela_legada_vencendo_depois_do_marco_e_transicao(service):
    p = proposta(1, date(2026, 7, 10))
    parcela = NS(id=10, proposta_id=1, ativo=True, data_vencimento=date(2026, 9, 12))
    resultado = service.montar_conciliacao([p], [], [], [], [parcela])
    assert resultado["linhas"][0]["periodo"] == "transicao"
    assert resultado["linhas"][0]["situacao"] == "revisar"


def test_proposta_antiga_com_os_nova_e_transicao(service):
    p = proposta(1, date(2026, 8, 18))
    o = ordem(2, date(2026, 9, 18), proposta_id=1)
    resultado = service.montar_conciliacao([p], [], [o], [])
    linha_p = next(x for x in resultado["linhas"] if x["tipo"] == "proposta")
    assert linha_p["periodo"] == "transicao"


def test_proposta_antiga_aprovada_em_setembro_e_transicao(service):
    p = proposta(1, date(2026, 8, 28))
    p.data_aprovacao = datetime(2026, 9, 2, 9, 0)
    resultado = service.montar_conciliacao([p], [], [], [])
    assert resultado["linhas"][0]["periodo"] == "transicao"


def test_periodo_operacao_filtra_sem_mudar_totais(service):
    resultado = service.montar_conciliacao(
        [proposta(1, date(2026, 8, 31)), proposta(2, date(2026, 9, 2))],
        [], [], [], situacao="revisar", periodo="operacao"
    )
    assert resultado["total_filtrado"] == 1
    assert resultado["linhas"][0]["id"] == 2
    assert resultado["totais"]["documentos"] == 2
    assert resultado["totais"]["legado_revisar"] == 1


def test_periodo_legado_filtra_de_forma_explicita(service):
    resultado = service.montar_conciliacao(
        [proposta(1, date(2026, 8, 31)), proposta(2, date(2026, 9, 2))],
        [], [], [], situacao="revisar", periodo="legado"
    )
    assert resultado["total_filtrado"] == 1
    assert resultado["linhas"][0]["id"] == 1


def test_todos_prioriza_operacao_sem_esconder_legado(service):
    resultado = service.montar_conciliacao(
        [proposta(10, date(2026, 8, 22)), proposta(1, date(2026, 9, 3))],
        [], [], [], situacao="revisar", periodo="todos"
    )
    assert resultado["total_filtrado"] == 2
    assert [x["id"] for x in resultado["linhas"]] == [1, 10]


def test_data_inexistente_nao_vira_legado_quitado(service):
    resultado = service.montar_conciliacao(
        [proposta(1, None)], [], [], [], situacao="revisar"
    )
    assert resultado["linhas"][0]["periodo"] == "sem_data"
    assert resultado["linhas"][0]["situacao"] == "revisar"


def test_parametro_periodo_invalido_retorna_todos(service):
    resultado = service.montar_conciliacao(
        [proposta(1, date(2026, 8, 31)), proposta(2, date(2026, 9, 2))],
        [], [], [], periodo="ilegivel"
    )
    assert resultado["periodo"] == "todos"
    assert resultado["total_filtrado"] == 2


def test_classificacao_nao_modifica_documentos(service):
    p = proposta(1, date(2026, 8, 31))
    snapshot = vars(p).copy()
    service.montar_conciliacao([p], [], [], [])
    assert vars(p) == snapshot


def test_template_mostra_marco_e_filtros():
    template = (SERVICE.parents[2] / "app/financeiro/templates/financeiro/conciliacao_comercial.html").read_text(encoding="utf-8")
    assert "marco_implantacao" in template
    assert 'name="periodo"' in template
    assert "Pré-implantação não significa quitado" in template
    assert "periodo=dados.periodo" in template
