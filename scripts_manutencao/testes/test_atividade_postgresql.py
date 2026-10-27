"""Mesmas regras contra PostgreSQL local descartável do CI."""
import pytest
from scripts_manutencao.testes.test_atividade_financeira import (
    banco_pr46, caso_jumirim_ficticio,
    test_inativar_reativar_sem_movimentar_banco_e_com_auditoria,
    test_vinculos_e_conciliacao_bloqueiam,
    test_validacao_reativacao_duplicada_e_motivo,
    test_http_permissoes_csrf_filtro_e_rota_antiga,
    test_setembro_124_161_ficticios_preservam_conciliacao,
    test_titulo_inativo_nao_pode_ser_conciliado,
)
pytestmark = pytest.mark.parametrize('banco_pr46', ['postgresql'], indirect=True)
