"""Registro de receita das etapas executadas; não altera caixa nem parcelas."""
from datetime import date
from decimal import Decimal
import hmac
import secrets
from flask import abort, current_app, flash, redirect, render_template, request, session, url_for
from flask_login import current_user, login_required
from sqlalchemy import func
from app.extensoes import db
from app.ordem_servico.ordem_servico_model import OrdemServico, ReconhecimentoReceitaOS
from app.ordem_servico.recebimento_parcelas import _valor_monetario


def registrar_etapa(*, os_id, competencia, descricao, valor, usuario, chave):
    if not isinstance(competencia, date) or competencia > date.today():
        raise ValueError('Informe uma data de execução válida, sem data futura.')
    descricao = (descricao or '').strip()
    if not descricao or len(descricao) > 255:
        raise ValueError('Informe a etapa executada com até 255 caracteres.')
    if not chave or len(chave) > 64:
        raise ValueError('Operação inválida. Reabra o formulário.')
    quantia = _valor_monetario(valor)
    ordem = db.session.query(OrdemServico).filter_by(id=os_id, ativo=True).populate_existing().with_for_update().one_or_none()
    if ordem is None or str(ordem.status).lower() in {'cancelada', 'cancelado'}:
        raise ValueError('Ordem inexistente ou cancelada.')
    existente = ReconhecimentoReceitaOS.query.filter_by(chave_operacao=chave).first()
    if existente:
        if (existente.ordem_servico_id != os_id or existente.valor != quantia or
                existente.data_competencia != competencia or existente.descricao != descricao):
            raise ValueError('Esta operação já foi registrada com outros dados.')
        return existente
    duplicada = ReconhecimentoReceitaOS.query.filter_by(
        ordem_servico_id=os_id, data_competencia=competencia,
        descricao=descricao, valor=quantia, ativo=True).first()
    if duplicada:
        raise ValueError('Já existe uma etapa igual nesta data. Revise antes de registrar.')
    ja = db.session.query(func.coalesce(func.sum(ReconhecimentoReceitaOS.valor), 0)).filter_by(
        ordem_servico_id=os_id, ativo=True).scalar()
    if Decimal(str(ja)) + quantia > Decimal(str(ordem.valor_total or 0)):
        raise ValueError('A soma das etapas ultrapassa o valor total da OS.')
    etapa = ReconhecimentoReceitaOS(ordem_servico_id=os_id, data_competencia=competencia,
        descricao=descricao, valor=quantia, usuario=str(usuario), chave_operacao=chave)
    db.session.add(etapa)
    db.session.flush()
    return etapa


def registrar_rotas_etapa(bp):
    @bp.route('/<int:id>/receita-etapas', methods=['GET', 'POST'])
    @login_required
    def receita_etapas_os(id):
        if getattr(current_user, 'tipo_usuario', None) != 'admin':
            abort(403)
        ordem = db.session.get(OrdemServico, id)
        if ordem is None:
            abort(404)
        if request.method == 'GET':
            csrf = session.setdefault('_csrf_etapas_receita', secrets.token_urlsafe(32))
            etapas = ReconhecimentoReceitaOS.query.filter_by(ordem_servico_id=id, ativo=True).order_by(
                ReconhecimentoReceitaOS.data_competencia, ReconhecimentoReceitaOS.id).all()
            return render_template('os/receita_etapas.html', ordem=ordem, etapas=etapas,
                csrf=csrf, chave=secrets.token_urlsafe(32), today=date.today())
        esperado = session.get('_csrf_etapas_receita', '')
        recebido = request.form.get('csrf', '')
        if not isinstance(esperado, str) or not esperado or not hmac.compare_digest(esperado.encode(), recebido.encode()):
            abort(400)
        try:
            registrar_etapa(os_id=id, competencia=date.fromisoformat(request.form.get('competencia', '')),
                descricao=request.form.get('descricao'), valor=request.form.get('valor'),
                usuario=current_user.id, chave=request.form.get('chave'))
            db.session.commit()
            flash('Etapa registrada. Recebimentos e saldo bancário não foram alterados.', 'success')
        except ValueError as exc:
            db.session.rollback()
            flash(str(exc), 'warning')
        except Exception:
            db.session.rollback()
            current_app.logger.exception('Falha ao registrar etapa de receita OS %s', id)
            flash('Não foi possível registrar a etapa. Nada foi salvo.', 'danger')
        return redirect(url_for('ordem_servico.receita_etapas_os', id=id))
