"""Mesmos testes em banco PostgreSQL local descartável do CI."""
import pytest
from scripts_manutencao.testes.test_fluxo_projecao import (
    banco_pr46, caso_jumirim_ficticio,
    test_projecao_diferencia_pago_pendente_conciliado_e_atrasado,
    test_tela_e_excel_iguais_e_dre_avisa_limitacao,
)
pytestmark = pytest.mark.parametrize('banco_pr46', ['postgresql'], indirect=True)
