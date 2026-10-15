# -*- coding: utf-8 -*-
"""G5-F3: checklists digitais, snapshots, autorização, rascunho, fechamento.

Testes isolados em SQLite em memória, sem bancos externos.
"""
import os
from datetime import date
from pathlib import Path

os.environ["FLASK_ENV"] = "testing"
os.environ["FLASK_CONFIG"] = "testing"
os.environ.pop("DATABASE_URL", None)

import pytest
from app import create_app
from app.extensoes import db
from app.auth.usuario_model import Usuario
from app.cliente.cliente_model import Cliente
from app.ordem_servico.ordem_servico_model import OrdemServico
from app.geradores.gerador_model import Gerador
from app.geradores.gerador_consumivel_model import GeradorConsumivel
from app.geradores.gerador_os_vinculo_service import vincular_gerador_os
from app.geradores.gerador_checklist_catalogo import itens_do_modelo
from app.geradores.gerador_checklist_execucao_model import GeradorChecklistExecucao
from app.geradores.gerador_checklist_execucao_service import (
    ExecucaoChecklistError, criar_checklist, obter_checklist,
    salvar_checklist, listar_checklists_os,
)


@pytest.fixture
def ctx():
    app = create_app("testing")
    assert app.config["SQLALCHEMY_DATABASE_URI"] == "sqlite:///:memory:"
    with app.app_context():
        db.create_all()
        admin = Usuario(
            nome="Admin G5 F3", usuario="admin_g5f3", email="admin_g5f3@example.com",
            tipo_usuario="admin", ativo=True, primeiro_login=False,
            email_confirmado=True,
        )
        admin.set_senha("SenhaTestesG5f3!")
        comum = Usuario(
            nome="Comum G5 F3", usuario="comum_g5f3",
            email="comum_g5f3@example.com",
            tipo_usuario="usuario", ativo=True,
            primeiro_login=False, email_confirmado=True,
        )
        comum.set_senha("SenhaTestesG5f3!")
        cliente_a = Cliente(nome="Cliente de teste G5F3", tipo="PJ",
                            cpf_cnpj="55111999000155", ativo=True)
        cliente_b = Cliente(nome="Outro cliente G5F3", tipo="PJ",
                            cpf_cnpj="55222999000166", ativo=True)
        db.session.add_all([admin, comum, cliente_a, cliente_b])
        db.session.commit()

        os_a = OrdemServico(
            numero="OSG5F30001", titulo="Preventiva 2 geradores",
            cliente_id=cliente_a.id, status="pendente", ativo=True,
            valor_total=7300,
        )
        gerador_a = Gerador(
            codigo="GER-G5-F3-A", cliente_id=cliente_a.id,
            fabricante_grupo="MWM", modelo="Exemplo",
            numero_serie="SN-G5F3-001",
            status="ATIVO", ativo=True,
        )
        gerador_b = Gerador(
            codigo="GER-G5-F3-B", cliente_id=cliente_a.id,
            fabricante_grupo="FPT", modelo="Exemplo B",
            status="ATIVO", ativo=True,
        )
        estranho = Gerador(
            codigo="GER-G5-F3-C", cliente_id=cliente_b.id,
            status="ATIVO", ativo=True,
        )
        db.session.add_all([os_a, gerador_a, gerador_b, estranho])
        db.session.commit()
        db.session.add(GeradorConsumivel(
            gerador_id=gerador_a.id, tipo="FILTRO_OLEO",
            fabricante_original="FPT", referencia_original="REF-TESTE",
            quantidade=1, unidade="un", ativo=True,
        ))
        db.session.commit()
        v1, _ = vincular_gerador_os(
            os_a.id, gerador_a.id, usuario_id=admin.id,
        )
        v2, _ = vincular_gerador_os(
            os_a.id, gerador_b.id, usuario_id=admin.id,
        )
        db.session.commit()
        ids = {
            "os": os_a.id, "g1": gerador_a.id, "g2": gerador_b.id,
            "v1": v1.id, "v2": v2.id, "admin": admin.id,
            "comum": comum.id, "estranho": estranho.id,
        }
        yield app, ids
        db.session.remove()
        db.drop_all()


def resposta_para(tipo, *, modo="CONFORME"):
    return {
        chave: {
            "status": modo,
            "medicao": "12,5" if item["unidade"] and modo == "CONFORME" else "",
            "observacao": "Justificativa de teste" if modo != "CONFORME" else "",
        }
        for chave, item in itens_do_modelo(tipo).items()
    }


def login(client, usuario="admin_g5f3"):
    r = client.post("/auth/login", data={
        "identificador": usuario, "senha": "SenhaTestesG5f3!",
    })
    assert r.status_code == 302


def token(client, os_id):
    with client.session_transaction() as sess:
        # Token é gerado pelo GET de listagem para sessões válidas.
        pass
    response = client.get(f"/geradores/checklists/os/{os_id}")
    assert response.status_code == 200
    with client.session_transaction() as sess:
        return sess["_csrf_geradores_g5_f3"]


def test_iniciar_snapshot_versao_e_consumivel(ctx):
    _, ids = ctx
    execucao, criado = criar_checklist(
        ids["v1"], "INTERMEDIARIA", usuario_id=ids["admin"],
    )
    assert criado is True
    assert execucao.versao_catalogo == "G5-1.0"
    assert execucao.estado == "RASCUNHO"
    assert execucao.identificacao_snapshot["os"]["numero"] == "OSG5F30001"
    assert execucao.identificacao_snapshot["gerador"]["numero_serie"] == "SN-G5F3-001"
    assert execucao.identificacao_snapshot["consumiveis"][0]["referencia"] == "REF-TESTE"
    assert execucao.respostas_snapshot["apto_para_encerramento"] is False


def test_iniciar_mesma_os_e_plano_nao_duplica(ctx):
    _, ids = ctx
    a, primeira = criar_checklist(ids["v1"], "BASICA", usuario_id=ids["admin"])
    b, segunda = criar_checklist(ids["v1"], "BASICA", usuario_id=ids["admin"])
    assert primeira and not segunda
    assert a.id == b.id
    assert GeradorChecklistExecucao.query.count() == 1


def test_do_is_geradores_criam_execucoes_independentes(ctx):
    _, ids = ctx
    a, _ = criar_checklist(ids["v1"], "INTERMEDIARIA", usuario_id=ids["admin"])
    b, _ = criar_checklist(ids["v2"], "INTERMEDIARIA", usuario_id=ids["admin"])
    assert a.id != b.id
    assert a.identificacao_snapshot["gerador"]["codigo"] != b.identificacao_snapshot["gerador"]["codigo"]
    assert len(listar_checklists_os(ids["os"])) == 2


def test_snapshot_nao_muda_apos_atualizacao_do_gerador(ctx):
    _, ids = ctx
    ex, _ = criar_checklist(ids["v1"], "BASICA", usuario_id=ids["admin"])
    db.session.commit()
    old = ex.identificacao_snapshot["gerador"]["modelo"]
    gerador = db.session.get(Gerador, ids["g1"])
    gerador.modelo = "Novo modelo posterior"
    db.session.commit()
    ex = obter_checklist(ex.id)
    assert ex.identificacao_snapshot["gerador"]["modelo"] == old


def test_salvar_rascunho_incompleto_permitido(ctx):
    _, ids = ctx
    ex, _ = criar_checklist(ids["v1"], "BASICA", usuario_id=ids["admin"])
    salvar_checklist(
        ex.id,
        {"SEG_EPI": {"status": "CONFORME"}},
        usuario_id=ids["admin"],
    )
    db.session.commit()
    linha = next(x for x in ex.respostas_snapshot["respostas"] if x["item_id"] == "SEG_EPI")
    assert linha["status"] == "CONFORME"
    assert ex.estado == "RASCUNHO"


def test_nao_conclui_com_item_sem_resposta(ctx):
    _, ids = ctx
    ex, _ = criar_checklist(ids["v1"], "BASICA", usuario_id=ids["admin"])
    with pytest.raises(ExecucaoChecklistError, match="não avaliado"):
        salvar_checklist(ex.id, {}, usuario_id=ids["admin"], concluir=True)
    db.session.rollback()
    assert db.session.get(GeradorChecklistExecucao, ex.id) is None


def test_conclusao_valida_todos_os_itens(ctx):
    _, ids = ctx
    ex, _ = criar_checklist(ids["v1"], "INTERMEDIARIA", usuario_id=ids["admin"])
    db.session.commit()
    res = salvar_checklist(
        ex.id, resposta_para("INTERMEDIARIA"),
        usuario_id=ids["admin"], concluir=True,
        observacoes_gerais="Serviço executado conforme avaliação humana.",
    )
    db.session.commit()
    assert res.estado == "CONCLUIDO"
    assert res.concluido_em is not None
    assert res.concluido_por_id == ids["admin"]


def test_concluido_e_imutavel(ctx):
    _, ids = ctx
    ex, _ = criar_checklist(ids["v1"], "BASICA", usuario_id=ids["admin"])
    db.session.commit()
    salvar_checklist(
        ex.id, resposta_para("BASICA"),
        usuario_id=ids["admin"], concluir=True,
    )
    db.session.commit()
    with pytest.raises(ExecucaoChecklistError, match="imutável"):
        salvar_checklist(ex.id, {}, usuario_id=ids["admin"])


def test_excecao_nao_conforme_justificada_pode_concluir(ctx):
    _, ids = ctx
    ex, _ = criar_checklist(ids["v1"], "BASICA", usuario_id=ids["admin"])
    r = resposta_para("BASICA")
    r["SEG_EPI"] = {"status": "NAO_CONFORME", "observacao": "Registro para correção."}
    salvar_checklist(ex.id, r, usuario_id=ids["admin"], concluir=True)
    assert ex.estado == "CONCLUIDO"
    assert any(x["status"] == "NAO_CONFORME" for x in ex.respostas_snapshot["respostas"])


def test_medicao_invalida_e_bloqueada(ctx):
    _, ids = ctx
    ex, _ = criar_checklist(ids["v1"], "BASICA", usuario_id=ids["admin"])
    with pytest.raises(ExecucaoChecklistError, match="numérica"):
        salvar_checklist(
            ex.id,
            {"MOT_HORIMETRO": {"status": "CONFORME", "medicao": "1e10000"}},
            usuario_id=ids["admin"],
        )


def test_data_futura_rejeitada(ctx):
    _, ids = ctx
    ex, _ = criar_checklist(ids["v1"], "BASICA", usuario_id=ids["admin"])
    with pytest.raises(ExecucaoChecklistError, match="Data futura"):
        salvar_checklist(
            ex.id, {}, usuario_id=ids["admin"],
            data_servico="2099-01-01",
        )


def test_login_obrigatorio_e_usuario_comum_bloqueado(ctx):
    app, ids = ctx
    client = app.test_client()
    assert client.get(f"/geradores/checklists/os/{ids['os']}").status_code == 302
    login(client, "comum_g5f3")
    assert client.get(f"/geradores/checklists/os/{ids['os']}").status_code == 403
    assert client.post(f"/geradores/checklists/vinculos/{ids['v1']}/iniciar").status_code == 403


def test_tela_admin_listagem_e_formulario(ctx):
    app, ids = ctx
    client = app.test_client()
    login(client)
    response = client.get(f"/geradores/checklists/os/{ids['os']}")
    assert response.status_code == 200
    assert "GER-G5-F3-A" in response.get_data(as_text=True)
    ex, _ = criar_checklist(ids["v1"], "INTERMEDIARIA", usuario_id=ids["admin"])
    db.session.commit()
    tela = client.get(f"/geradores/checklists/{ex.id}")
    assert tela.status_code == 200
    assert "SEG_EPI" in tela.get_data(as_text=True)
    assert "REF-TESTE" in tela.get_data(as_text=True)


def test_csrf_ausente_e_rejeitado(ctx):
    app, ids = ctx
    client = app.test_client()
    login(client)
    response = client.post(
        f"/geradores/checklists/vinculos/{ids['v1']}/iniciar",
        data={"tipo_plano": "BASICA"},
    )
    assert response.status_code == 400
    assert GeradorChecklistExecucao.query.count() == 0


def test_post_iniciar_e_repetir_nao_duplicar(ctx):
    app, ids = ctx
    client = app.test_client()
    login(client)
    csrf = token(client, ids["os"])
    url = f"/geradores/checklists/vinculos/{ids['v1']}/iniciar"
    for _ in range(2):
        resposta = client.post(url, data={
            "csrf_token_g5_f3": csrf, "tipo_plano": "BASICA",
        })
        assert resposta.status_code == 302
    assert GeradorChecklistExecucao.query.count() == 1


def test_post_salvar_rascunho_por_http(ctx):
    app, ids = ctx
    ex, _ = criar_checklist(ids["v1"], "BASICA", usuario_id=ids["admin"])
    db.session.commit()
    client = app.test_client()
    login(client)
    csrf = token(client, ids["os"])
    resposta = client.post(f"/geradores/checklists/{ex.id}/salvar", data={
        "csrf_token_g5_f3": csrf,
        "acao": "salvar",
        "status__SEG_EPI": "CONFORME",
        "observacoes_gerais": "Inspeção começada.",
        "data_servico": date.today().isoformat(),
    })
    assert resposta.status_code == 302
    db.session.refresh(ex)
    assert ex.observacoes_gerais == "Inspeção começada."
    assert ex.respostas_snapshot["respostas"][0]["status"] == "CONFORME"


def test_conclusao_http_incompleta_salva_rascunho(ctx):
    app, ids = ctx
    ex, _ = criar_checklist(ids["v1"], "BASICA", usuario_id=ids["admin"])
    db.session.commit()
    client = app.test_client()
    login(client)
    csrf = token(client, ids["os"])
    resposta = client.post(f"/geradores/checklists/{ex.id}/salvar", data={
        "csrf_token_g5_f3": csrf, "acao": "concluir",
        "status__SEG_EPI": "CONFORME",
    })
    assert resposta.status_code == 302
    db.session.refresh(ex)
    assert ex.estado == "RASCUNHO"
    assert ex.respostas_snapshot["respostas"][0]["status"] == "CONFORME"


def test_concluido_nao_e_alterado_por_post(ctx):
    app, ids = ctx
    ex, _ = criar_checklist(ids["v1"], "BASICA", usuario_id=ids["admin"])
    db.session.commit()
    salvar_checklist(ex.id, resposta_para("BASICA"), usuario_id=ids["admin"], concluir=True)
    db.session.commit()
    original = ex.respostas_snapshot
    client = app.test_client()
    login(client)
    csrf = token(client, ids["os"])
    resp = client.post(f"/geradores/checklists/{ex.id}/salvar", data={
        "csrf_token_g5_f3": csrf, "acao": "salvar",
        "status__SEG_EPI": "NAO_CONFORME",
    })
    assert resp.status_code == 302
    db.session.refresh(ex)
    assert ex.respostas_snapshot == original


def test_metodos_http_protegidos(ctx):
    app, ids = ctx
    client = app.test_client()
    login(client)
    assert client.post(f"/geradores/checklists/os/{ids['os']}").status_code == 405
    assert client.get(f"/geradores/checklists/vinculos/{ids['v1']}/iniciar").status_code == 405


def test_checklist_concluido_permanece_consultavel_apos_inativar_gerador(ctx):
    app, ids = ctx
    ex, _ = criar_checklist(ids["v1"], "BASICA", usuario_id=ids["admin"])
    db.session.commit()
    salvar_checklist(
        ex.id, resposta_para("BASICA"),
        usuario_id=ids["admin"], concluir=True,
    )
    db.session.commit()
    gerador = db.session.get(Gerador, ids["g1"])
    gerador.ativo = False
    db.session.commit()
    client = app.test_client()
    login(client)
    resposta = client.get(f"/geradores/checklists/{ex.id}")
    assert resposta.status_code == 200
    assert "bloqueado para edição" in resposta.get_data(as_text=True)
    with pytest.raises(ExecucaoChecklistError):
        salvar_checklist(ex.id, {}, usuario_id=ids["admin"])


def test_checklist_rascunho_rejeita_edicao_de_gerador_inativo(ctx):
    _, ids = ctx
    ex, _ = criar_checklist(ids["v1"], "BASICA", usuario_id=ids["admin"])
    db.session.commit()
    gerador = db.session.get(Gerador, ids["g1"])
    gerador.ativo = False
    db.session.commit()
    with pytest.raises(ExecucaoChecklistError, match="indisponível"):
        salvar_checklist(ex.id, {}, usuario_id=ids["admin"])


def test_migration_f3_compativel_com_f2():
    codigo = (
        Path(__file__).resolve().parents[2]
        / "migrations/versions/20261014_02_geradores_g5_checklist_digital.py"
    ).read_text(encoding="utf-8")
    assert 'revision = "20261014_02"' in codigo
    assert 'down_revision = "20261014_01"' in codigo
    assert "op.alter_column" not in codigo
    assert "uq_gerador_checklist_vinculo_tipo" in codigo
    assert "Downgrade bloqueado" in codigo


def test_service_sem_commit_e_sem_financeiro_estoque():
    codigo = (
        Path(__file__).resolve().parents[2]
        / "app/geradores/gerador_checklist_execucao_service.py"
    ).read_text(encoding="utf-8")
    assert "db.session.commit(" not in codigo
    assert "LancamentoFinanceiro" not in codigo
    assert "MovimentacaoEstoque" not in codigo
