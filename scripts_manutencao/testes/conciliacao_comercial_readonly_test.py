# -*- coding: utf-8 -*-
"""Conciliação comercial: testes puros, sem banco e sem gravar documentos."""
import importlib.util
from datetime import date
from decimal import Decimal
from pathlib import Path
from types import SimpleNamespace as NS

import pytest
from jinja2 import Environment

ROOT = Path(__file__).resolve().parents[2]
SERVICE = ROOT / "app/financeiro/conciliacao_comercial_service.py"


@pytest.fixture
def service():
    spec = importlib.util.spec_from_file_location("jsp_conciliacao_pura", SERVICE)
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


def doc(kind, ident, *, status=None, valor="100.00", proposta_id=None,
        tipo_os="comercial", cliente_id=7, ativo=True):
    base = dict(
        id=ident, status=status or "pendente", ativo=ativo,
        cliente_id=cliente_id, cliente=NS(nome="Cliente Teste"),
        valor_total=Decimal(valor), proposta_id=proposta_id,
        tipo_os=tipo_os,
    )
    if kind == "proposta":
        base["codigo"] = f"PROP{ident:06d}"
    else:
        base["numero"] = f"{'PED' if kind == 'pedido' else 'OS'}{ident:06d}"
    return NS(**base)


def lan(ident, *, proposta_id=None, pedido_id=None, os_id=None,
        valor="100.00", status="pendente", data_pagamento=None,
        numero_documento=None, ativo=True, tipo="conta_receber"):
    return NS(
        id=ident, ativo=ativo, tipo=tipo,
        proposta_id=proposta_id, pedido_id=pedido_id,
        ordem_servico_id=os_id, valor=Decimal(valor), status=status,
        data_pagamento=data_pagamento, cliente_id=7,
        numero_documento=numero_documento,
    )


def montar(s, propostas=(), pedidos=(), ordens=(), lans=(), parcelas=(), **kwargs):
    return s.montar_conciliacao(
        propostas, pedidos, ordens, lans, parcelas,
        situacao="todas", **kwargs,
    )


def linha(resultado, kind):
    return next(x for x in resultado["linhas"] if x["tipo"] == kind)


def test_proposta_aprovada_sem_financeiro_para_revisao(service):
    resultado = montar(service, propostas=[doc("proposta", 1, status="aprovada")])
    assert resultado["totais"]["propostas_revisar"] == 1
    assert linha(resultado, "proposta")["financeiro"]["ids"] == []


def test_proposta_pendente_nao_exige_cobranca(service):
    resultado = montar(service, propostas=[doc("proposta", 1)])
    assert resultado["totais"]["propostas_revisar"] == 0
    assert linha(resultado, "proposta")["situacao"] == "em_andamento"


def test_proposta_com_parcela_e_recebivel(service):
    proposta = doc("proposta", 1, status="aprovada")
    result = montar(
        service, propostas=[proposta],
        lans=[lan(10, proposta_id=1)],
        parcelas=[NS(id=5, proposta_id=1, ativo=True)],
    )
    assert linha(result, "proposta")["situacao"] == "vinculado"


def test_proposta_os_mesmo_lancamento_nao_duplica_valor(service):
    prop = doc("proposta", 1, status="aprovada")
    os = doc("os", 2, status="concluida", proposta_id=1)
    receivel = lan(10, proposta_id=1, os_id=2)
    result = montar(service, [prop], (), [os], [receivel])
    assert linha(result, "proposta")["financeiro"]["total"] == Decimal("100.00")
    assert linha(result, "os")["financeiro"]["ids"] == [10]


def test_pedido_direto_concluido_sem_vinculo_sinalizado(service):
    result = montar(service, pedidos=[doc("pedido", 1, status="CONCLUIDO")])
    assert result["totais"]["pedidos_revisar"] == 1


def test_pedido_direto_com_financeiro_vinculado(service):
    result = montar(
        service, pedidos=[doc("pedido", 1, status="CONCLUIDO")],
        lans=[lan(15, pedido_id=1)],
    )
    assert result["totais"]["pedidos_revisar"] == 0


def test_pedido_vinculado_proposta_nao_gera_alarme_sem_dupla_origem(service):
    result = montar(
        service,
        propostas=[doc("proposta", 1, status="aprovada")],
        pedidos=[doc("pedido", 2, status="CONCLUIDO", proposta_id=1)],
        lans=[lan(15, proposta_id=1)],
    )
    pedido = linha(result, "pedido")
    assert pedido["situacao"] == "vinculado"
    assert pedido["financeiro"]["ids"] == [15]


def test_pedido_com_duas_origens_requer_conferencia(service):
    result = montar(
        service,
        propostas=[doc("proposta", 1, status="aprovada")],
        pedidos=[doc("pedido", 2, status="CONCLUIDO", proposta_id=1)],
        lans=[lan(15, proposta_id=1), lan(16, pedido_id=2)],
    )
    assert linha(result, "pedido")["situacao"] == "revisar"


def test_os_direta_concluida_sem_financeiro_requer_revisao(service):
    result = montar(service, ordens=[doc("os", 1, status="concluida")])
    assert result["totais"]["os_revisar"] == 1


def test_os_operacional_nao_e_tratada_como_cobranca(service):
    result = montar(
        service, ordens=[doc("os", 1, status="concluida", tipo_os="operacional")]
    )
    assert result["totais"]["os_revisar"] == 0


def test_os_com_recebivel_da_proposta_e_reconhecida(service):
    result = montar(
        service,
        propostas=[doc("proposta", 1, status="aprovada")],
        ordens=[doc("os", 2, status="concluida", proposta_id=1)],
        lans=[lan(15, proposta_id=1)],
    )
    assert linha(result, "os")["situacao"] == "vinculado"


def test_baixa_somente_quando_recebida_com_data(service):
    result = montar(
        service,
        propostas=[doc("proposta", 1, status="aprovada")],
        lans=[
            lan(10, proposta_id=1, status="recebido", data_pagamento=date(2026, 10, 8)),
            lan(11, proposta_id=1, status="recebido", data_pagamento=None),
        ],
    )
    assert linha(result, "proposta")["financeiro"]["recebido"] == Decimal("100.00")


def test_lancamento_manual_sem_chave_nao_e_baixa_confirmada(service):
    p = doc("proposta", 1, status="aprovada")
    result = montar(
        service, propostas=[p],
        lans=[lan(20, numero_documento=p.codigo)],
    )
    item = linha(result, "proposta")
    assert item["situacao"] == "revisar"
    assert item["candidatos_manuais"] == [20]
    assert item["financeiro"]["ids"] == []


def test_lancamento_cancelado_nao_conta_como_vinculo(service):
    result = montar(
        service, pedidos=[doc("pedido", 1, status="CONCLUIDO")],
        lans=[lan(9, pedido_id=1, status="cancelado")],
    )
    assert result["totais"]["pedidos_revisar"] == 1


def test_filtro_busca_por_codigo_e_tipo(service):
    result = montar(
        service, propostas=[doc("proposta", 1, status="aprovada")],
        pedidos=[doc("pedido", 2, status="CONCLUIDO")],
        busca="PED000002", tipo="pedido",
    )
    assert result["total_filtrado"] == 1
    assert result["linhas"][0]["tipo"] == "pedido"


def test_paginacao_tem_limite_fixo_e_ordem_estavel(service):
    ps = [doc("proposta", x, status="aprovada") for x in range(1, 28)]
    result = montar(service, propostas=ps, pagina=2)
    assert result["paginas"] == 2
    assert len(result["linhas"]) == 2
    assert result["linhas"][0]["id"] == 2


def test_situacao_revisar_filtra_sem_alterar_totais(service):
    result = service.montar_conciliacao(
        [doc("proposta", 1, status="aprovada"),
         doc("proposta", 2, status="pendente")],
        [], [], [], situacao="revisar",
    )
    assert result["total_filtrado"] == 1
    assert result["totais"]["documentos"] == 2


def test_objetos_originals_nao_sao_modificados(service):
    proposta = doc("proposta", 1, status="aprovada")
    antes = vars(proposta).copy()
    montar(service, propostas=[proposta])
    assert vars(proposta) == antes


def test_template_jinja_valido_e_sem_formularios_de_escrita():
    template = (
        ROOT / "app/financeiro/templates/financeiro/conciliacao_comercial.html"
    ).read_text(encoding="utf-8")
    Environment().parse(template)
    assert 'method="get"' in template
    assert 'method="post"' not in template.lower()


def test_rotas_nunca_recebem_post():
    rota = (
        ROOT / "app/financeiro/conciliacao_comercial_routes.py"
    ).read_text(encoding="utf-8")
    assert '@bp_conciliacao_comercial.get(' in rota
    assert "tem_permissao(\"visualizar_financeiro\")" in rota
    assert '.post(' not in rota


def test_servico_nao_usa_escrita_orm():
    codigo = SERVICE.read_text(encoding="utf-8")
    for proibido in [
        "db.session.commit(", "db.session.flush(", "db.session.add(",
        "db.session.delete(", "db.session.execute(text(",
    ]:
        assert proibido not in codigo


def test_proposta_com_valor_financeiro_divergente_requer_revisao(service):
    result = montar(
        service,
        propostas=[doc("proposta", 1, status="aprovada", valor="200.00")],
        lans=[lan(10, proposta_id=1, valor="100.00")],
    )
    assert linha(result, "proposta")["situacao"] == "revisar"


def test_os_concluida_com_valor_financeiro_divergente_requer_revisao(service):
    result = montar(
        service,
        ordens=[doc("os", 1, status="concluida", valor="200.00")],
        lans=[lan(10, os_id=1, valor="150.00")],
    )
    assert linha(result, "os")["situacao"] == "revisar"


def test_pedido_direto_concluido_com_valor_divergente(service):
    result = montar(
        service,
        pedidos=[doc("pedido", 1, status="CONCLUIDO", valor="250.00")],
        lans=[lan(10, pedido_id=1, valor="100.00")],
    )
    assert linha(result, "pedido")["situacao"] == "revisar"
