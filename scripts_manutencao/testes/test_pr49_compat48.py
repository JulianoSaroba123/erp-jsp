"""Rodar também na árvore temporária combinada com a PR48, sem fazer merge."""
from datetime import date
from decimal import Decimal
import pytest
from app.extensoes import db
from app.ordem_servico import ordem_servico_model as os_model
from app.financeiro.financeiro_utils import gerar_lancamento_ordem_servico
from app.ordem_servico.custos_service import resumo_custos
from scripts_manutencao.testes.test_pr46_os_recebimento import banco_pr46, caso_jumirim_ficticio
from scripts_manutencao.testes.test_pr49_custos import caso_custos, salvar, bancario


@pytest.mark.parametrize('banco_pr46',['sqlite','postgresql'],indirect=True)
def test_custos_nao_reconhecem_receita_nem_modificam_caixa(caso_custos):
    if not hasattr(os_model,'ReconhecimentoReceitaOS'):
        pytest.skip('PR48 ainda não integrada; executar na árvore de compatibilidade')
    from app.ordem_servico.receita_etapas import registrar_etapa
    from app.financeiro.financeiro_routes import receita_etapas_periodo
    app,ids=caso_custos
    with app.app_context():
        gerar_lancamento_ordem_servico(db.session.get(os_model.OrdemServico,ids['os']))
        antes=bancario(ids)
        etapa=registrar_etapa(os_id=ids['os'],competencia=date(2026,9,11),descricao='Etapa teste compatibilidade',
            valor='400',usuario='9',chave='compat49-48')
        db.session.commit()
        salvar(ids); db.session.commit()
        assert resumo_custos(ids['os'])['contratada']==Decimal('800')
        assert resumo_custos(ids['os'])['margem']==Decimal('400')
        assert resumo_custos(ids['os'])['recebida']==0
        assert receita_etapas_periodo(date(2026,9,1),date(2026,9,30))==Decimal('400')
        assert os_model.ReconhecimentoReceitaOS.query.count()==1 and etapa.ativo
        assert bancario(ids)==antes


from scripts_manutencao.testes.test_pr49_migration import engine_migracao, preparar, carregar


def test_migracoes_independentes_preservam_dados(engine_migracao):
    import importlib.util
    from pathlib import Path
    import sqlalchemy as sa
    from alembic.migration import MigrationContext
    from alembic.operations import Operations
    path=Path(__file__).resolve().parents[2]/'migrations/versions/20261027_01_os_receita_etapas.py'
    if not path.exists(): pytest.skip('Rodar na árvore combinada com PR48')
    spec=importlib.util.spec_from_file_location('compat_migration48',path)
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
    with engine_migracao.begin() as c:
        preparar(c)
        antes=c.execute(sa.text('SELECT * FROM lancamentos_financeiros')).all()
        with Operations.context(MigrationContext.configure(c)):
            m.upgrade(); carregar().upgrade()
        assert {'os_receita_etapas','os_custos_internos','os_custos_auditoria'} <= set(sa.inspect(c).get_table_names())
        assert c.execute(sa.text('SELECT * FROM lancamentos_financeiros')).all()==antes
        with Operations.context(MigrationContext.configure(c)):
            carregar().downgrade(); m.downgrade()
        assert c.execute(sa.text('SELECT * FROM lancamentos_financeiros')).all()==antes
