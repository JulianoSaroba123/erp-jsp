# -*- coding: utf-8 -*-

from __future__ import annotations

from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest
from sqlalchemy.exc import IntegrityError


@pytest.fixture()
def app_ctx():
    from app import create_app
    from app.extensoes import db

    app = create_app("testing")

    with app.app_context():
        from app.auth.usuario_model import Usuario  # noqa: F401
        from app.cliente.cliente_model import Cliente  # noqa: F401
        from app.financeiro.financeiro_model import ContaBancaria, HistoricoFinanceiro, LancamentoFinanceiro  # noqa: F401
        from app.fornecedor.fornecedor_model import Fornecedor  # noqa: F401
        from app.ordem_servico.ordem_servico_model import OrdemServico  # noqa: F401
        from app.pedido.pedido_model import Pedido  # noqa: F401
        from app.pedido_compra.pedido_compra_model import PedidoCompra, PedidoCompraItem  # noqa: F401
        from app.produto.produto_model import Produto  # noqa: F401
        from app.proposta.proposta_model import Proposta  # noqa: F401
        from app.servico.servico_model import Servico  # noqa: F401

        db.drop_all()
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


def _seed_user(db, tipo_usuario: str, username: str):
    from app.auth.usuario_model import Usuario

    usuario = Usuario(
        nome=f"Usuario {tipo_usuario}",
        email=f"{username}@teste.local",
        usuario=username,
        tipo_usuario=tipo_usuario,
        ativo=True,
        email_confirmado=True,
        primeiro_login=False,
    )
    usuario.set_senha("123456")
    db.session.add(usuario)
    db.session.commit()
    return usuario


def _autenticar(client, usuario):
    response = client.post(
        "/auth/login",
        data={"identificador": usuario.usuario, "senha": "123456"},
        follow_redirects=False,
    )
    assert response.status_code == 302


def _seed_base_compra(db):
    from app.cliente.cliente_model import Cliente
    from app.fornecedor.fornecedor_model import Fornecedor
    from app.ordem_servico.ordem_servico_model import OrdemServico
    from app.pedido.pedido_model import Pedido
    from app.produto.produto_model import Produto
    from app.proposta.proposta_model import Proposta
    from app.servico.servico_model import Servico

    cliente = Cliente(nome="Cliente Fluxo", tipo="PF", cpf_cnpj="44455566677")
    db.session.add(cliente)
    db.session.flush()

    fornecedor = Fornecedor(nome="Fornecedor Teste")
    produto = Produto(
        nome="Produto Compra",
        preco_custo=Decimal("100.00"),
        preco_venda=Decimal("150.00"),
        unidade_medida="UN",
        estoque_atual=10,
    )
    servico = Servico(nome="Servico Compra", valor_base=Decimal("500.00"), tipo_cobranca="servico")
    proposta = Proposta(cliente_id=cliente.id, titulo="Proposta Compra", status="aprovada", valor_total=Decimal("500.00"))
    pedido_venda = Pedido(cliente_id=cliente.id, proposta_id=None)
    ordem = OrdemServico(numero="OS0001", titulo="OS Teste Compra", cliente_id=cliente.id, data_abertura=date.today())

    db.session.add_all([fornecedor, produto, servico, proposta, pedido_venda, ordem])
    db.session.commit()
    return fornecedor, produto, servico, ordem, pedido_venda


def _post_data(fornecedor, produto, servico, ordem, pedido_venda, **overrides):
    data = {
        "fornecedor_id": str(fornecedor.id),
        "data_emissao": "2026-09-01",
        "previsao_entrega": "2026-09-15",
        "status": "APROVADO",
        "finalidade": "PEDIDO_VENDA",
        "solicitante": "Compras",
        "responsavel_compra": "Maria",
        "condicao_pagamento": "15 dias",
        "desconto": "0,00",
        "ordem_servico_id": str(ordem.id),
        "pedido_venda_id": str(pedido_venda.id),
        "item_id[]": ["", ""],
        "item_tipo[]": ["PRODUTO", "SERVICO"],
        "item_referencia_id[]": [f"P:{produto.id}", f"S:{servico.id}"],
        "item_descricao[]": ["Produto Compra", "Servico Compra"],
        "item_unidade[]": ["UN", "SV"],
        "item_quantidade[]": ["2", "1"],
        "item_valor_unitario[]": ["100,00", "500,00"],
        "item_desconto[]": ["0", "0"],
    }
    data.update(overrides)
    return data


def _criar_pedido(client, fornecedor, produto, servico, ordem, pedido_venda, **overrides):
    payload = _post_data(fornecedor, produto, servico, ordem, pedido_venda, **overrides)
    response = client.post("/pedido-compra/novo", data=payload, follow_redirects=True)
    assert response.status_code == 200


def _fingerprint_erp_db() -> str:
    import hashlib

    root = Path(__file__).resolve().parents[1]
    db_path = root / "erp.db"
    if not db_path.exists():
        return "erp.db:not-found"

    payload = db_path.read_bytes()
    return f"{len(payload)}|{hashlib.sha256(payload).hexdigest()}"


def test_01_pedido_valido_gera_conta_a_pagar(app_ctx):
    from app.extensoes import db
    from app.financeiro.financeiro_model import LancamentoFinanceiro

    usuario = _seed_user(db, "usuario", "usuario_pc_01")
    fornecedor, produto, servico, ordem, pedido_venda = _seed_base_compra(db)
    client = app_ctx.test_client()
    _autenticar(client, usuario)

    _criar_pedido(client, fornecedor, produto, servico, ordem, pedido_venda)

    lanc = LancamentoFinanceiro.query.filter_by(origem="PEDIDO_COMPRA").one()
    assert lanc.tipo == "conta_pagar"


def test_02_fornecedor_e_vinculado_corretamente(app_ctx):
    from app.extensoes import db
    from app.financeiro.financeiro_model import LancamentoFinanceiro

    usuario = _seed_user(db, "usuario", "usuario_pc_02")
    fornecedor, produto, servico, ordem, pedido_venda = _seed_base_compra(db)
    client = app_ctx.test_client()
    _autenticar(client, usuario)

    _criar_pedido(client, fornecedor, produto, servico, ordem, pedido_venda)

    lanc = LancamentoFinanceiro.query.filter_by(origem="PEDIDO_COMPRA").one()
    assert lanc.fornecedor_id == fornecedor.id


def test_03_valor_corresponde_total_real_pedido(app_ctx):
    from app.extensoes import db
    from app.financeiro.financeiro_model import LancamentoFinanceiro
    from app.pedido_compra.pedido_compra_model import PedidoCompra

    usuario = _seed_user(db, "usuario", "usuario_pc_03")
    fornecedor, produto, servico, ordem, pedido_venda = _seed_base_compra(db)
    client = app_ctx.test_client()
    _autenticar(client, usuario)

    _criar_pedido(client, fornecedor, produto, servico, ordem, pedido_venda)

    pedido = PedidoCompra.query.one()
    lanc = LancamentoFinanceiro.query.filter_by(origem="PEDIDO_COMPRA").one()
    assert Decimal(str(lanc.valor)) == Decimal(str(pedido.total))


def test_04_origem_canonica_pedido_compra(app_ctx):
    from app.extensoes import db
    from app.financeiro.financeiro_model import LancamentoFinanceiro

    usuario = _seed_user(db, "usuario", "usuario_pc_04")
    fornecedor, produto, servico, ordem, pedido_venda = _seed_base_compra(db)
    client = app_ctx.test_client()
    _autenticar(client, usuario)

    _criar_pedido(client, fornecedor, produto, servico, ordem, pedido_venda)

    lanc = LancamentoFinanceiro.query.one()
    assert lanc.origem == "PEDIDO_COMPRA"


def test_05_lancamento_inicia_pendente(app_ctx):
    from app.extensoes import db
    from app.financeiro.financeiro_model import LancamentoFinanceiro

    usuario = _seed_user(db, "usuario", "usuario_pc_05")
    fornecedor, produto, servico, ordem, pedido_venda = _seed_base_compra(db)
    client = app_ctx.test_client()
    _autenticar(client, usuario)

    _criar_pedido(client, fornecedor, produto, servico, ordem, pedido_venda)

    lanc = LancamentoFinanceiro.query.one()
    assert lanc.status == "pendente"
    assert lanc.data_pagamento is None


def test_06_criacao_nao_movimenta_caixa(app_ctx):
    from app.extensoes import db
    from app.financeiro.financeiro_model import ContaBancaria

    usuario = _seed_user(db, "usuario", "usuario_pc_06")
    fornecedor, produto, servico, ordem, pedido_venda = _seed_base_compra(db)
    conta = ContaBancaria(nome="Conta Teste", tipo="conta_corrente", saldo_inicial=Decimal("10000.00"), saldo_atual=Decimal("10000.00"))
    db.session.add(conta)
    db.session.commit()

    saldo_antes = Decimal(str(conta.saldo_atual))

    client = app_ctx.test_client()
    _autenticar(client, usuario)
    _criar_pedido(client, fornecedor, produto, servico, ordem, pedido_venda)

    db.session.refresh(conta)
    assert Decimal(str(conta.saldo_atual)) == saldo_antes


def test_07_segunda_execucao_nao_duplica_lancamento(app_ctx):
    from app.extensoes import db
    from app.financeiro.financeiro_model import LancamentoFinanceiro
    from app.pedido_compra.pedido_compra_financeiro_service import sincronizar_obrigacao_financeira_pedido_compra
    from app.pedido_compra.pedido_compra_model import PedidoCompra

    usuario = _seed_user(db, "usuario", "usuario_pc_07")
    fornecedor, produto, servico, ordem, pedido_venda = _seed_base_compra(db)
    client = app_ctx.test_client()
    _autenticar(client, usuario)
    _criar_pedido(client, fornecedor, produto, servico, ordem, pedido_venda)

    pedido = PedidoCompra.query.one()
    sincronizar_obrigacao_financeira_pedido_compra(pedido, usuario="usuario_pc_07")
    db.session.commit()

    assert LancamentoFinanceiro.query.filter_by(pedido_compra_id=pedido.id).count() == 1


def test_08_cancelado_antes_pagamento_inativa_obrigacao(app_ctx):
    from app.extensoes import db
    from app.financeiro.financeiro_model import LancamentoFinanceiro
    from app.pedido_compra.pedido_compra_model import PedidoCompra

    usuario = _seed_user(db, "usuario", "usuario_pc_08")
    fornecedor, produto, servico, ordem, pedido_venda = _seed_base_compra(db)
    client = app_ctx.test_client()
    _autenticar(client, usuario)
    _criar_pedido(client, fornecedor, produto, servico, ordem, pedido_venda)

    pedido = PedidoCompra.query.one()
    response = client.post(f"/pedido-compra/{pedido.id}/cancelar", follow_redirects=True)
    assert response.status_code == 200

    lanc = LancamentoFinanceiro.query.filter_by(pedido_compra_id=pedido.id).one()
    assert lanc.status == "cancelado"
    assert lanc.ativo is False


def test_09_recebimento_nao_significa_pago(app_ctx):
    from app.extensoes import db
    from app.financeiro.financeiro_model import LancamentoFinanceiro
    from app.pedido_compra.pedido_compra_model import PedidoCompra

    usuario = _seed_user(db, "usuario", "usuario_pc_09")
    fornecedor, produto, servico, ordem, pedido_venda = _seed_base_compra(db)
    client = app_ctx.test_client()
    _autenticar(client, usuario)
    _criar_pedido(client, fornecedor, produto, servico, ordem, pedido_venda)

    pedido = PedidoCompra.query.one()
    response = client.post(
        f"/pedido-compra/{pedido.id}/recebimento",
        data={"item_quantidade_receber[]": ["2", "1"]},
        follow_redirects=True,
    )
    assert response.status_code == 200

    lanc = LancamentoFinanceiro.query.filter_by(pedido_compra_id=pedido.id).one()
    assert lanc.status == "pendente"
    assert lanc.data_pagamento is None


def test_10_baixa_movimenta_caixa_uma_unica_vez(app_ctx):
    from app.extensoes import db
    from app.financeiro.financeiro_model import ContaBancaria, LancamentoFinanceiro

    usuario = _seed_user(db, "usuario", "usuario_pc_10")
    fornecedor, produto, servico, ordem, pedido_venda = _seed_base_compra(db)
    conta = ContaBancaria(nome="Conta Caixa", tipo="conta_corrente", saldo_inicial=Decimal("10000.00"), saldo_atual=Decimal("10000.00"))
    db.session.add(conta)
    db.session.commit()

    client = app_ctx.test_client()
    _autenticar(client, usuario)
    _criar_pedido(client, fornecedor, produto, servico, ordem, pedido_venda)

    lanc = LancamentoFinanceiro.query.filter_by(origem="PEDIDO_COMPRA").one()
    lanc.conta_bancaria_id = conta.id
    db.session.commit()

    lanc.marcar_como_pago(data_pagamento=date(2026, 9, 15), usuario="usuario_pc_10")
    db.session.refresh(conta)
    saldo_apos_primeira_baixa = Decimal(str(conta.saldo_atual))

    lanc.marcar_como_pago(data_pagamento=date(2026, 9, 15), usuario="usuario_pc_10")
    db.session.refresh(conta)

    assert saldo_apos_primeira_baixa == Decimal("9300.00")
    assert Decimal(str(conta.saldo_atual)) == Decimal("9300.00")


def test_11_pedido_pago_nao_e_reescrito_por_sincronizacao(app_ctx):
    from app.extensoes import db
    from app.financeiro.financeiro_model import HistoricoFinanceiro, LancamentoFinanceiro
    from app.pedido_compra.pedido_compra_financeiro_service import sincronizar_obrigacao_financeira_pedido_compra
    from app.pedido_compra.pedido_compra_model import PedidoCompra

    usuario = _seed_user(db, "usuario", "usuario_pc_11")
    fornecedor, produto, servico, ordem, pedido_venda = _seed_base_compra(db)
    client = app_ctx.test_client()
    _autenticar(client, usuario)
    _criar_pedido(client, fornecedor, produto, servico, ordem, pedido_venda)

    pedido = PedidoCompra.query.one()
    lanc = LancamentoFinanceiro.query.filter_by(pedido_compra_id=pedido.id).one()
    lanc.marcar_como_pago(data_pagamento=date(2026, 9, 15), usuario="usuario_pc_11")

    valor_quitado = Decimal(str(lanc.valor))

    pedido.desconto = Decimal("10.00")
    pedido.recalcular_totais()
    sincronizar_obrigacao_financeira_pedido_compra(pedido, usuario="usuario_pc_11")
    db.session.commit()

    db.session.refresh(lanc)
    assert Decimal(str(lanc.valor)) == valor_quitado
    historicos = HistoricoFinanceiro.query.filter_by(lancamento_id=lanc.id).all()
    assert any("Sincronizacao automatica bloqueada" in (h.motivo or "") for h in historicos)


def test_12_conta_aparece_em_contas_a_pagar(app_ctx):
    from app.extensoes import db
    from app.financeiro.financeiro_model import LancamentoFinanceiro

    usuario = _seed_user(db, "usuario", "usuario_pc_12")
    fornecedor, produto, servico, ordem, pedido_venda = _seed_base_compra(db)
    client = app_ctx.test_client()
    _autenticar(client, usuario)
    _criar_pedido(client, fornecedor, produto, servico, ordem, pedido_venda)

    lanc = LancamentoFinanceiro.query.filter_by(origem="PEDIDO_COMPRA").one()
    assert LancamentoFinanceiro.get_contas_pagar().filter_by(id=lanc.id).count() == 1


def test_13_conta_entra_no_projetado_por_vencimento(app_ctx):
    from app.extensoes import db
    from app.financeiro.indicadores_service import resumir_financeiro_periodo

    usuario = _seed_user(db, "usuario", "usuario_pc_13")
    fornecedor, produto, servico, ordem, pedido_venda = _seed_base_compra(db)
    client = app_ctx.test_client()
    _autenticar(client, usuario)
    _criar_pedido(client, fornecedor, produto, servico, ordem, pedido_venda)

    resumo = resumir_financeiro_periodo(date(2026, 9, 1), date(2026, 9, 30))
    assert resumo.contas_a_pagar_pendentes == Decimal("700.00")


def test_14_conta_nao_entra_em_despesa_realizada_antes_baixa(app_ctx):
    from app.extensoes import db
    from app.financeiro.indicadores_service import resumir_financeiro_periodo

    usuario = _seed_user(db, "usuario", "usuario_pc_14")
    fornecedor, produto, servico, ordem, pedido_venda = _seed_base_compra(db)
    client = app_ctx.test_client()
    _autenticar(client, usuario)
    _criar_pedido(client, fornecedor, produto, servico, ordem, pedido_venda)

    resumo = resumir_financeiro_periodo(date(2026, 9, 1), date(2026, 9, 30))
    assert resumo.despesas_realizadas == Decimal("0")


def test_15_baixa_faz_entrar_em_despesa_realizada_por_data_pagamento(app_ctx):
    from app.extensoes import db
    from app.financeiro.financeiro_model import LancamentoFinanceiro
    from app.financeiro.indicadores_service import resumir_financeiro_periodo

    usuario = _seed_user(db, "usuario", "usuario_pc_15")
    fornecedor, produto, servico, ordem, pedido_venda = _seed_base_compra(db)
    client = app_ctx.test_client()
    _autenticar(client, usuario)
    _criar_pedido(client, fornecedor, produto, servico, ordem, pedido_venda)

    lanc = LancamentoFinanceiro.query.filter_by(origem="PEDIDO_COMPRA").one()
    lanc.marcar_como_pago(data_pagamento=date(2026, 9, 15), usuario="usuario_pc_15")

    resumo = resumir_financeiro_periodo(date(2026, 9, 1), date(2026, 9, 30))
    assert resumo.despesas_realizadas == Decimal("700.00")


def test_16_erp_db_permanece_intacto_durante_teste(app_ctx):
    from app.extensoes import db

    before = _fingerprint_erp_db()

    usuario = _seed_user(db, "usuario", "usuario_pc_16")
    fornecedor, produto, servico, ordem, pedido_venda = _seed_base_compra(db)
    client = app_ctx.test_client()
    _autenticar(client, usuario)
    _criar_pedido(client, fornecedor, produto, servico, ordem, pedido_venda)

    after = _fingerprint_erp_db()
    assert before == after


def test_17_cenario_pratico_fluxo_completo(app_ctx):
    from app.extensoes import db
    from app.financeiro.financeiro_model import ContaBancaria, LancamentoFinanceiro
    from app.pedido_compra.pedido_compra_model import PedidoCompra

    usuario = _seed_user(db, "usuario", "usuario_pc_17")
    fornecedor, produto, servico, ordem, pedido_venda = _seed_base_compra(db)
    conta = ContaBancaria(nome="Banco Teste", tipo="conta_corrente", saldo_inicial=Decimal("10000.00"), saldo_atual=Decimal("10000.00"))
    db.session.add(conta)
    db.session.commit()

    client = app_ctx.test_client()
    _autenticar(client, usuario)

    _criar_pedido(
        client,
        fornecedor,
        produto,
        servico,
        ordem,
        pedido_venda,
        previsao_entrega="2026-09-15",
        item_quantidade=["20", "1"],
        item_valor_unitario=["100,00", "500,00"],
    )

    pedido = PedidoCompra.query.one()
    pedido.total = Decimal("2500.00")
    from app.pedido_compra.pedido_compra_financeiro_service import sincronizar_obrigacao_financeira_pedido_compra

    sincronizar_obrigacao_financeira_pedido_compra(pedido, usuario="usuario_pc_17")
    db.session.commit()

    lanc = LancamentoFinanceiro.query.filter_by(pedido_compra_id=pedido.id).one()
    assert Decimal(str(lanc.valor)) == Decimal("2500.00")
    assert lanc.status == "pendente"
    assert lanc.fornecedor_id == fornecedor.id
    assert lanc.data_vencimento == date(2026, 9, 15)
    assert lanc.origem == "PEDIDO_COMPRA"

    db.session.refresh(conta)
    assert Decimal(str(conta.saldo_atual)) == Decimal("10000.00")

    lanc.conta_bancaria_id = conta.id
    db.session.commit()

    lanc.marcar_como_pago(data_pagamento=date(2026, 9, 15), usuario="usuario_pc_17")
    db.session.refresh(conta)
    assert lanc.status == "pago"
    assert lanc.data_pagamento == date(2026, 9, 15)
    assert Decimal(str(conta.saldo_atual)) == Decimal("7500.00")

    lanc.marcar_como_pago(data_pagamento=date(2026, 9, 15), usuario="usuario_pc_17")
    db.session.refresh(conta)
    assert Decimal(str(conta.saldo_atual)) == Decimal("7500.00")


def test_18_vinculo_unico_pedido_compra_impede_duplicidade(app_ctx):
    from app.extensoes import db
    from app.financeiro.financeiro_model import LancamentoFinanceiro
    from app.pedido_compra.pedido_compra_model import PedidoCompra

    usuario = _seed_user(db, "usuario", "usuario_pc_18")
    fornecedor, produto, servico, ordem, pedido_venda = _seed_base_compra(db)
    client = app_ctx.test_client()
    _autenticar(client, usuario)
    _criar_pedido(client, fornecedor, produto, servico, ordem, pedido_venda)

    pedido = PedidoCompra.query.one()
    duplicado = LancamentoFinanceiro(
        descricao="Duplicado indevido",
        valor=Decimal("1.00"),
        tipo="conta_pagar",
        status="pendente",
        data_lancamento=date(2026, 9, 1),
        data_vencimento=date(2026, 9, 15),
        fornecedor_id=fornecedor.id,
        pedido_compra_id=pedido.id,
        origem="MANUAL",
    )
    db.session.add(duplicado)

    with pytest.raises(IntegrityError):
        db.session.commit()

    db.session.rollback()