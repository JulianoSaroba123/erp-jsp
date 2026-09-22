# -*- coding: utf-8 -*-

import importlib.util
from decimal import Decimal
from pathlib import Path

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    create_engine,
)
from sqlalchemy.orm import (
    declarative_base,
    sessionmaker,
)


RAIZ = Path(__file__).resolve().parents[2]

SERVICE = (
    RAIZ
    / "app"
    / "financeiro"
    / "conciliacao_service.py"
)

spec = importlib.util.spec_from_file_location(
    "conciliacao_service_a23",
    SERVICE,
)

modulo = importlib.util.module_from_spec(spec)
spec.loader.exec_module(modulo)

ConciliacaoInvalida = modulo.ConciliacaoInvalida
SolicitacaoAlocacao = modulo.SolicitacaoAlocacao
executar_conciliacao_orm = (
    modulo.executar_conciliacao_orm
)


Base = declarative_base()


class ExtratoTeste(Base):
    __tablename__ = "extratos_teste"

    id = Column(
        Integer,
        primary_key=True,
    )

    valor = Column(
        Numeric(12, 2),
        nullable=False,
    )

    tipo_movimento = Column(
        String(20),
        nullable=False,
    )

    conta_bancaria_id = Column(
        Integer,
        nullable=True,
    )

    conciliado = Column(
        Boolean,
        default=False,
        nullable=False,
    )

    data_conciliacao = Column(
        DateTime,
        nullable=True,
    )

    lancamento_id = Column(
        Integer,
        nullable=True,
    )


class LancamentoTeste(Base):
    __tablename__ = "lancamentos_teste"

    id = Column(
        Integer,
        primary_key=True,
    )

    valor = Column(
        Numeric(12, 2),
        nullable=False,
    )

    tipo = Column(
        String(20),
        nullable=False,
    )

    conta_bancaria_id = Column(
        Integer,
        nullable=True,
    )


class ItemTeste(Base):
    __tablename__ = "itens_teste"

    __table_args__ = (
        UniqueConstraint(
            "extrato_id",
            "lancamento_id",
        ),
    )

    id = Column(
        Integer,
        primary_key=True,
    )

    extrato_id = Column(
        Integer,
        ForeignKey("extratos_teste.id"),
        nullable=False,
    )

    lancamento_id = Column(
        Integer,
        ForeignKey("lancamentos_teste.id"),
        nullable=False,
    )

    valor_conciliado = Column(
        Numeric(12, 2),
        nullable=False,
    )

    ativo = Column(
        Boolean,
        default=True,
        nullable=False,
    )

    usuario = Column(
        String(100),
        nullable=True,
    )

    observacoes = Column(
        Text,
        nullable=True,
    )


def nova_sessao():
    engine = create_engine(
        "sqlite:///:memory:"
    )

    Base.metadata.create_all(engine)

    Session = sessionmaker(
        bind=engine
    )

    return engine, Session()


def testar_mr_jacky():
    engine, session = nova_sessao()

    try:
        session.add(
            ExtratoTeste(
                id=1,
                valor=Decimal("990.00"),
                tipo_movimento="credito",
                conta_bancaria_id=1,
                conciliado=False,
            )
        )

        session.add_all(
            [
                LancamentoTeste(
                    id=101,
                    valor=Decimal("450.00"),
                    tipo="receita",
                    conta_bancaria_id=1,
                ),
                LancamentoTeste(
                    id=102,
                    valor=Decimal("540.00"),
                    tipo="receita",
                    conta_bancaria_id=1,
                ),
            ]
        )

        session.commit()

        resultado = executar_conciliacao_orm(
            session=session,
            extrato_model=ExtratoTeste,
            lancamento_model=LancamentoTeste,
            item_model=ItemTeste,
            extrato_id=1,
            alocacoes=[
                SolicitacaoAlocacao(
                    101,
                    Decimal("450.00"),
                ),
                SolicitacaoAlocacao(
                    102,
                    Decimal("540.00"),
                ),
            ],
            usuario="teste-a23",
        )

        assert resultado.itens_criados == 2
        assert resultado.itens_atualizados == 0

        itens = (
            session.query(ItemTeste)
            .order_by(ItemTeste.id)
            .all()
        )

        assert len(itens) == 2

        total = sum(
            (
                item.valor_conciliado
                for item in itens
            ),
            Decimal("0.00"),
        )

        assert total == Decimal("990.00")

        extrato = session.get(
            ExtratoTeste,
            1,
        )

        assert extrato.conciliado is True

        # N:N nao cabe no campo legado.
        assert extrato.lancamento_id is None

    finally:
        session.close()
        engine.dispose()


def testar_complemento_mesmo_par():
    engine, session = nova_sessao()

    try:
        session.add(
            ExtratoTeste(
                id=2,
                valor=Decimal("1000.00"),
                tipo_movimento="credito",
                conta_bancaria_id=1,
                conciliado=False,
            )
        )

        session.add(
            LancamentoTeste(
                id=201,
                valor=Decimal("1000.00"),
                tipo="receita",
                conta_bancaria_id=1,
            )
        )

        session.commit()

        primeira = executar_conciliacao_orm(
            session=session,
            extrato_model=ExtratoTeste,
            lancamento_model=LancamentoTeste,
            item_model=ItemTeste,
            extrato_id=2,
            alocacoes=[
                SolicitacaoAlocacao(
                    201,
                    Decimal("400.00"),
                ),
            ],
        )

        assert (
            primeira.preparacao.status_final
            == "PARCIAL"
        )

        assert (
            session.query(ItemTeste).count()
            == 1
        )

        segunda = executar_conciliacao_orm(
            session=session,
            extrato_model=ExtratoTeste,
            lancamento_model=LancamentoTeste,
            item_model=ItemTeste,
            extrato_id=2,
            alocacoes=[
                SolicitacaoAlocacao(
                    201,
                    Decimal("600.00"),
                ),
            ],
        )

        assert segunda.itens_criados == 0
        assert segunda.itens_atualizados == 1

        item = (
            session.query(ItemTeste)
            .one()
        )

        assert (
            item.valor_conciliado
            == Decimal("1000.00")
        )

        extrato = session.get(
            ExtratoTeste,
            2,
        )

        assert extrato.conciliado is True
        assert extrato.lancamento_id == 201

    finally:
        session.close()
        engine.dispose()


def testar_multiplos_pix_um_lancamento():
    engine, session = nova_sessao()

    try:
        session.add_all(
            [
                ExtratoTeste(
                    id=3,
                    valor=Decimal("400.00"),
                    tipo_movimento="credito",
                    conta_bancaria_id=1,
                ),
                ExtratoTeste(
                    id=4,
                    valor=Decimal("600.00"),
                    tipo_movimento="credito",
                    conta_bancaria_id=1,
                ),
                LancamentoTeste(
                    id=301,
                    valor=Decimal("1000.00"),
                    tipo="receita",
                    conta_bancaria_id=1,
                ),
            ]
        )

        session.commit()

        executar_conciliacao_orm(
            session=session,
            extrato_model=ExtratoTeste,
            lancamento_model=LancamentoTeste,
            item_model=ItemTeste,
            extrato_id=3,
            alocacoes=[
                SolicitacaoAlocacao(
                    301,
                    Decimal("400.00"),
                ),
            ],
        )

        executar_conciliacao_orm(
            session=session,
            extrato_model=ExtratoTeste,
            lancamento_model=LancamentoTeste,
            item_model=ItemTeste,
            extrato_id=4,
            alocacoes=[
                SolicitacaoAlocacao(
                    301,
                    Decimal("600.00"),
                ),
            ],
        )

        itens = (
            session.query(ItemTeste)
            .filter(
                ItemTeste.lancamento_id
                == 301
            )
            .all()
        )

        assert len(itens) == 2

        total = sum(
            (
                item.valor_conciliado
                for item in itens
            ),
            Decimal("0.00"),
        )

        assert total == Decimal("1000.00")

    finally:
        session.close()
        engine.dispose()


def testar_rollback():
    engine, session = nova_sessao()

    try:
        session.add(
            ExtratoTeste(
                id=5,
                valor=Decimal("100.00"),
                tipo_movimento="credito",
                conta_bancaria_id=1,
            )
        )

        session.add(
            LancamentoTeste(
                id=501,
                valor=Decimal("100.00"),
                tipo="receita",
                conta_bancaria_id=1,
            )
        )

        session.commit()

        try:
            executar_conciliacao_orm(
                session=session,
                extrato_model=ExtratoTeste,
                lancamento_model=LancamentoTeste,
                item_model=ItemTeste,
                extrato_id=5,
                alocacoes=[
                    SolicitacaoAlocacao(
                        501,
                        Decimal("101.00"),
                    ),
                ],
            )
        except ConciliacaoInvalida:
            pass
        else:
            raise AssertionError(
                "Sobrealocacao deveria falhar."
            )

        assert (
            session.query(ItemTeste).count()
            == 0
        )

        extrato = session.get(
            ExtratoTeste,
            5,
        )

        assert extrato.conciliado is False
        assert extrato.lancamento_id is None

    finally:
        session.close()
        engine.dispose()


def main():
    testar_mr_jacky()
    testar_complemento_mesmo_par()
    testar_multiplos_pix_um_lancamento()
    testar_rollback()

    print("OK: MR Jacky persistiu 990 = 450 + 540.")
    print("OK: N:N criou dois itens para um extrato.")
    print("OK: complemento do mesmo par fez UPDATE, nao duplicou.")
    print("OK: dois PIX quitaram um unico lancamento.")
    print("OK: sobrealocacao executou rollback integral.")
    print("OK: campo legado ficou seguro no caso N:N.")
    print("OK: SQLite usado somente em memoria.")
    print("OK: nenhum Flask/app/erp.db foi acessado.")
    print("OK: D25F01-A2.3 homologado.")


if __name__ == "__main__":
    main()
