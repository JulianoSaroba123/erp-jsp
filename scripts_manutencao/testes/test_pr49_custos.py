"""Integração real Flask/SQLAlchemy; somente dados artificiais, banco isolado."""
from datetime import date
from decimal import Decimal
from uuid import uuid4
import json
import pytest
from flask import render_template
from werkzeug.datastructures import MultiDict
from app.extensoes import db
from app.fiscal.nfse_documento_model import NfseDocumento
from app.fiscal.configuracao_fiscal_model import ConfiguracaoFiscal
from app.ordem_servico.custos_model import CustoOrdemServico, EventoCustoInterno
from app.ordem_servico.custos_service import salvar_custo, inativar_custo, resumo_custos, CustoInvalido
from app.colaborador.colaborador_model import Colaborador, OrdemServicoColaborador
from app.ordem_servico.ordem_servico_model import OrdemServico, OrdemServicoProduto
from app.financeiro.financeiro_model import ContaBancaria, LancamentoFinanceiro, ExtratoBancario, ConciliacaoBancariaItem
from app.financeiro.indicadores_service import resumir_financeiro_periodo
from scripts_manutencao.testes.test_pr46_os_recebimento import banco_pr46, caso_jumirim_ficticio


@pytest.fixture()
def caso_custos(caso_jumirim_ficticio):
    app, ids = caso_jumirim_ficticio
    with app.app_context():
        ordem = db.session.get(OrdemServico, ids['os'])
        ordem.numero = 'OS20260101'
        # Valor contratual da referência; demais dados são artificiais.
        for item in ordem.servicos:
            item.valor_unitario = Decimal('800'); item.calcular_total()
        for parcela, valor in zip(ordem.parcelas, ['400','200','200']):
            parcela.valor = Decimal(valor)
        db.session.flush()
        ordem.valor_servico = Decimal('800'); ordem.valor_total = Decimal('800')
        lua = Colaborador(nome='Luã FICTÍCIO', salario_mensal=Decimal('3219.87'), ativo=True)
        juliano = Colaborador(nome='Juliano Fraga FICTÍCIO', ativo=True)
        db.session.add_all([lua,juliano]); db.session.flush()
        ids['lua'], ids['juliano'] = lua.id, juliano.id
        for id, valor in [(165, '600.00'),(166, '500.00')]:
            db.session.add(LancamentoFinanceiro(id=id, descricao=f'Pagamento consolidado FICTÍCIO {id}',
                tipo='conta_pagar', status='pago', valor=Decimal(valor), data_lancamento=date(2026,9,11),
                data_pagamento=date(2026,9,11), conta_bancaria_id=ids['conta'], sem_movimentacao_bancaria=True, ativo=True))
        db.session.flush()
        extrato = db.session.get(ExtratoBancario, ids['extrato'])
        extrato.valor=Decimal('600'); extrato.tipo_movimento='debito'; extrato.conciliado=True; extrato.lancamento_id=165
        segundo = ExtratoBancario(conta_bancaria_id=ids['conta'], data_movimento=date(2026,9,11),
            descricao='Pagamento Fraga FICTÍCIO', tipo_movimento='debito', valor=Decimal('500'), saldo=Decimal('13900'), conciliado=True, ativo=True)
        db.session.add(segundo); db.session.flush()
        db.session.add_all([ConciliacaoBancariaItem(extrato_id=extrato.id, lancamento_id=165, valor_conciliado=Decimal('600'), ativo=True),
            ConciliacaoBancariaItem(extrato_id=segundo.id, lancamento_id=166, valor_conciliado=Decimal('500'), ativo=True)])
        db.session.commit()
        ids['extrato2']=segundo.id
    yield app, ids


def dados(ids, valor='400.00', **kw):
    d=dict(categoria='mao_obra', modalidade='diaria', descricao='Atividade FICTÍCIA Luã',
        data_custo='2026-09-11', quantidade='2', valor=valor, situacao='realizado', fonte_custo='Acordo fictício teste',
        colaborador_id=ids['lua'], lancamento_id=165)
    d.update(kw)
    return d


def salvar(ids, valor='400.00', os_id='padrao', **kw):
    return salvar_custo(os_id=ids['os'] if os_id=='padrao' else os_id, dados=dados(ids, valor, **kw),
        usuario='admin-teste', motivo='Teste isolado de rateio', chave=uuid4().hex)


def bancario(ids):
    return {
        'pagamentos':[(p.id,p.valor,p.status,p.ativo,p.data_pagamento,p.conta_bancaria_id) for p in LancamentoFinanceiro.query.order_by(LancamentoFinanceiro.id)],
        'extratos':[(e.id,e.valor,e.conciliado,e.lancamento_id,e.saldo) for e in ExtratoBancario.query.order_by(ExtratoBancario.id)],
        'conciliacao':[(c.id,c.extrato_id,c.lancamento_id,c.valor_conciliado,c.ativo) for c in ConciliacaoBancariaItem.query.order_by(ConciliacaoBancariaItem.id)],
        'saldo': db.session.get(ContaBancaria,ids['conta']).saldo_atual,
        'despesas':resumir_financeiro_periodo(date(2026,9,1),date(2026,9,30)).despesas_realizadas,
    }


def test_cenario_os20260101_1100_800_300_sem_efeitos_bancarios(caso_custos):
    app, ids=caso_custos
    with app.app_context():
        antes=bancario(ids)
        salvar(ids)
        salvar(ids, '200.00', os_id=None, descricao='Organização interna Luã')
        salvar(ids, colaborador_id=ids['juliano'], lancamento_id=166, descricao='Atividade FICTÍCIA Fraga')
        salvar(ids, '100.00', os_id=None, colaborador_id=ids['juliano'], lancamento_id=166, descricao='Organização interna Fraga')
        db.session.commit(); db.session.expire_all()
        assert resumo_custos(ids['os'])['realizados']==Decimal('800')
        assert resumo_custos(None)['realizados']==Decimal('300')
        assert sum(p.valor for p in LancamentoFinanceiro.query.filter(LancamentoFinanceiro.id.in_([165,166])))==Decimal('1100')
        assert bancario(ids)==antes
        assert EventoCustoInterno.query.filter_by(entidade='custo', operacao='criacao').count()==4


@pytest.mark.parametrize('modalidade,quantidade', [('hora','3.5'),('diaria','2'),('servico','1')])
def test_custo_sem_pagamento_modalidades(caso_custos, modalidade, quantidade):
    app,ids=caso_custos
    with app.app_context():
        antes=bancario(ids)
        c=salvar(ids, modalidade=modalidade, quantidade=quantidade, lancamento_id=None)
        db.session.commit()
        assert c.valor==Decimal('400') and c.lancamento_id is None
        assert bancario(ids)==antes


def test_rateio_excedente_e_repetido_revertem(caso_custos):
    app,ids=caso_custos
    with app.app_context():
        chave=uuid4().hex
        salvar_custo(os_id=ids['os'], dados=dados(ids), usuario='9', motivo='Teste', chave=chave)
        db.session.commit()
        with pytest.raises(CustoInvalido,match='repetida'):
            salvar_custo(os_id=ids['os'], dados=dados(ids), usuario='9', motivo='Teste', chave=chave)
        db.session.rollback()
        with pytest.raises(CustoInvalido,match='ultrapassa'):
            salvar(ids,'201',os_id=None)
        db.session.rollback()
        assert CustoOrdemServico.query.count()==1


@pytest.mark.parametrize('campo,valor', [('ativo',False),('status','pendente'),('tipo','receita')])
def test_pagamento_incompativel(caso_custos,campo,valor):
    app,ids=caso_custos
    with app.app_context():
        p=db.session.get(LancamentoFinanceiro,165)
        setattr(p,campo,valor); db.session.commit()
        with pytest.raises(CustoInvalido): salvar(ids)
        db.session.rollback()
        assert CustoOrdemServico.query.count()==0


def test_edicao_inativacao_auditoria_versao_sem_dobrar(caso_custos):
    app,ids=caso_custos
    with app.app_context():
        antes=bancario(ids)
        c=salvar(ids); db.session.commit(); cid=c.id
        salvar_custo(os_id=ids['os'],dados=dados(ids,'350'),usuario='10',motivo='Ajuste revisado',custo_id=cid,versao=1)
        db.session.commit()
        assert resumo_custos(ids['os'])['realizados']==Decimal('350')
        with pytest.raises(CustoInvalido,match='outro usuário'):
            salvar_custo(os_id=ids['os'],dados=dados(ids,'300'),usuario='11',motivo='Formulário antigo',custo_id=cid,versao=1)
        db.session.rollback()
        inativar_custo(os_id=ids['os'],custo_id=cid,versao=2,usuario='10',motivo='Duplicidade revisada')
        db.session.commit()
        assert resumo_custos(ids['os'])['realizados']==0
        eventos=EventoCustoInterno.query.filter_by(entidade='custo',registro_id=cid).order_by(EventoCustoInterno.id).all()
        assert [e.operacao for e in eventos]==['criacao','edicao','inativacao']
        assert json.loads(eventos[1].anterior)['valor']=='400.00'
        assert bancario(ids)==antes
        with pytest.raises(ValueError,match='histórico'):
            eventos[0].motivo='apagar'; db.session.flush()
        db.session.rollback()


def test_pagamento_rateado_nao_pode_mudar(caso_custos):
    app,ids=caso_custos
    with app.app_context():
        salvar(ids); db.session.commit()
        p=db.session.get(LancamentoFinanceiro,165)
        p.valor=Decimal('999')
        with pytest.raises(ValueError,match='rateio'): db.session.flush()
        db.session.rollback()
        assert db.session.get(LancamentoFinanceiro,165).valor==Decimal('600')


def test_margem_estimados_nao_informados_tributos(caso_custos):
    app,ids=caso_custos
    with app.app_context():
        assert resumo_custos(ids['os'])['incompleta']
        salvar(ids)
        salvar(ids,'100',categoria='material',modalidade='unidade',lancamento_id=None,descricao='Material realizado')
        salvar(ids,'50',categoria='alimentacao',lancamento_id=None,situacao='estimado',descricao='Refeições estimadas')
        salvar(ids,None,categoria='deslocamento',lancamento_id=None,situacao='nao_informado',descricao='Viagem pendente')
        salvar(ids,'80',categoria='tributos',lancamento_id=None,descricao='Tributo atribuído')
        db.session.commit()
        r=resumo_custos(ids['os'])
        assert r['realizados']==500 and r['estimados']==50 and r['nao_informados']==1
        assert r['margem']==300 and r['percentual']==Decimal('37.5')
        assert r['incompleta'] and r['resultado_apos_tributos'] is None


def apontamento(ids):
    t=OrdemServicoColaborador(ordem_servico_id=ids['os'],colaborador_id=ids['lua'],data_trabalho=date(2026,9,11),
        valor_hora_custo=Decimal('123.45'),hora_entrada_manha=__import__('datetime').time(8),hora_saida_manha=__import__('datetime').time(12),ativo=True)
    t.calcular_horas_automatico(); db.session.add(t); db.session.commit(); return t


def form_apontamento(ordem,t,**campos):
    d=MultiDict({'apontamentos_revisao':ordem.apontamentos_revisao, 'colaboradores[0][id]':str(t.id),
        'colaboradores[0][colaborador_id]':str(t.colaborador_id), 'colaboradores[0][data_trabalho]':'2026-09-11',
        'colaboradores[0][hora_entrada_manha]':'08:00','colaboradores[0][hora_saida_manha]':'13:00'})
    d.update(campos); return d


def test_apontamentos_preservam_id_valor_historico_inclusao_remocao(caso_custos):
    from app.ordem_servico.ordem_servico_routes import processar_colaboradores_os
    from app.auth.usuario_model import Usuario
    from flask_login import login_user
    app,ids=caso_custos
    with app.app_context(),app.test_request_context('/'):
        login_user(Usuario.query.filter_by(usuario='admin_pr46').one())
        t=apontamento(ids); tid=t.id
        ordem=db.session.get(OrdemServico,ids['os'])
        d=form_apontamento(ordem,t)
        processar_colaboradores_os(ordem,d); db.session.commit()
        assert t.id==tid and t.total_horas==5 and t.valor_hora_custo==Decimal('123.45')
        with pytest.raises(ValueError,match='Recarregue'): processar_colaboradores_os(ordem,d)
        db.session.rollback()
        d=form_apontamento(ordem,t)
        d.update({'colaboradores[1][colaborador_id]':str(ids['juliano']),'colaboradores[1][data_trabalho]':'2026-09-11'})
        processar_colaboradores_os(ordem,d); db.session.commit()
        assert OrdemServicoColaborador.query.filter_by(ordem_servico_id=ids['os'],ativo=True).count()==2
        processar_colaboradores_os(ordem,MultiDict({'apontamentos_revisao':ordem.apontamentos_revisao})); db.session.commit()
        assert OrdemServicoColaborador.query.filter_by(ordem_servico_id=ids['os']).count()==2
        assert OrdemServicoColaborador.query.filter_by(ordem_servico_id=ids['os'],ativo=True).count()==0
        assert EventoCustoInterno.query.filter_by(entidade='apontamento',operacao='inativacao').count()==2


def test_apontamento_com_custo_nao_pode_ser_removido_ou_usado_por_outra_os(caso_custos):
    from app.ordem_servico.ordem_servico_routes import processar_colaboradores_os
    from app.auth.usuario_model import Usuario
    from flask_login import login_user
    app,ids=caso_custos
    with app.app_context(),app.test_request_context('/'):
        login_user(Usuario.query.filter_by(usuario='admin_pr46').one())
        t=apontamento(ids)
        salvar(ids,apontamento_id=t.id); db.session.commit()
        ordem=db.session.get(OrdemServico,ids['os'])
        with pytest.raises(ValueError,match='custo ativo'):
            processar_colaboradores_os(ordem,MultiDict({'apontamentos_revisao':ordem.apontamentos_revisao}))
        db.session.rollback()
        with pytest.raises(CustoInvalido,match='incompatível'):
            salvar(ids,os_id=None,apontamento_id=t.id)
        db.session.rollback()
        with pytest.raises(CustoInvalido,match='já possui'):
            salvar(ids,'10',apontamento_id=t.id,lancamento_id=None)
        db.session.rollback()
        assert db.session.get(OrdemServicoColaborador,t.id).ativo


def login(client,admin=True):
    client.post('/auth/login',data={'identificador':'admin_pr46' if admin else 'comum_pr46','senha':'SenhaPr46Teste!'})


def test_http_permissoes_csrf_destino_filtros(caso_custos):
    app,ids=caso_custos
    client=app.test_client(); path=f"/ordem-servico/{ids['os']}/custos"
    # Prefixo real do módulo.
    with app.test_request_context():
        from flask import url_for
        path=url_for('ordem_servico.custos_os',id=ids['os'])
        interno=url_for('ordem_servico.custos_internos')
    assert client.get(path).status_code==302
    login(client,False)
    assert client.get(path).status_code==403 and client.get(interno).status_code==403
    client.get('/auth/logout'); login(client)
    response=client.get(path); assert response.status_code==200
    assert b'Custos e Rentabilidade' in response.data
    assert client.post(path,data={'acao':'salvar'}).status_code==400
    with client.session_transaction() as sess: csrf=sess['_csrf_os_custos']
    d=dados(ids); d.update(csrf_custos=csrf,acao='salvar',motivo='Teste HTTP',confirmar='sim',chave_operacao=uuid4().hex)
    assert client.post(path,data=d).status_code==302
    assert b'Atividade FICT' in client.get(path).data
    with app.app_context(): cid=CustoOrdemServico.query.one().id
    assert client.get(interno+f'?editar={cid}').status_code==404
    assert client.post(path,data={**d,'chave_operacao':uuid4().hex,'confirmar':''}).status_code==400
    assert client.get(path+'?atividade=invalido').status_code==400


def test_confidencialidade_pdf_cliente_parametros_e_api_salario(caso_custos):
    from flask import url_for
    app,ids=caso_custos
    with app.app_context():
        t=apontamento(ids)
        salvar(ids,descricao='SEGREDO_INTERNO_PR49',apontamento_id=t.id); db.session.commit()
    client=app.test_client()
    with app.test_request_context():
        pdf=url_for('ordem_servico.gerar_relatorio_pdf',id=ids['os'])
        api=url_for('colaborador.api_buscar_ativos')
    assert client.get(pdf+'?fechamento=1').status_code==302
    login(client,False)
    assert client.get(pdf+'?fechamento=1').status_code==403
    assert all('salario_mensal' not in x for x in client.get(api).json['colaboradores'])
    for extra in ['', '?com_custos=1','?fechamento=0&com_custos=1']:
        r=client.get(pdf+extra)
        assert r.status_code==200
        assert b'SEGREDO_INTERNO_PR49' not in r.data and b'123.45' not in r.data
        assert b'Custo/h' not in r.data and b'FECHAMENTO DE M' not in r.data
    client.get('/auth/logout'); login(client)
    assert client.get(pdf+'?fechamento=1').status_code==200
    assert b'123.45' in client.get(pdf+'?fechamento=1').data
    # O template comercial é seguro mesmo se um chamador passar o flag interno.
    with app.test_request_context():
        from app.configuracao.configuracao_utils import get_config
        html=render_template('os/pdf_ordem_servico.html',ordem=db.session.get(OrdemServico,ids['os']),config=get_config(),
            fechamento=True,com_custos=True,now=__import__('datetime').datetime.now,anexos_base64={})
        assert '123.45' not in html and 'SEGREDO_INTERNO_PR49' not in html


def test_duplicidade_exata_bloqueada_mesmo_com_chaves_distintas(caso_custos):
    app,ids=caso_custos
    with app.app_context():
        salvar(ids,'100',lancamento_id=None); db.session.commit()
        with pytest.raises(CustoInvalido,match='idêntico'):
            salvar(ids,'100',lancamento_id=None)
        db.session.rollback()
        assert CustoOrdemServico.query.count()==1


def test_http_edicao_os_preserva_apontamento_material_e_custo(caso_custos):
    from app.financeiro.financeiro_utils import gerar_lancamento_ordem_servico
    app,ids=caso_custos
    with app.app_context():
        t=apontamento(ids); tid=t.id
        p=OrdemServicoProduto(ordem_servico_id=ids['os'],descricao='Material histórico fictício',quantidade=Decimal('1'),valor_unitario=Decimal('10'))
        p.calcular_total(); db.session.add(p); db.session.commit(); pid=p.id
        salvar(ids,'50',categoria='material',modalidade='unidade',colaborador_id=None,lancamento_id=None,produto_os_id=pid,descricao='Material comprado')
        db.session.commit()
        ordem=db.session.get(OrdemServico,ids['os'])
        d=form_apontamento(ordem,t)
        d.update({'cliente_id':str(ordem.cliente_id),'titulo':'Título editado com vínculos',
            'tipo_os':'comercial','tipo_servico':'atendimento','status':'iniciada',
            'condicao_pagamento':'parcelado','status_pagamento':'pendente','numero_parcelas':'3',
            'valor_entrada':'405','valor_desconto':'0','forma_pagamento':'pix','data_abertura':'2026-09-11',
            'data_primeira_parcela':'2026-09-17',
            'servico_descricao[]':'Serviço fictício','servico_tipo[]':'fechado','servico_quantidade[]':'1','servico_valor[]':'800',
            'produto_os_id[]':str(pid),'produto_id[]':'','produto_descricao[]':'Material histórico fictício',
            'produto_descricao_custom[]':'','produto_quantidade[]':'1','produto_valor[]':'10',
            'parcela_data[]':['2026-09-17','2026-10-17','2026-11-17'],
            'parcela_valor[]':['405','202.50','202.50']})
    client=app.test_client(); login(client)
    r=client.post(f"/ordem_servico/{ids['os']}/editar",data=d)
    assert r.status_code==302
    with app.app_context():
        ordem=db.session.get(OrdemServico,ids['os'])
        assert ordem.titulo=='Título editado com vínculos'
        assert db.session.get(OrdemServicoColaborador,tid).ativo
        assert db.session.get(OrdemServicoProduto,pid).descricao=='Material histórico fictício'
        c=CustoOrdemServico.query.one()
        assert c.produto_os_id==pid and c.valor==50
        assert EventoCustoInterno.query.filter_by(entidade='apontamento',registro_id=tid).count()>0


def test_custo_materiais_historico_nao_usa_preco_atual_estoque(caso_custos):
    from app.produto.produto_model import Produto
    app,ids=caso_custos
    with app.app_context():
        produto=Produto(nome='Peça de teste',preco_custo=Decimal('90'),preco_venda=Decimal('150'),estoque_atual=10,ativo=True)
        db.session.add(produto); db.session.flush()
        p=OrdemServicoProduto(ordem_servico_id=ids['os'],produto_id=produto.id,descricao=produto.nome,quantidade=Decimal('1'),valor_unitario=150)
        p.calcular_total(); db.session.add(p); db.session.commit()
        salvar(ids,'70',categoria='material',modalidade='unidade',colaborador_id=None,lancamento_id=None,produto_os_id=p.id,descricao='Material por nota histórica')
        db.session.commit(); saldo=produto.estoque_atual
        produto.preco_custo=Decimal('120'); db.session.commit()
        assert CustoOrdemServico.query.one().valor==70 and produto.estoque_atual==saldo


def test_falha_de_auditoria_reverte_custo_e_preserva_financeiro(caso_custos,monkeypatch):
    import app.ordem_servico.custos_service as service
    app,ids=caso_custos
    with app.app_context():
        antes=bancario(ids)
        def falhar(*args,**kw): raise RuntimeError('Falha simulada de auditoria')
        monkeypatch.setattr(service,'auditar',falhar)
        with pytest.raises(RuntimeError,match='simulada'):
            salvar(ids)
        db.session.rollback()
        assert CustoOrdemServico.query.count()==0
        assert bancario(ids)==antes


def test_previa_interface_e_visibilidade_administrativa(caso_custos):
    import os
    import re
    from pathlib import Path
    from jinja2 import ChoiceLoader, DictLoader
    app,ids=caso_custos
    with app.app_context():
        salvar(ids,descricao='SEGREDO_INTERNO_PR49_LUA')
        salvar(ids,'200',os_id=None,descricao='Organização interna Luã')
        salvar(ids,colaborador_id=ids['juliano'],lancamento_id=166,descricao='SEGREDO_INTERNO_PR49_FRAGA')
        salvar(ids,'100',os_id=None,colaborador_id=ids['juliano'],lancamento_id=166,descricao='Organização interna Fraga')
        db.session.commit()
    client=app.test_client();login(client,False)
    pagina=client.get(f"/ordem_servico/{ids['os']}")
    assert pagina.status_code==200 and b'SEGREDO_INTERNO_PR49' not in pagina.data
    assert b'Gerenciar custos e rateios' not in pagina.data
    client.get('/auth/logout');login(client)
    pagina=client.get(f"/ordem_servico/{ids['os']}/custos")
    assert pagina.status_code==200 and b'SEGREDO_INTERNO_PR49' in pagina.data
    assert b'Gerenciar custos e rateios' in pagina.data
    if os.environ.get('PR49_PREVIEW_PATH'):
        destino=Path(os.environ['PR49_PREVIEW_PATH']).resolve()
        raiz=Path(__file__).resolve().parents[2]
        assert destino==raiz/'docs/pr49-previa.html'
        # Usa o template funcional; apenas a base recebe estilos offline simplificados.
        base='''<!doctype html><html lang="pt-BR"><head><meta charset="utf-8"><title>Prévia PR49 — dados fictícios</title><style>
        *{box-sizing:border-box}body{margin:0;padding:25px;background:#101c2b;color:#e7edf5;font:15px Arial;line-height:1.5}a{color:#65d5d4}h1{font-size:25px}.card{background:#1a2c40;border:1px solid #365267;border-radius:12px;margin:20px 0}.card-header{padding:16px;background:#223d53;font-size:18px}.card-body{padding:20px}.row{display:flex;flex-wrap:wrap;gap:15px}.row>div{flex:1 1 28%}.col-12{flex-basis:100%!important}.form-control,.form-select{width:100%;padding:10px;border:1px solid #547083;border-radius:6px;background:#152438;color:white}.form-label{display:block;margin-bottom:5px}small{color:#afc6d8}.fs-5{font-size:24px;color:#69ded7}.alert{background:#443c22;padding:12px;border-left:4px solid #e9c266;margin:12px 0}.btn,button{display:inline-block;padding:8px 12px;background:#187b83;border:0;border-radius:6px;color:white;text-decoration:none;cursor:default}table{width:100%;border-collapse:collapse}td,th{padding:12px;text-align:left;border-bottom:1px solid #365267}pre{white-space:pre-wrap;font-size:11px}.text-end{text-align:right}.badge{background:#806426;padding:4px 8px;border-radius:6px}.table-responsive{overflow:auto}details{margin:12px 0}.mt-3{margin-top:15px}.mb-1{margin-bottom:5px}
        </style></head><body><p><strong>JSP — PRÉVIA COM DADOS FICTÍCIOS</strong><br>Gerada dos templates da PR49, com base e estilos simplificados para leitura offline. A tela publicada utiliza o layout atual do ERP. Os controles desta prévia não executam operações.</p>{% block content %}{% endblock %}<script>document.querySelectorAll('form').forEach(f=>f.addEventListener('submit',e=>e.preventDefault()));</script></body></html>'''
        app.jinja_loader=ChoiceLoader([DictLoader({'base.html':base}),app.jinja_loader]);app.jinja_env.cache.clear()
        pagina=client.get(f"/ordem_servico/{ids['os']}/custos")
        assert pagina.status_code==200
        html=re.sub(r'(name="csrf_custos" value=")[^"]+',r'\1TOKEN_DE_PREVIA',pagina.get_data(as_text=True))
        html=html.replace('SEGREDO_INTERNO_PR49_LUA','Instalação elétrica — Luã (teste)').replace('SEGREDO_INTERNO_PR49_FRAGA','Instalação elétrica — Fraga (teste)')
        destino.parent.mkdir(exist_ok=True);destino.write_text(html,encoding='utf-8')


def test_tela_interna_separa_custos_da_rentabilidade_os(caso_custos):
    app, ids = caso_custos
    with app.app_context():
        salvar(ids, '200', os_id=None, descricao='Custo interno isolado')
        salvar(ids, '400', descricao='Custo exclusivo da OS')
        db.session.commit()
        antes = bancario(ids)
    client = app.test_client()
    login(client)
    interna = client.get('/ordem_servico/custos-internos')
    assert interna.status_code == 200
    html = interna.get_data(as_text=True)
    assert 'Resumo de custos internos' in html and 'R$ 200,00' in html
    assert 'Custo interno isolado' in html and 'Custo exclusivo da OS' not in html
    for texto in ('Receita contratada', 'Receita recebida registrada', 'Margem de contribuição', 'Rentabilidade incompleta', 'Fonte do recebimento', 'name="apontamento_id"', 'name="produto_os_id"'):
        assert texto not in html
    assert 'jsp-executive-suite-phase-f.css' in html
    os_html = client.get(f"/ordem_servico/{ids['os']}/custos").get_data(as_text=True)
    assert 'Receita contratada' in os_html and 'Margem de contribuição' in os_html
    assert 'Custo exclusivo da OS' in os_html and 'Custo interno isolado' not in os_html
    assert 'name="apontamento_id"' in os_html and 'name="produto_os_id"' in os_html
    with app.app_context():
        assert bancario(ids) == antes
