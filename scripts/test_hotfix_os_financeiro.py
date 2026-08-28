import os
import sys
from pathlib import Path

os.environ['FLASK_CONFIG'] = 'testing'
os.environ['FLASK_ENV'] = 'testing'
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from datetime import date
from decimal import Decimal

from app import create_app
from app.extensoes import db
from app.cliente.cliente_model import Cliente
from app.financeiro.financeiro_model import LancamentoFinanceiro
from app.financeiro.financeiro_utils import gerar_lancamento_ordem_servico
from app.ordem_servico.ordem_servico_model import OrdemServico, OrdemServicoItem, OrdemServicoParcela


def _create_os(app, status='pendente'):
    with app.app_context():
        cliente = Cliente(nome='Cliente Hotfix', ativo=True)
        db.session.add(cliente)
        db.session.flush()
        ordem = OrdemServico(
            numero='OS-HOTFIX-001',
            titulo='OS Hotfix',
            cliente_id=cliente.id,
            status=status,
            valor_total=Decimal('200.00'),
            condicao_pagamento='parcelado',
            data_abertura=date(2026, 8, 1),
            data_prevista=date(2026, 8, 15),
            ativo=True,
        )
        db.session.add(ordem)
        db.session.flush()
        item = OrdemServicoItem(
            ordem_servico_id=ordem.id,
            descricao='Serviço de teste',
            tipo_servico='fechado',
            quantidade=Decimal('1.00'),
            valor_unitario=Decimal('200.00'),
        )
        item.calcular_total()
        db.session.add(item)
        parcela = OrdemServicoParcela(
            ordem_servico_id=ordem.id,
            numero_parcela=1,
            data_vencimento=date(2026, 8, 15),
            valor=Decimal('200.00'),
        )
        db.session.add(parcela)
        db.session.commit()
        return ordem.id, parcela.id


def test_existing_and_inactive_lancamento_are_reconciled():
    app = create_app('testing')
    assert app.config['SQLALCHEMY_DATABASE_URI'] == 'sqlite:///:memory:'
    with app.app_context():
        db.create_all()
    ordem_id, parcela_id = _create_os(app)

    with app.app_context():
        ordem = db.session.get(OrdemServico, ordem_id)
        parcela = db.session.get(OrdemServicoParcela, parcela_id)
        ordem.valor_total = Decimal('200.00')
        lancamento = LancamentoFinanceiro(
            descricao='Historico',
            valor=Decimal('200.00'),
            tipo='conta_receber',
            status='recebido',
            data_lancamento=date(2026, 8, 1),
            data_vencimento=date(2026, 8, 15),
            data_pagamento=date(2026, 8, 10),
            valor_original=Decimal('200.00'),
            juros=Decimal('3.00'),
            multa=Decimal('2.00'),
            desconto=Decimal('1.00'),
            conta_bancaria_id=None,
            comprovante_anexo='comprovante.pdf',
            ativo=False,
            ordem_servico_id=ordem.id,
            ordem_servico_parcela_id=parcela.id,
        )
        db.session.add(lancamento)
        db.session.commit()
        original_id = lancamento.id

        assert len(gerar_lancamento_ordem_servico(ordem, forma_pagamento='pix')) == 1
        assert len(gerar_lancamento_ordem_servico(ordem, forma_pagamento=None)) == 1
        db.session.expire_all()
        registros = LancamentoFinanceiro.query.filter_by(
            ordem_servico_parcela_id=parcela.id,
        ).all()
        atual = registros[0]
        assert len(registros) == 1
        assert atual.id == original_id
        assert atual.forma_pagamento == 'pix'
        assert atual.status == 'recebido'
        assert atual.data_pagamento == date(2026, 8, 10)
        assert atual.juros == Decimal('3.00')
        assert atual.multa == Decimal('2.00')
        assert atual.desconto == Decimal('1.00')
        assert atual.comprovante_anexo == 'comprovante.pdf'


def test_new_parcela_creates_one_lancamento_and_maps_payment():
    app = create_app('testing')
    with app.app_context():
        db.create_all()
    ordem_id, parcela_id = _create_os(app, status='concluida')

    with app.app_context():
        ordem = db.session.get(OrdemServico, ordem_id)
        ordem.valor_total = Decimal('200.00')
        resultado = gerar_lancamento_ordem_servico(ordem, forma_pagamento='pix')
        assert len(resultado) == 1
        assert resultado[0].ordem_servico_parcela_id == parcela_id
        assert resultado[0].forma_pagamento == 'pix'
        assert LancamentoFinanceiro.query.filter_by(
            ordem_servico_parcela_id=parcela_id,
        ).count() == 1


def test_template_uses_explicit_prefill_and_multiple_parcels_are_idempotent():
    template = Path(__file__).parents[1] / 'app' / 'ordem_servico' / 'templates' / 'os' / 'form.html'
    source = template.read_text(encoding='utf-8')
    assert 'ordem.forma_pagamento' not in source
    assert 'forma_pagamento_atual' in source
    assert 'value="__multiplas__"' in source

    app = create_app('testing')
    with app.app_context():
        db.create_all()
    ordem_id, parcela_id = _create_os(app)
    with app.app_context():
        ordem = db.session.get(OrdemServico, ordem_id)
        ordem.valor_total = Decimal('300.00')
        segunda = OrdemServicoParcela(
            ordem_servico_id=ordem.id,
            numero_parcela=2,
            data_vencimento=date(2026, 9, 15),
            valor=Decimal('100.00'),
        )
        primeira = db.session.get(OrdemServicoParcela, parcela_id)
        primeira.valor = Decimal('200.00')
        db.session.add(segunda)
        db.session.commit()
        assert len(gerar_lancamento_ordem_servico(ordem, forma_pagamento='pix')) == 2
        assert len(gerar_lancamento_ordem_servico(ordem, forma_pagamento='pix')) == 2
        assert LancamentoFinanceiro.query.filter_by(ordem_servico_id=ordem.id).count() == 2


if __name__ == '__main__':
    test_existing_and_inactive_lancamento_are_reconciled()
    test_new_parcela_creates_one_lancamento_and_maps_payment()
    test_template_uses_explicit_prefill_and_multiple_parcels_are_idempotent()
    print('HOTFIX OS FINANCEIRO: 3/3 testes passaram')
