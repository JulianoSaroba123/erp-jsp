"""Interface exclusivamente administrativa, com CSRF e transação por operação."""
import hmac
import secrets
from functools import wraps
from flask import abort, current_app, flash, redirect, render_template, request, session, url_for
from flask_login import current_user, login_required
from sqlalchemy import func
from app.extensoes import db
from app.ordem_servico.custos_model import CustoOrdemServico, EventoCustoInterno
from app.ordem_servico.custos_service import CustoInvalido, salvar_custo, inativar_custo, resumo_custos, pagamento_conciliado
from app.ordem_servico.ordem_servico_model import OrdemServico, OrdemServicoProduto
from app.colaborador.colaborador_model import Colaborador, OrdemServicoColaborador
from app.financeiro.financeiro_model import LancamentoFinanceiro


def admin_required(fn):
    @wraps(fn)
    @login_required
    def wrapped(*args, **kwargs):
        if getattr(current_user, 'tipo_usuario', None) != 'admin':
            abort(403)
        return fn(*args, **kwargs)
    return wrapped


def csrf_custos():
    if '_csrf_os_custos' not in session:
        session['_csrf_os_custos'] = secrets.token_urlsafe(32)
    return session['_csrf_os_custos']


def registrar_rotas_custos(bp):
    @bp.route('/<int:id>/custos', methods=['GET', 'POST'])
    @admin_required
    def custos_os(id):
        ordem = OrdemServico.query.filter_by(id=id, ativo=True).first_or_404()
        return pagina_custos(ordem)

    @bp.route('/custos-internos', methods=['GET', 'POST'])
    @admin_required
    def custos_internos():
        return pagina_custos(None)


def pagina_custos(ordem):
    os_id = ordem.id if ordem else None
    destino = url_for('ordem_servico.custos_os', id=os_id) if ordem else url_for('ordem_servico.custos_internos')
    if request.method == 'POST':
        esperado, recebido = session.get('_csrf_os_custos', ''), request.form.get('csrf_custos', '')
        if not esperado or not hmac.compare_digest(str(esperado).encode(), recebido.encode()):
            abort(400)
        if request.form.get('confirmar') != 'sim':
            abort(400, description='Confirmação obrigatória.')
        try:
            custo_id = request.form.get('custo_id') or None
            if request.form.get('acao') == 'inativar':
                inativar_custo(os_id=os_id, custo_id=custo_id, versao=request.form.get('versao'),
                    usuario=str(current_user.id), motivo=request.form.get('motivo'))
            elif request.form.get('acao') == 'salvar':
                salvar_custo(os_id=os_id, dados=request.form, custo_id=custo_id, versao=request.form.get('versao'),
                    usuario=str(current_user.id), motivo=request.form.get('motivo'), chave=request.form.get('chave_operacao'))
            else:
                raise CustoInvalido('Operação inválida.')
            db.session.commit()
            flash('Custo atualizado com histórico. Nenhuma movimentação financeira criada.', 'success')
        except CustoInvalido as exc:
            db.session.rollback()
            flash(str(exc), 'warning')
        except Exception:
            db.session.rollback()
            current_app.logger.exception('Falha transacional no custo interno')
            flash('Não foi possível salvar. A operação foi revertida; recarregue antes de tentar novamente.', 'danger')
        return redirect(destino)
    filtro = request.args.get('atividade', 'ativos')
    if filtro not in {'ativos','inativos','todos'}:
        abort(400)
    query = CustoOrdemServico.query.filter_by(ordem_servico_id=os_id)
    if filtro != 'todos':
        query = query.filter_by(ativo=filtro == 'ativos')
    custos = query.order_by(CustoOrdemServico.data_custo.desc(), CustoOrdemServico.id.desc()).all()
    editar = None
    if request.args.get('editar'):
        try:
            editar_id = int(request.args['editar'])
        except ValueError:
            abort(400)
        editar = CustoOrdemServico.query.filter_by(id=editar_id, ordem_servico_id=os_id, ativo=True).first_or_404()
    pagamentos = LancamentoFinanceiro.query.filter(LancamentoFinanceiro.ativo.is_(True),
        LancamentoFinanceiro.tipo.in_(['conta_pagar','despesa']), LancamentoFinanceiro.status == 'pago',
        LancamentoFinanceiro.data_pagamento.isnot(None)).order_by(LancamentoFinanceiro.data_pagamento.desc(), LancamentoFinanceiro.id.desc()).all()
    alocados = dict(db.session.query(CustoOrdemServico.lancamento_id, func.sum(CustoOrdemServico.valor))
        .filter(CustoOrdemServico.ativo.is_(True), CustoOrdemServico.lancamento_id.isnot(None))
        .group_by(CustoOrdemServico.lancamento_id).all())
    ativos = CustoOrdemServico.query.filter_by(ordem_servico_id=os_id, ativo=True).all()
    suspeitas = [(a.id,b.id) for i,a in enumerate(ativos) for b in ativos[i+1:]
        if (a.categoria,a.colaborador_id,a.data_custo,a.valor) == (b.categoria,b.colaborador_id,b.data_custo,b.valor)]
    sem_pagamento = sum(c.situacao == 'realizado' and not c.lancamento_id for c in ativos)
    return render_template('os/custos.html', ordem=ordem, custos=custos, editar=editar, atividade=filtro,
        suspeitas=suspeitas, sem_pagamento=sem_pagamento,
        resumo=resumo_custos(os_id), colaboradores=Colaborador.query.order_by(Colaborador.nome).all(),
        apontamentos=OrdemServicoColaborador.query.filter_by(ordem_servico_id=os_id, ativo=True).all() if ordem else [],
        materiais=OrdemServicoProduto.query.filter_by(ordem_servico_id=os_id, ativo=True).all() if ordem else [],
        pagamentos=pagamentos, alocados=alocados,
        conciliados={p.id: pagamento_conciliado(p.id) for p in pagamentos},
        eventos=EventoCustoInterno.query.filter_by(ordem_servico_id=os_id).order_by(EventoCustoInterno.id.desc()).all(),
        csrf_custos=csrf_custos(), chave_operacao=secrets.token_hex(24), destino=destino)
