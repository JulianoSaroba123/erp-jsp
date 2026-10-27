import pytest
from scripts_manutencao.testes.test_receita_etapas import (
    banco_pr46, caso_jumirim_ficticio,
    test_etapas_separam_competencia_de_caixa_e_sao_idempotentes,
    test_http_etapas_restricao_e_csrf,
)
pytestmark = pytest.mark.parametrize('banco_pr46', ['postgresql'], indirect=True)


def test_duas_sessoes_nao_registram_etapa_duplicada(caso_jumirim_ficticio):
    from concurrent.futures import ThreadPoolExecutor
    from threading import Barrier
    from datetime import date
    from app.extensoes import db
    from app.ordem_servico.receita_etapas import registrar_etapa
    from app.ordem_servico.ordem_servico_model import ReconhecimentoReceitaOS
    app, ids = caso_jumirim_ficticio
    barreira = Barrier(2)
    def registrar(indice):
        with app.app_context():
            try:
                barreira.wait(timeout=15)
                registrar_etapa(os_id=ids['os'], competencia=date(2026,9,20),
                    descricao='Etapa fictícia', valor='4000.00', usuario='9',
                    chave=f'chave-concorrente-{indice}')
                db.session.commit()
                return 'registrada'
            except ValueError:
                db.session.rollback()
                return 'duplicada'
            finally:
                db.session.remove()
    with ThreadPoolExecutor(max_workers=2) as pool:
        assert sorted(pool.map(registrar, [1, 2])) == ['duplicada', 'registrada']
    with app.app_context():
        assert ReconhecimentoReceitaOS.query.filter_by(ordem_servico_id=ids['os']).count() == 1
