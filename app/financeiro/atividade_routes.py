"""Interface administrativa para inativação e reativação de títulos."""
import hmac
import secrets
from flask import abort, current_app, flash, redirect, render_template, request, session, url_for
from flask_login import current_user, login_required
from app.extensoes import db
from app.financeiro.financeiro_model import LancamentoFinanceiro, HistoricoFinanceiro
from app.financeiro.inativacao_service import alterar_atividade, OperacaoFinanceiraInvalida


def registrar_rotas_atividade(bp):
    @bp.route('/lancamentos/<int:id>/atividade', methods=['GET', 'POST'])
    @login_required
    def atividade_lancamento(id):
        if getattr(current_user, 'tipo_usuario', None) != 'admin':
            abort(403)
        lanc = db.session.get(LancamentoFinanceiro, id)
        if lanc is None:
            abort(404)
        if request.method == 'GET':
            token = session.setdefault('_csrf_atividade_financeira', secrets.token_urlsafe(32))
            historico = HistoricoFinanceiro.query.filter_by(lancamento_id=id).order_by(
                HistoricoFinanceiro.data_alteracao.desc(), HistoricoFinanceiro.id.desc()).all()
            return render_template('financeiro/atividade_lancamento.html', lancamento=lanc,
                                   csrf_atividade=token, historico=historico)
        enviado = request.form.get('csrf_atividade', '').encode('utf-8')
        esperado = session.get('_csrf_atividade_financeira', '')
        if not isinstance(esperado, str) or not esperado or not hmac.compare_digest(enviado, esperado.encode('utf-8')):
            abort(400)
        acao = request.form.get('acao')
        if acao not in {'inativar', 'reativar'}:
            abort(400)
        try:
            alterar_atividade(id, ativar=acao == 'reativar', motivo=request.form.get('motivo'), usuario=current_user.id)
            db.session.commit()
            flash('Estado do lançamento atualizado. Saldo e extrato bancários não foram modificados.', 'success')
            return redirect(url_for('financeiro.atividade_lancamento', id=id))
        except OperacaoFinanceiraInvalida as exc:
            db.session.rollback()
            flash(str(exc), 'warning')
        except Exception:
            db.session.rollback()
            current_app.logger.exception('Falha ao alterar atividade do lançamento %s', id)
            flash('Operação não realizada. Nenhuma alteração foi salva.', 'danger')
        return redirect(url_for('financeiro.atividade_lancamento', id=id))
