# -*- coding: utf-8 -*-
# D25F01-B2.1
# Homologacao isolada da rota HTTP N:N.
# Extrai conciliar_nn do AST sem importar app/__init__.py.

from __future__ import annotations

import ast
import copy
import sys
import types
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path
from types import SimpleNamespace


ROOT = Path(__file__).resolve().parents[2]
ROUTES = ROOT / "app" / "financeiro" / "financeiro_routes.py"


class ConciliacaoInvalida(ValueError):
    pass


@dataclass(frozen=True)
class SolicitacaoAlocacao:
    lancamento_id: int
    valor: Decimal


class RequestFake:
    def __init__(self):
        self.payload = None

    def get_json(self, silent=False):
        return self.payload


class SessionFake:
    def __init__(self):
        self.rollbacks = 0

    def rollback(self):
        self.rollbacks += 1


class DbFake:
    def __init__(self):
        self.session = SessionFake()


class LoggerFake:
    def __init__(self):
        self.warnings = []
        self.exceptions = []

    def warning(self, *args):
        self.warnings.append(args)

    def exception(self, *args):
        self.exceptions.append(args)


class AdapterFake:
    def __init__(self):
        self.chamadas = []
        self.erro = None

    def executar(
        self,
        *,
        extrato_id,
        alocacoes,
        usuario=None,
        observacoes=None,
    ):
        self.chamadas.append({
            "extrato_id": extrato_id,
            "alocacoes": tuple(alocacoes),
            "usuario": usuario,
            "observacoes": observacoes,
        })

        if self.erro is not None:
            raise self.erro

        preparacao = SimpleNamespace(
            extrato_id=extrato_id,
            valor_extrato=Decimal("990.00"),
            valor_ja_conciliado=Decimal("0.00"),
            total_novo=sum(
                (
                    alocacao.valor
                    for alocacao in alocacoes
                ),
                Decimal("0.00"),
            ),
            saldo_final_extrato=Decimal("0.00"),
            status_final="CONCILIADO",
        )

        return SimpleNamespace(
            preparacao=preparacao,
            itens_criados=len(alocacoes),
            itens_atualizados=0,
        )


def carregar_funcao_real():
    source = ROUTES.read_text(encoding="utf-8")
    tree = ast.parse(source)

    encontrada = None

    for node in tree.body:
        if (
            isinstance(node, ast.FunctionDef)
            and node.name == "conciliar_nn"
        ):
            encontrada = copy.deepcopy(node)
            break

    assert encontrada is not None, (
        "Funcao conciliar_nn nao encontrada."
    )

    encontrada.decorator_list = []

    module = ast.Module(
        body=[encontrada],
        type_ignores=[],
    )

    ast.fix_missing_locations(module)

    namespace = {
        "Decimal": Decimal,
    }

    exec(
        compile(
            module,
            filename=str(ROUTES),
            mode="exec",
        ),
        namespace,
    )

    return namespace["conciliar_nn"]


def instalar_modulos_fake(adapter):
    adapter_module = types.ModuleType(
        "app.financeiro.conciliacao_adapter"
    )

    adapter_module.executar_conciliacao_bancaria = (
        adapter.executar
    )

    service_module = types.ModuleType(
        "app.financeiro.conciliacao_service"
    )

    service_module.ConciliacaoInvalida = (
        ConciliacaoInvalida
    )

    service_module.SolicitacaoAlocacao = (
        SolicitacaoAlocacao
    )

    sys.modules[
        "app.financeiro.conciliacao_adapter"
    ] = adapter_module

    sys.modules[
        "app.financeiro.conciliacao_service"
    ] = service_module


request = RequestFake()
db = DbFake()
logger = LoggerFake()
current_user = SimpleNamespace(
    id=7,
    username="homologacao-b21",
)


def jsonify(payload):
    return payload


adapter = AdapterFake()
instalar_modulos_fake(adapter)

funcao = carregar_funcao_real()

funcao.__globals__.update({
    "request": request,
    "db": db,
    "logger": logger,
    "current_user": current_user,
    "jsonify": jsonify,
    "Decimal": Decimal,
})


# CASO 1 - MR JACKY
request.payload = {
    "extrato_id": 101,
    "alocacoes": [
        {
            "lancamento_id": 82,
            "valor": "450.00",
        },
        {
            "lancamento_id": 84,
            "valor": "540.00",
        },
    ],
    "observacoes": "MR Jacky B2.1",
}

body, status = funcao()

assert status == 200
assert body["ok"] is True
assert body["extrato_id"] == 101
assert body["total_novo"] == "990.00"
assert body["saldo_final_extrato"] == "0.00"
assert body["status_final"] == "CONCILIADO"
assert body["itens_criados"] == 2
assert body["itens_atualizados"] == 0

assert len(adapter.chamadas) == 1

chamada = adapter.chamadas[0]

assert chamada["extrato_id"] == 101
assert chamada["usuario"] == "homologacao-b21"
assert chamada["observacoes"] == "MR Jacky B2.1"

assert chamada["alocacoes"] == (
    SolicitacaoAlocacao(
        lancamento_id=82,
        valor=Decimal("450.00"),
    ),
    SolicitacaoAlocacao(
        lancamento_id=84,
        valor=Decimal("540.00"),
    ),
)


# CASO 2 - PAYLOAD INVALIDO
request.payload = {
    "extrato_id": 101,
    "alocacoes": [],
}

body, status = funcao()

assert status == 400
assert body["ok"] is False
assert "ao menos uma alocacao" in body["erro"]
assert db.session.rollbacks == 1


# CASO 3 - REGRA FINANCEIRA REJEITADA
adapter.erro = ConciliacaoInvalida(
    "Selecao excede o valor disponivel."
)

request.payload = {
    "extrato_id": 101,
    "alocacoes": [
        {
            "lancamento_id": 82,
            "valor": "1090.00",
        }
    ],
}

body, status = funcao()

assert status == 400
assert body["ok"] is False
assert body["erro"] == (
    "Selecao excede o valor disponivel."
)
assert db.session.rollbacks == 2


# CASO 4 - ERRO INESPERADO NAO VAZA DETALHE
adapter.erro = RuntimeError(
    "segredo interno que nao pode vazar"
)

request.payload = {
    "extrato_id": 101,
    "alocacoes": [
        {
            "lancamento_id": 82,
            "valor": "450.00",
        }
    ],
}

body, status = funcao()

assert status == 500
assert body["ok"] is False
assert "segredo interno" not in body["erro"]
assert body["erro"] == (
    "Erro interno ao processar "
    "a conciliacao bancaria."
)
assert db.session.rollbacks == 3


# CASO 5 - LEGADO CONTINUA PRESENTE
source = ROUTES.read_text(encoding="utf-8")

assert source.count("def conciliar_nn(") == 1
assert source.count("def conciliar_manual(") == 1
assert (
    "/conciliacao-bancaria/conciliar-nn"
    in source
)

print("=== D25F01-B2.1 ===")
print("Rota N:N extraida do AST: OK")
print("MR Jacky 450 + 540: HTTP 200")
print("Payload vazio: HTTP 400")
print("Regra financeira rejeitada: HTTP 400")
print("Erro inesperado protegido: HTTP 500")
print("Rota legada 1:1 preservada: OK")
print()
print("D25F01-B2.1 HOMOLOGADO")
