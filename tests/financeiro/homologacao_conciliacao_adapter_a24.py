# -*- coding: utf-8 -*-
"""
D25F01-A2.4

Teste isolado da integracao entre:

- db.session real do ERP
- ExtratoBancario real
- LancamentoFinanceiro real
- ConciliacaoBancariaItem real
- conciliacao_adapter real
- executar_conciliacao_orm real

IMPORTANTE:
app/__init__.py NAO e executado.

O banco usado e exclusivamente:
sqlite:///:memory:

O arquivo erp.db e apenas lido para comparacao de SHA-256 antes/depois.
"""

from __future__ import annotations

import hashlib
import importlib
import sys
import types
from datetime import date
from decimal import Decimal
from pathlib import Path

from flask import Flask


ROOT = Path(__file__).resolve().parents[2]
APP_DIR = ROOT / "app"
FINANCEIRO_DIR = APP_DIR / "financeiro"
ERP_DB = ROOT / "erp.db"


def sha256_arquivo(caminho: Path):
    if not caminho.exists():
        return None

    digest = hashlib.sha256()

    with caminho.open("rb") as arquivo:
        for bloco in iter(lambda: arquivo.read(1024 * 1024), b""):
            digest.update(bloco)

    return digest.hexdigest()


def registrar_pacote_sintetico(nome: str, caminho: Path):
    """
    Registra um package Python em memoria sem executar __init__.py.
    """
    pacote = types.ModuleType(nome)
    pacote.__path__ = [str(caminho)]
    pacote.__package__ = nome
    pacote.__file__ = None
    pacote.__d25_pacote_sintetico__ = True

    sys.modules[nome] = pacote
    return pacote


# ============================================================
# BOOTSTRAP SEGURO
# ============================================================

registrar_pacote_sintetico("app", APP_DIR)
registrar_pacote_sintetico("app.financeiro", FINANCEIRO_DIR)

extensoes = importlib.import_module("app.extensoes")
models_base = importlib.import_module("app.models")

db = extensoes.db
BaseModel = models_base.BaseModel


# ============================================================
# STUBS MINIMOS
#
# O financeiro_model real possui relacionamentos por string com
# estes quatro models externos ao modulo financeiro.
#
# Eles existem apenas para completar o registry SQLAlchemy neste
# laboratorio em memoria.
# ============================================================

class Cliente(BaseModel):
    __tablename__ = "clientes"


class Fornecedor(BaseModel):
    __tablename__ = "fornecedores"


class OrdemServico(BaseModel):
    __tablename__ = "ordem_servico"


class OrdemServicoParcela(BaseModel):
    __tablename__ = "ordem_servico_parcelas"


class Proposta(BaseModel):
    __tablename__ = "propostas"


class ParcelaProposta(BaseModel):
    __tablename__ = "parcelas_proposta"


# Agora carregamos o model financeiro REAL da worktree.
financeiro_model = importlib.import_module(
    "app.financeiro.financeiro_model"
)

ContaBancaria = financeiro_model.ContaBancaria
ExtratoBancario = financeiro_model.ExtratoBancario
LancamentoFinanceiro = financeiro_model.LancamentoFinanceiro
ConciliacaoBancariaItem = financeiro_model.ConciliacaoBancariaItem

conciliacao_service = importlib.import_module(
    "app.financeiro.conciliacao_service"
)

SolicitacaoAlocacao = conciliacao_service.SolicitacaoAlocacao

conciliacao_adapter = importlib.import_module(
    "app.financeiro.conciliacao_adapter"
)

executar_conciliacao_bancaria = (
    conciliacao_adapter.executar_conciliacao_bancaria
)


def executar_teste():
    hash_erp_antes = sha256_arquivo(ERP_DB)

    app_teste = Flask("d25f01_a24")

    app_teste.config.update(
        TESTING=True,
        SQLALCHEMY_DATABASE_URI="sqlite:///:memory:",
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
    )

    db.init_app(app_teste)

    with app_teste.app_context():

        print("=== D25F01-A2.4 ===")
        print(f"Banco de teste: {db.engine.url}")

        assert str(db.engine.url) == "sqlite:///:memory:"
        assert getattr(
            sys.modules["app"],
            "__d25_pacote_sintetico__",
            False,
        )

        db.create_all()

        # ----------------------------------------------------
        # Conta bancaria real
        # ----------------------------------------------------

        conta = ContaBancaria(
            nome="Cora - A2.4",
            tipo="conta_corrente",
            banco="Cora",
            saldo_inicial=Decimal("0.00"),
            saldo_atual=Decimal("0.00"),
            ativa=True,
        )

        db.session.add(conta)
        db.session.flush()

        # ----------------------------------------------------
        # Caso real MR Jacky
        #
        # PIX unico = 990
        # OS/lancamento 1 = 450
        # OS/lancamento 2 = 540
        # ----------------------------------------------------

        lancamento_450 = LancamentoFinanceiro(
            descricao="MR Jacky - OS 1",
            valor=Decimal("450.00"),
            tipo="conta_receber",
            status="pendente",
            data_lancamento=date(2026, 9, 17),
            conta_bancaria_id=conta.id,
            origem="ORDEM_SERVICO",
        )

        lancamento_540 = LancamentoFinanceiro(
            descricao="MR Jacky - OS 2",
            valor=Decimal("540.00"),
            tipo="conta_receber",
            status="pendente",
            data_lancamento=date(2026, 9, 17),
            conta_bancaria_id=conta.id,
            origem="ORDEM_SERVICO",
        )

        db.session.add_all([
            lancamento_450,
            lancamento_540,
        ])

        db.session.flush()

        extrato = ExtratoBancario(
            conta_bancaria_id=conta.id,
            data_movimento=date(2026, 9, 17),
            descricao="PIX MR Jacky",
            documento="A24-MR-JACKY",
            valor=Decimal("990.00"),
            tipo_movimento="credito",
            conciliado=False,
        )

        db.session.add(extrato)
        db.session.commit()

        extrato_id = extrato.id
        lancamento_450_id = lancamento_450.id
        lancamento_540_id = lancamento_540.id
        conta_id = conta.id

        # ----------------------------------------------------
        # EXECUCAO PELO ADAPTADOR REAL
        # ----------------------------------------------------

        resultado = executar_conciliacao_bancaria(
            extrato_id=extrato_id,
            alocacoes=[
                SolicitacaoAlocacao(
                    lancamento_id=lancamento_450_id,
                    valor=Decimal("450.00"),
                ),
                SolicitacaoAlocacao(
                    lancamento_id=lancamento_540_id,
                    valor=Decimal("540.00"),
                ),
            ],
            usuario="D25F01-A2.4",
            observacoes=(
                "Homologacao isolada dos models reais - MR Jacky"
            ),
        )

        db.session.expire_all()

        # ----------------------------------------------------
        # VALIDACAO DIRETA NO ORM REAL
        # ----------------------------------------------------

        itens = (
            db.session.query(ConciliacaoBancariaItem)
            .filter(
                ConciliacaoBancariaItem.extrato_id == extrato_id,
                ConciliacaoBancariaItem.ativo.is_(True),
            )
            .order_by(ConciliacaoBancariaItem.lancamento_id)
            .all()
        )

        extrato_db = db.session.get(
            ExtratoBancario,
            extrato_id,
        )

        lancamento_450_db = db.session.get(
            LancamentoFinanceiro,
            lancamento_450_id,
        )

        lancamento_540_db = db.session.get(
            LancamentoFinanceiro,
            lancamento_540_id,
        )

        conta_db = db.session.get(
            ContaBancaria,
            conta_id,
        )

        total_conciliado = sum(
            (
                Decimal(str(item.valor_conciliado))
                for item in itens
            ),
            Decimal("0.00"),
        )

        valores_por_lancamento = {
            item.lancamento_id: Decimal(
                str(item.valor_conciliado)
            )
            for item in itens
        }

        assert len(itens) == 2

        assert valores_por_lancamento == {
            lancamento_450_id: Decimal("450.00"),
            lancamento_540_id: Decimal("540.00"),
        }

        assert total_conciliado == Decimal("990.00")

        assert extrato_db.conciliado is True
        assert extrato_db.data_conciliacao is not None

        # N:N nao deve preencher o FK legado 1:1.
        assert extrato_db.lancamento_id is None

        # A conciliacao NAO quita automaticamente o lancamento.
        assert lancamento_450_db.status == "pendente"
        assert lancamento_540_db.status == "pendente"

        # A conciliacao NAO deve movimentar saldo bancario.
        assert Decimal(str(conta_db.saldo_atual)) == Decimal("0.00")

        print(f"Itens persistidos: {len(itens)}")
        print(f"Total conciliado:   R$ {total_conciliado}")
        print(f"Extrato conciliado: {extrato_db.conciliado}")
        print(
            "FK legado:           "
            f"{extrato_db.lancamento_id}"
        )
        print(
            "Status lancamentos:  "
            f"{lancamento_450_db.status} / "
            f"{lancamento_540_db.status}"
        )
        print(
            "Saldo da conta:      "
            f"R$ {Decimal(str(conta_db.saldo_atual))}"
        )

        print(
            "Resultado service:   "
            f"{type(resultado).__name__}"
        )

        db.session.remove()

    hash_erp_depois = sha256_arquivo(ERP_DB)

    assert hash_erp_antes == hash_erp_depois, (
        "ERRO: erp.db foi alterado durante o teste A2.4."
    )

    print()
    print("SHA-256 erp.db preservado:")
    print(hash_erp_depois or "<erp.db ausente>")
    print()
    print("D25F01-A2.4 HOMOLOGADO ✅")


if __name__ == "__main__":
    executar_teste()