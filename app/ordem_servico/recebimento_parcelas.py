"""Baixa manual e auditável de parcelas de OS, inclusive em andamento."""
from datetime import date
from decimal import Decimal
from flask import request, redirect, url_for, flash, current_app
from flask_login import login_required, current_user
from app.extensoes import db
from app.ordem_servico.ordem_servico_model import OrdemServico, OrdemServicoParcela
from app.financeiro.financeiro_model import LancamentoFinanceiro


def registrar_rotas_recebimento(blueprint):
    @blueprint.route('/<int:id>/parcelas/<int:parcela_id>/receber', methods=['POST'])
    @login_required
    def receber_parcela_os(id, parcela_id):
        destino = lambda: redirect(url_for('ordem_servico.visualizar', id=id))
        if getattr(current_user, 'tipo_usuario', None) != 'admin':
            flash('Apenas administradores podem registrar recebimentos.', 'danger')
            return destino()
        try:
            data_recebimento = date.fromisoformat(request.form['data_recebimento'])
            # Não aceitar recebimento futuro ou valor arbitrário.
            if data_recebimento > date.today():
                raise ValueError('A data do recebimento não pode ser futura.')
            with db.session.begin_nested():
                parcela = (db.session.query(OrdemServicoParcela)
                    .filter_by(id=parcela_id, ordem_servico_id=id, ativo=True)
                    .with_for_update().one_or_none())
                ordem = (db.session.query(OrdemServico)
                    .filter_by(id=id, ativo=True).one_or_none())
                if not parcela or not ordem or ordem.status == 'cancelada':
                    raise ValueError('OS ou parcela inválida.')
                if Decimal(str(parcela.valor or 0)) <= 0:
                    raise ValueError('Parcela sem valor positivo.')
                lancamentos = (db.session.query(LancamentoFinanceiro)
                    .filter_by(ordem_servico_parcela_id=parcela.id, ativo=True)
                    .with_for_update().all())
                if len(lancamentos) > 1:
                    raise ValueError('Existem lançamentos duplicados; solicitar auditoria.')
                lancamento = lancamentos[0] if lancamentos else None
                if parcela.pago or parcela.data_pagamento or (lancamento and lancamento.status == 'recebido'):
                    raise ValueError('Parcela já recebida. Nenhum novo lançamento foi criado.')
                if lancamento and Decimal(str(lancamento.valor)) != Decimal(str(parcela.valor)):
                    raise ValueError('Valor financeiro divergente da parcela.')
                if not lancamento:
                    lancamento = LancamentoFinanceiro()
                    db.session.add(lancamento)
                lancamento.descricao = f'OS {ordem.numero} - {ordem.titulo} - Parcela {parcela.numero_parcela}'
                lancamento.valor = parcela.valor
                lancamento.tipo = 'conta_receber'
                lancamento.status = 'recebido'
                lancamento.origem = 'ORDEM_SERVICO'
                lancamento.categoria = 'Serviços'
                lancamento.subcategoria = 'Ordem de Serviço'
                lancamento.cliente_id = ordem.cliente_id
                lancamento.ordem_servico_id = ordem.id
                lancamento.ordem_servico_parcela_id = parcela.id
                lancamento.data_lancamento = ordem.data_abertura or data_recebimento
                lancamento.data_vencimento = parcela.data_vencimento
                lancamento.data_pagamento = data_recebimento
                lancamento.forma_pagamento = (request.form.get('forma_pagamento') or 'pix').strip()
                lancamento.observacoes = 'Recebimento confirmado manualmente na OS; conciliar separadamente com o extrato bancário.'
                parcela.pago = True
                parcela.data_pagamento = data_recebimento
                outras = (db.session.query(OrdemServicoParcela)
                    .filter_by(ordem_servico_id=id, ativo=True).all())
                recebidas = sum(bool(p.pago or p.data_pagamento) for p in outras)
                ordem.status_pagamento = 'pago' if recebidas == len(outras) else 'parcial'
            db.session.commit()
            flash('Parcela recebida e vinculada ao financeiro. Faça a conciliação com o extrato bancário.', 'success')
        except (ValueError, KeyError) as exc:
            db.session.rollback()
            flash(str(exc), 'warning')
        except Exception:
            db.session.rollback()
            current_app.logger.exception('Falha ao receber parcela %s da OS %s', parcela_id, id)
            flash('Não foi possível registrar o recebimento. Nenhum dado foi confirmado.', 'danger')
        return destino()
