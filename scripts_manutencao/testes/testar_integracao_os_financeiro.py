# -*- coding: utf-8 -*-
"""Teste histórico corrigido: integração OS -> Financeiro em TestingConfig."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

from app import create_app
from app.cliente.cliente_model import Cliente
from app.extensoes import db
from app.financeiro.financeiro_model import LancamentoFinanceiro
from app.ordem_servico.ordem_servico_model import OrdemServico, OrdemServicoParcela, OrdemServicoItem


def test_integracao_os_financeiro_historico_testing_sqlite():
    """Valida fluxo histórico em ambiente de testes sem PostgreSQL."""
    app = create_app('testing')

    with app.app_context():
        db.create_all()

        cliente = Cliente(
            nome='Cliente Teste - Histórico',
            cpf_cnpj='12345678000190',
            telefone='11999999999',
            email='historico_os_financeiro@teste.com',
            ativo=True,
        )
        db.session.add(cliente)
        db.session.flush()

        ordem = OrdemServico(
            numero=f'TESTE-{datetime.now().strftime("%H%M%S")}',
            titulo='Teste histórico integração',
            descricao='Validação histórica OS->Financeiro',
            cliente_id=cliente.id,
            data_abertura=date.today(),
            status='pendente',
            tipo_os='comercial',
            valor_total=Decimal('1500.00'),
            ativo=True,
        )
        db.session.add(ordem)
        db.session.flush()

        parcela = OrdemServicoParcela(
            ordem_servico_id=ordem.id,
            numero_parcela=1,
            data_vencimento=date.today(),
            valor=Decimal('1500.00'),
        )
        item = OrdemServicoItem(
            ordem_servico_id=ordem.id,
            descricao='Serviço histórico',
            quantidade=Decimal('1.00'),
            valor_unitario=Decimal('1500.00'),
            valor_total=Decimal('1500.00'),
        )
        db.session.add(parcela)
        db.session.add(item)
        db.session.commit()

        # Conclusão deve gerar lançamento automático.
        ordem.status = 'finalizada'
        db.session.commit()
        ordem.gerar_lancamento_financeiro()

        lancamentos = LancamentoFinanceiro.query.filter_by(ordem_servico_id=ordem.id, ativo=True).all()
        assert len(lancamentos) >= 1
        assert any(l.ordem_servico_parcela_id == parcela.id for l in lancamentos)
