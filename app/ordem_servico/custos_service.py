"""Serviço transacional: chamador confirma/rollback; sem geração financeira."""
from datetime import date
from decimal import Decimal, InvalidOperation
import json
import hashlib
from sqlalchemy import func, select
from app.extensoes import db
from app.ordem_servico.custos_model import CustoOrdemServico, EventoCustoInterno
from app.ordem_servico.ordem_servico_model import OrdemServico, OrdemServicoParcela, OrdemServicoProduto
from app.colaborador.colaborador_model import Colaborador, OrdemServicoColaborador
from app.financeiro.financeiro_model import LancamentoFinanceiro, ConciliacaoBancariaItem, ExtratoBancario


class CustoInvalido(ValueError):
    pass


def numero(valor, casas=2):
    try:
        n = Decimal(str(valor).replace(',', '.'))
        if not n.is_finite() or n < 0 or n != n.quantize(Decimal(10) ** -casas) or n > Decimal('999999999.99'):
            raise ValueError
        return n
    except (ValueError, TypeError, InvalidOperation):
        raise CustoInvalido('Valor ou quantidade inválido.')


def snapshot(registro):
    return json.dumps({c.name: str(getattr(registro, c.name)) if getattr(registro, c.name) is not None else None
                       for c in registro.__table__.columns}, sort_keys=True, ensure_ascii=False)


def auditar(entidade, registro, anterior, usuario, operacao, motivo):
    db.session.add(EventoCustoInterno(entidade=entidade, registro_id=registro.id,
        ordem_servico_id=registro.ordem_servico_id, usuario=str(usuario), operacao=operacao,
        motivo=motivo, anterior=anterior, novo=snapshot(registro)))


def _id(valor):
    if valor in (None, ''):
        return None
    try:
        n = int(valor)
        if n <= 0:
            raise ValueError
        return n
    except (ValueError, TypeError):
        raise CustoInvalido('Identificador inválido.')


def _lock_os(os_id):
    if os_id is not None:
        ordem = db.session.execute(select(OrdemServico).where(OrdemServico.id == os_id,
            OrdemServico.ativo.is_(True)).execution_options(populate_existing=True).with_for_update()).scalar_one_or_none()
        if ordem is None:
            raise CustoInvalido('OS inexistente ou inativa.')


def salvar_custo(*, os_id, dados, usuario, custo_id=None, versao=None, motivo, chave=None):
    """Não troca o destino de custo existente. Locks OS -> custo -> pagamentos ordenados."""
    os_id = _id(os_id)
    motivo = str(motivo or '').strip()
    if not motivo or len(motivo) > 1000:
        raise CustoInvalido('Informe o motivo (até 1000 caracteres).')
    if not usuario:
        raise CustoInvalido('Usuário obrigatório.')
    _lock_os(os_id)
    custo = None
    if custo_id:
        custo = db.session.execute(select(CustoOrdemServico).where(CustoOrdemServico.id == _id(custo_id))
            .execution_options(populate_existing=True).with_for_update()).scalar_one_or_none()
        if not custo or not custo.ativo or custo.ordem_servico_id != os_id:
            raise CustoInvalido('Custo não pertence ao destino ou está inativo.')
        if str(custo.versao) != str(versao):
            raise CustoInvalido('Custo alterado por outro usuário. Recarregue a página.')
    elif not chave or len(str(chave)) > 64 or CustoOrdemServico.query.filter_by(chave_operacao=str(chave)).first():
        raise CustoInvalido('Operação repetida ou identificador de operação inválido.')
    anterior = snapshot(custo) if custo else '{}'
    categoria = dados.get('categoria')
    modalidade = dados.get('modalidade')
    situacao = dados.get('situacao')
    if categoria not in {'mao_obra','material','deslocamento','alimentacao','terceirizacao','outros','tributos'}:
        raise CustoInvalido('Categoria inválida.')
    if modalidade not in {'hora','diaria','servico','unidade'} or situacao not in {'realizado','estimado','nao_informado'}:
        raise CustoInvalido('Modalidade ou situação inválida.')
    descricao = str(dados.get('descricao') or '').strip()
    fonte = str(dados.get('fonte_custo') or '').strip()
    if not descricao or len(descricao) > 255 or not fonte or len(fonte) > 255:
        raise CustoInvalido('Informe atividade e fonte do custo (até 255 caracteres).')
    try:
        data_custo = date.fromisoformat(str(dados.get('data_custo')))
    except (ValueError, TypeError):
        raise CustoInvalido('Data de custo inválida.')
    if situacao == 'realizado' and data_custo > date.today():
        raise CustoInvalido('Custo realizado não pode ter data futura.')
    quantidade = numero(dados.get('quantidade'), 3)
    if quantidade <= 0:
        raise CustoInvalido('Quantidade deve ser positiva.')
    if situacao == 'nao_informado' and dados.get('valor') not in (None, ''):
        raise CustoInvalido('Custo não informado deve ficar sem valor.')
    valor = None if situacao == 'nao_informado' else numero(dados.get('valor'))
    colaborador_id, apontamento_id = _id(dados.get('colaborador_id')), _id(dados.get('apontamento_id'))
    produto_id, lancamento_id = _id(dados.get('produto_os_id')), _id(dados.get('lancamento_id'))
    if categoria == 'mao_obra' and not colaborador_id:
        raise CustoInvalido('Selecione o colaborador cadastrado.')
    if colaborador_id and not db.session.get(Colaborador, colaborador_id):
        raise CustoInvalido('Colaborador inexistente.')
    if apontamento_id:
        apont = db.session.execute(select(OrdemServicoColaborador).where(OrdemServicoColaborador.id == apontamento_id)
            .execution_options(populate_existing=True).with_for_update()).scalar_one_or_none()
        if not apont or not apont.ativo or apont.ordem_servico_id != os_id or apont.colaborador_id != colaborador_id or categoria != 'mao_obra':
            raise CustoInvalido('Apontamento incompatível com OS ou colaborador.')
        vinculado = CustoOrdemServico.query.filter(CustoOrdemServico.ativo.is_(True),
            CustoOrdemServico.apontamento_id == apontamento_id, CustoOrdemServico.id != (custo.id if custo else -1)).first()
        if vinculado:
            raise CustoInvalido('Apontamento já possui custo ativo. Edite o custo existente.')
    if produto_id:
        produto = db.session.get(OrdemServicoProduto, produto_id)
        if not produto or not produto.ativo or produto.ordem_servico_id != os_id or categoria != 'material':
            raise CustoInvalido('Material não pertence à OS.')
        if CustoOrdemServico.query.filter(CustoOrdemServico.produto_os_id == produto_id,
            CustoOrdemServico.ativo.is_(True), CustoOrdemServico.id != (custo.id if custo else -1)).first():
            raise CustoInvalido('Material já possui custo ativo. Edite o custo existente.')
    repetido = CustoOrdemServico.query.filter(
        CustoOrdemServico.ativo.is_(True), CustoOrdemServico.ordem_servico_id == os_id,
        CustoOrdemServico.categoria == categoria, CustoOrdemServico.colaborador_id == colaborador_id,
        CustoOrdemServico.descricao == descricao, CustoOrdemServico.data_custo == data_custo,
        CustoOrdemServico.valor == valor, CustoOrdemServico.quantidade == quantidade,
        CustoOrdemServico.situacao == situacao, CustoOrdemServico.id != (custo.id if custo else -1)).first()
    if repetido:
        raise CustoInvalido('Custo idêntico já registrado. Edite ou revise a atividade existente.')
    # Travar o pagamento também serializa com edição e inativação financeira.
    pagamentos = sorted({n for n in (lancamento_id, custo.lancamento_id if custo else None) if n})
    for pagamento_id in pagamentos:
        lanc = db.session.execute(select(LancamentoFinanceiro).where(LancamentoFinanceiro.id == pagamento_id)
            .execution_options(populate_existing=True).with_for_update()).scalar_one_or_none()
        if pagamento_id != lancamento_id:
            continue
        if not lanc or not lanc.ativo or lanc.tipo not in {'despesa','conta_pagar'} or lanc.status != 'pago' or not lanc.data_pagamento or lanc.categoria == 'Transferência Bancária':
            raise CustoInvalido('Selecione uma despesa paga, ativa e com data de pagamento.')
        if lanc.ordem_servico_id is not None and lanc.ordem_servico_id != os_id:
            raise CustoInvalido('Pagamento vinculado a outra OS.')
        if lanc.ordem_servico_parcela_id or lanc.proposta_id or lanc.proposta_parcela_id or lanc.pedido_id:
            raise CustoInvalido('Título comercial incompatível com rateio de custos.')
        if situacao != 'realizado' or not valor or valor <= 0:
            raise CustoInvalido('Rateio exige custo realizado com valor positivo.')
        alocado = db.session.query(func.coalesce(func.sum(CustoOrdemServico.valor), 0)).filter(
            CustoOrdemServico.lancamento_id == lanc.id, CustoOrdemServico.ativo.is_(True),
            CustoOrdemServico.id != (custo.id if custo else -1)).scalar()
        if Decimal(alocado) + valor > lanc.valor:
            raise CustoInvalido('Rateio ultrapassa o valor disponível do pagamento.')
    if not custo:
        custo = CustoOrdemServico(ordem_servico_id=os_id, chave_operacao=str(chave), versao=1)
        db.session.add(custo)
    else:
        custo.versao += 1
    for campo, v in dict(categoria=categoria, modalidade=modalidade, situacao=situacao, descricao=descricao,
        data_custo=data_custo, quantidade=quantidade, valor=valor, fonte_custo=fonte,
        colaborador_id=colaborador_id, apontamento_id=apontamento_id, produto_os_id=produto_id,
        lancamento_id=lancamento_id).items():
        setattr(custo, campo, v)
    custo.assinatura = hashlib.sha256(json.dumps([os_id, categoria, colaborador_id, descricao,
        data_custo.isoformat(), str(valor.quantize(Decimal('0.01'))) if valor is not None else None,
        str(quantidade.quantize(Decimal('0.001'))), situacao], ensure_ascii=False).encode()).hexdigest()
    db.session.flush()
    auditar('custo', custo, anterior, usuario, 'edicao' if anterior != '{}' else 'criacao', motivo)
    return custo


def inativar_custo(*, os_id, custo_id, versao, usuario, motivo):
    os_id = _id(os_id)
    _lock_os(os_id)
    custo = db.session.execute(select(CustoOrdemServico).where(CustoOrdemServico.id == _id(custo_id))
        .execution_options(populate_existing=True).with_for_update()).scalar_one_or_none()
    if not custo or not custo.ativo or custo.ordem_servico_id != os_id or str(custo.versao) != str(versao):
        raise CustoInvalido('Custo inválido ou alterado por outro usuário.')
    motivo = str(motivo or '').strip()
    if not usuario:
        raise CustoInvalido('Usuário obrigatório.')
    if not motivo or len(motivo) > 1000:
        raise CustoInvalido('Informe um motivo (até 1000 caracteres).')
    if custo.lancamento_id:
        db.session.execute(select(LancamentoFinanceiro).where(LancamentoFinanceiro.id == custo.lancamento_id).with_for_update()).scalar_one()
    anterior = snapshot(custo)
    custo.ativo = False
    custo.versao += 1
    auditar('custo', custo, anterior, usuario, 'inativacao', motivo)
    return custo


def resumo_custos(os_id):
    ordem = db.session.get(OrdemServico, os_id) if os_id else None
    custos = CustoOrdemServico.query.filter_by(ordem_servico_id=os_id, ativo=True).all()
    diretos = [c for c in custos if c.categoria != 'tributos']
    realizados = sum((c.valor for c in diretos if c.situacao == 'realizado'), Decimal('0'))
    estimados = sum((c.valor for c in diretos if c.situacao == 'estimado'), Decimal('0'))
    receita = Decimal(str(ordem.valor_total or 0)) if ordem else Decimal('0')
    # Parcelas são a fonte da baixa; não somar novamente seus títulos financeiros.
    parcelas = OrdemServicoParcela.query.filter_by(ordem_servico_id=os_id, ativo=True).all() if ordem else []
    legado = LancamentoFinanceiro.query.filter(
        LancamentoFinanceiro.ordem_servico_id == os_id, LancamentoFinanceiro.ativo.is_(True),
        LancamentoFinanceiro.ordem_servico_parcela_id.is_(None),
        LancamentoFinanceiro.tipo.in_(['receita','conta_receber']),
        LancamentoFinanceiro.status.in_(['pago','recebido']),
        LancamentoFinanceiro.data_pagamento.isnot(None)).all() if ordem else []
    recebida = sum((p.valor for p in parcelas if p.pago), Decimal('0')) if parcelas else sum((l.valor for l in legado), Decimal('0'))
    apontados = OrdemServicoColaborador.query.filter_by(ordem_servico_id=os_id, ativo=True).all() if ordem else []
    materiais = OrdemServicoProduto.query.filter_by(ordem_servico_id=os_id, ativo=True).all() if ordem else []
    faltantes = sum(c.situacao == 'nao_informado' for c in custos)
    faltantes += sum(not any(c.apontamento_id == a.id for c in custos) for a in apontados)
    faltantes += sum(not any(c.produto_os_id == p.id for c in custos) for p in materiais)
    tributos = [c for c in custos if c.categoria == 'tributos']
    margem = receita - realizados
    return dict(contratada=receita, recebida=Decimal(recebida), recebimentos_revisar=bool(parcelas and legado),
        fonte_recebida='parcelas baixadas' if parcelas else 'títulos recebidos sem parcelamento', realizados=realizados,
        estimados=estimados, nao_informados=faltantes, margem=margem,
        percentual=(margem / receita * 100) if receita else None,
        incompleta=not custos or faltantes > 0 or any(c.situacao == 'estimado' for c in custos),
        # Mesmo com todos os registros conhecidos, não afirmar lucro líquido.
        resultado_apos_tributos=(margem - sum((c.valor for c in tributos), Decimal('0')))
            if tributos and all(c.situacao == 'realizado' for c in tributos) and not faltantes and not estimados else None,
        por_categoria={cat:sum((c.valor for c in custos if c.categoria == cat and c.situacao == 'realizado'), Decimal('0'))
            for cat in ('mao_obra','material','deslocamento','alimentacao','terceirizacao','outros','tributos')})


def pagamento_conciliado(lancamento_id):
    return bool(ConciliacaoBancariaItem.query.filter_by(lancamento_id=lancamento_id, ativo=True).first()
        or ExtratoBancario.query.filter_by(lancamento_id=lancamento_id, conciliado=True, ativo=True).first())
