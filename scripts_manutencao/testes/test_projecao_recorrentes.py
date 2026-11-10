# -*- coding: utf-8 -*-
"""Cenários de caixa sem produção; funções puras, fontes isoladas."""
from datetime import date
from decimal import Decimal
from types import SimpleNamespace as N

import pytest

from app.financeiro.projecao_recorrentes_service import gerar_previsao


def custo(id, nome, valor, dia, *, categoria='Contabilidade',
          conta=1, inicio=date(2026, 1, 1), fim=None, ativo=True):
    return N(id=id, nome=nome, categoria=categoria, valor_mensal=Decimal(str(valor)),
             dia_vencimento=dia, tipo='DESPESA', data_inicio=inicio,
             data_fim=fim, gerar_automaticamente=True, ativo=ativo,
             conta_bancaria_id=conta)


def titulo(id, valor, tipo, status, venc, descricao, *, custo_id=None,
           pago=None, conta=1):
    return N(id=id, valor=Decimal(str(valor)), tipo=tipo, status=status,
             data_vencimento=venc, data_pagamento=pago, data_lancamento=venc,
             descricao=descricao, categoria='Operacional', custo_fixo_id=custo_id,
             conta_bancaria_id=conta, ativo=True)


def calcular_cenario(hoje, dias, fixos=(), titulos=(), inicial=8508.77):
    return gerar_previsao(hoje=hoje, dias=dias, saldo_inicial=Decimal(str(inicial)),
                         conta_id=1, custos=fixos, lancamentos=titulos)


def test_previsao_30_60_90_mensal_sem_escrever():
    ref = date(2026, 11, 9)
    custos = [custo(8, 'Contabilidade', 350, 10)]
    p30 = calcular_cenario(ref, 30, custos)
    assert p30['qtd_recorrencias_estimadas'] == 1
    assert p30['total_despesas'] == 350
    assert p30['saldo_final'] == 8158.77
    p60 = calcular_cenario(ref, 60, custos)
    assert p60['qtd_recorrencias_estimadas'] == 2
    assert p60['total_despesas'] == 700
    p90 = calcular_cenario(ref, 90, custos)
    assert p90['qtd_recorrencias_estimadas'] == 3
    assert p90['total_despesas'] == 1050
    assert len(p90['projecao']) == 91
    assert p90['saldo_final'] == 7458.77
    assert not any(l.status == 'pago' for l in p90['projecao'][0]['lancamentos'])


def test_ja_quitado_no_mes_ou_ja_pendente_nao_duplicar():
    ref = date(2026, 11, 9)
    fixos = [custo(8,'Contabilidade',350,10)]
    coberto = titulo(1,350,'conta_pagar','pago',date(2026,11,10),
                     'Contabilidade - 2026-11',custo_id=8,pago=date(2026,11,7))
    p = calcular_cenario(ref, 60, fixos, [coberto])
    assert p['total_despesas'] == 350  # só dezembro
    assert p['qtd_recorrencias_estimadas'] == 1
    pendente = titulo(2,355,'conta_pagar','pendente',date(2026,12,10),
                     'Contabilidade - 2026-12',custo_id=8)
    q = calcular_cenario(ref,60,fixos,[coberto,pendente])
    assert q['total_despesas'] == 355
    assert q['qtd_recorrencias_estimadas'] == 0


def test_manual_pago_correspondente_bloqueia_previsao_e_avisa():
    ref = date(2026, 11, 9)
    custos = [custo(2,'Energia Elétrica',400,19,categoria='Energia')]
    pago = titulo(3,415.34,'conta_pagar','pago',date(2026,11,19),
                  'Pagamento CPFL de energia elétrica da JSP',pago=date(2026,11,8))
    p = calcular_cenario(ref,30,custos,[pago])
    assert p['total_despesas'] == 0
    assert p['qtd_recorrencias_estimadas'] == 0
    assert any('possivelmente correspondente' in a for a in p['alertas'])


def test_titulos_pendentes_separados_de_quitados_e_passado_vence_hoje():
    ref = date(2026,11,9)
    contas = [
        titulo(1,3500,'conta_receber','pendente',date(2026,11,20),'OS A'),
        titulo(2,120,'conta_pagar','pendente',date(2026,11,5),'Internet'),
        titulo(3,30,'conta_pagar','pago',date(2026,11,11),'Pago',pago=date(2026,11,8)),
    ]
    p = calcular_cenario(ref,30,[],contas)
    assert p['total_receitas'] == 3500
    assert p['total_despesas'] == 120
    assert p['saldo_final'] == 11888.77
    assert len(p['projecao'][0]['lancamentos']) == 1
    assert any('vencido' in a for a in p['alertas'])


def test_exclusoes_revisao_valor_e_conta_diferente():
    ref=date(2026,11,9)
    fixos=[
        custo(1,'Prolabore',3000,10,categoria='Salários'),
        custo(2,'Dr. Adinho Imoveis',1000,10,categoria='Aluguel'),
        custo(3,'Contabilidade',350,10,conta=2),
        custo(4,'Taxa Negativa',-12,10),
    ]
    p=calcular_cenario(ref,30,fixos)
    assert p['total_despesas'] == 1000
    assert p['qtd_recorrencias_estimadas'] == 1
    assert any('Prolabore' in a and 'exige revisão' in a for a in p['alertas'])


def test_fevereiro_e_vigencia_e_ano_novo():
    p=calcular_cenario(date(2027,1,1),90,[
        custo(6,'Contabilidade',100,31,fim=date(2027,2,28)),
    ])
    datas=[l.vencimento_original for d in p['projecao'] for l in d['lancamentos']]
    assert date(2027,1,31) in datas
    assert date(2027,2,28) in datas
    assert date(2027,3,31) not in datas
    assert p['total_despesas']==200


def test_horizonte_invalido_abortado():
    with pytest.raises(ValueError,match='30, 60 ou 90'):
        calcular_cenario(date(2026,11,9),365)

def test_celular_e_vivo_sao_contas_distintas_sem_falso_positivo():
    ref = date(2026, 11, 9)
    contas = [
        custo(5,'Vivo - Telecomunicação',119,10,categoria='Telefone'),
        custo(10,'Celular',62.71,10,categoria='Telefone')
    ]
    # Um pagamento manual do plano Vivo não quita nem cobre a conta Celular.
    vivo_pago = titulo(290,63.97,'conta_pagar','pago',date(2026,11,10),
                      'Plano Vivo Celular Empresarial - Novembro/2026',
                      pago=date(2026,11,8))
    p = calcular_cenario(ref, 30, contas, [vivo_pago])
    assert p['qtd_recorrencias_estimadas'] == 1
    assert p['total_despesas'] == 62.71
    assert any('Celular (11/2026)' in x.descricao
               for d in p['projecao'] for x in d['lancamentos'])
    # Sem pagamento manual, as duas obrigações são estimadas individualmente.
    q = calcular_cenario(ref, 30, contas)
    assert q['qtd_recorrencias_estimadas'] == 2
    assert q['total_despesas'] == 181.71

