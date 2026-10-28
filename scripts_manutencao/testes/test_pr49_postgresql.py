"""Concorrência em PostgreSQL efêmero local/CI, nunca usa DATABASE_URL para PG."""
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from decimal import Decimal
from uuid import uuid4
import pytest
from sqlalchemy.exc import IntegrityError
from app.extensoes import db
from app.ordem_servico.custos_model import CustoOrdemServico, EventoCustoInterno
from app.ordem_servico.custos_service import salvar_custo, CustoInvalido
from scripts_manutencao.testes.test_pr46_os_recebimento import banco_pr46, caso_jumirim_ficticio
from scripts_manutencao.testes.test_pr49_custos import caso_custos, dados, salvar, bancario

pytestmark=pytest.mark.parametrize('banco_pr46',['postgresql'],indirect=True)


def test_rateio_simultaneo_nao_ultrapassa_pagamento(caso_custos):
    app,ids=caso_custos
    barreira=Barrier(2)
    with app.app_context(): antes=bancario(ids)
    def worker(i):
        with app.app_context():
            try:
                barreira.wait(timeout=15)
                salvar_custo(os_id=None,dados=dados(ids,descricao=f'Interno concorrente {i}'),
                    usuario=str(i),motivo='Teste concorrente',chave=uuid4().hex)
                db.session.commit(); return 'ok'
            except CustoInvalido:
                db.session.rollback(); return 'bloqueado'
            finally: db.session.remove()
    with ThreadPoolExecutor(max_workers=2) as e: respostas=list(e.map(worker,[1,2]))
    assert sorted(respostas)==['bloqueado','ok']
    with app.app_context():
        assert CustoOrdemServico.query.count()==1
        assert bancario(ids)==antes


def test_edicao_simultanea_detecta_versao(caso_custos):
    app,ids=caso_custos
    with app.app_context():
        c=salvar(ids); db.session.commit(); cid=c.id
    barreira=Barrier(2)
    def worker(i):
        with app.app_context():
            try:
                # Sessão deliberadamente mantém objeto lido antes da disputa.
                lido=db.session.get(CustoOrdemServico,cid)
                assert lido.versao==1
                barreira.wait(timeout=15)
                salvar_custo(os_id=ids['os'],dados=dados(ids,str(100+i)),usuario=str(i),motivo='Teste de versão',custo_id=cid,versao=1)
                db.session.commit(); return 'ok'
            except CustoInvalido:
                db.session.rollback(); return 'bloqueado'
            finally: db.session.remove()
    with ThreadPoolExecutor(max_workers=2) as e: respostas=list(e.map(worker,[1,2]))
    assert sorted(respostas)==['bloqueado','ok']
    with app.app_context():
        assert db.session.get(CustoOrdemServico,cid).versao==2
        assert EventoCustoInterno.query.filter_by(entidade='custo',registro_id=cid).count()==2


def test_criacao_identica_simultanea_com_chaves_distintas(caso_custos):
    app,ids=caso_custos
    barreira=Barrier(2)
    def worker(i):
        with app.app_context():
            try:
                barreira.wait(timeout=15)
                salvar(ids,'100',os_id=None,descricao='Mesma atividade concorrente')
                db.session.commit(); return 'ok'
            except (CustoInvalido,IntegrityError):
                db.session.rollback(); return 'bloqueado'
            finally: db.session.remove()
    with ThreadPoolExecutor(max_workers=2) as e: respostas=list(e.map(worker,[1,2]))
    assert sorted(respostas)==['bloqueado','ok']
    with app.app_context(): assert CustoOrdemServico.query.count()==1
