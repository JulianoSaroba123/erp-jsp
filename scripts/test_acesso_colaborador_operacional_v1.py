# -*- coding: utf-8 -*-
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OS_ROUTES = ROOT / "app/ordem_servico/ordem_servico_routes.py"
FIN_ROUTES = ROOT / "app/financeiro/financeiro_routes.py"
NFSE_ROUTES = ROOT / "app/financeiro/nfse_routes.py"
BASE = ROOT / "app/templates/base.html"
LISTA = ROOT / "app/ordem_servico/templates/os/listar_colaborador.html"
VIEW = ROOT / "app/ordem_servico/templates/os/visualizar_colaborador.html"
APONT = ROOT / "app/ordem_servico/templates/os/apontamento_colaborador.html"

os_routes = OS_ROUTES.read_text(encoding="utf-8")
fin = FIN_ROUTES.read_text(encoding="utf-8")
nfse = NFSE_ROUTES.read_text(encoding="utf-8")
base = BASE.read_text(encoding="utf-8")
lista = LISTA.read_text(encoding="utf-8")
view = VIEW.read_text(encoding="utf-8")
apont = APONT.read_text(encoding="utf-8")

# Catraca real no Financeiro e fiscal.
assert "@bp_financeiro.before_request" in fin
assert "current_user.tem_permissao('visualizar_financeiro')" in fin
assert "@bp_nfse.before_request" in nfse
assert "current_user.tem_permissao('visualizar_financeiro')" in nfse

# Resolução de identidade do colaborador deve ser fail-closed e nunca por nome.
assert "def colaborador_do_usuario_atual():" in os_routes
assert "db.func.lower(Colaborador.email) == email" in os_routes
assert "return encontrados[0] if len(encontrados) == 1 else None" in os_routes
assert "current_user.nome" not in os_routes.split("def colaborador_do_usuario_atual():", 1)[1].split("def ordem_pertence_ao_colaborador", 1)[0]

# Só OS próprias e operacionais.
assert "OrdemServicoColaborador.colaborador_id == colaborador_vinculado.id" in os_routes
assert "OrdemServicoColaborador.ativo.is_(True)" in os_routes
assert "OrdemServico.tipo_os == 'operacional'" in os_routes
assert "query = query.filter(OrdemServico.id == -1)  # fail-closed" in os_routes

# Blueprint da OS limita a superfície do colaborador.
assert "def restringir_rotas_colaborador():" in os_routes
for endpoint in (
    "ordem_servico.listar",
    "ordem_servico.visualizar",
    "ordem_servico.apontamento_colaborador",
):
    assert endpoint in os_routes

# Rota dedicada só atualiza dados operacionais.
assert "def apontamento_colaborador(id):" in os_routes
bloco = os_routes.split("def apontamento_colaborador(id):", 1)[1].split("def editar(id):", 1)[0]
for campo in (
    "data_trabalho",
    "hora_entrada_manha",
    "hora_saida_manha",
    "hora_entrada_tarde",
    "hora_saida_tarde",
    "hora_entrada_extra",
    "hora_saida_extra",
    "km_inicial",
    "km_final",
    "descricao_atividade",
    "observacoes",
):
    assert campo in bloco
for proibido in (
    "valor_servico",
    "valor_pecas",
    "valor_desconto",
    "status_pagamento",
    "condicao_pagamento",
    "numero_parcelas",
    "valor_entrada",
    "gerar_lancamento_ordem_servico",
):
    assert proibido not in bloco, f"Apontamento expõe regra financeira: {proibido}"

# Visualizações específicas do colaborador não exibem informações monetárias/financeiras.
for nome, html in (("lista", lista), ("visualizacao", view), ("apontamento", apont)):
    for proibido in ("R$", "valor_total", "status_pagamento", "condicao_pagamento", "parcela", "contas_receber"):
        assert proibido not in html, f"{nome} contém dado financeiro: {proibido}"

# Sidebar do colaborador deve ter apenas entrada operacional além de perfil/senha/logout.
assert "MINHA OPERAÇÃO" in base
assert ">Minhas OS<" in base
assert "current_user.tipo_usuario|default('usuario') != 'colaborador'" in base

print("ACESSO COLABORADOR OPERACIONAL V1: OK")
