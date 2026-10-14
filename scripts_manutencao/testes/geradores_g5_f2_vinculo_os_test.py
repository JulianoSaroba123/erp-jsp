# -*- coding: utf-8 -*-
"""G5-F2: testes HTTP, serviço e integridade com SQLite em memória.

Não acessa produção e não executa migration no PostgreSQL.
"""
import os
import re
from pathlib import Path

os.environ["FLASK_ENV"] = "testing"
os.environ["FLASK_CONFIG"] = "testing"
os.environ.pop("DATABASE_URL", None)

import pytest
from app import create_app
from app.extensoes import db
from app.auth.usuario_model import Usuario
from app.cliente.cliente_model import Cliente
from app.geradores.gerador_model import Gerador
from app.geradores.gerador_os_vinculo_model import GeradorOSVinculo
from app.geradores.gerador_os_vinculo_service import (
    GeradorOSVinculoError, candidatos_da_os, listar_vinculos_os,
    vincular_gerador_os,
)
from app.ordem_servico.ordem_servico_model import OrdemServico


@pytest.fixture
def ctx():
    app = create_app("testing")
    assert app.config["SQLALCHEMY_DATABASE_URI"] == "sqlite:///:memory:"
    with app.app_context():
        db.create_all()
        admin = Usuario(
            nome="Admin G5-F2", usuario="admin_g5f2", email="admin_g5f2@example.com",
            tipo_usuario="admin", ativo=True, email_confirmado=True,
            primeiro_login=False,
        )
        admin.set_senha("TesteG5f2Senha123!")
        comum = Usuario(
            nome="Usuario G5-F2", usuario="usuario_g5f2",
            email="usuario_g5f2@example.com", tipo_usuario="usuario",
            ativo=True, email_confirmado=True, primeiro_login=False,
        )
        comum.set_senha("TesteG5f2Senha123!")
        cliente_a = Cliente(nome="Cliente A G5", tipo="PJ",
                            cpf_cnpj="11666000000111", ativo=True)
        cliente_b = Cliente(nome="Cliente B G5", tipo="PJ",
                            cpf_cnpj="22777000000122", ativo=True)
        db.session.add_all([admin, comum, cliente_a, cliente_b])
        db.session.commit()

        os_a = OrdemServico(
            numero="OSG5F20001", titulo="Manutencao multipla de geradores",
            cliente_id=cliente_a.id, tipo_os="comercial",
            status="pendente", ativo=True, valor_total=990,
        )
        os_cancelada = OrdemServico(
            numero="OSG5F20002", titulo="OS cancelada",
            cliente_id=cliente_a.id, tipo_os="comercial",
            status="cancelada", ativo=True,
        )
        gerador1 = Gerador(
            codigo="GER-G5F2-01", cliente_id=cliente_a.id,
            status="ATIVO", ativo=True,
        )
        gerador2 = Gerador(
            codigo="GER-G5F2-02", cliente_id=cliente_a.id,
            status="ATIVO", ativo=True,
        )
        outro = Gerador(
            codigo="GER-G5F2-03", cliente_id=cliente_b.id,
            status="ATIVO", ativo=True,
        )
        inativo = Gerador(
            codigo="GER-G5F2-04", cliente_id=cliente_a.id,
            status="ATIVO", ativo=False,
        )
        db.session.add_all([os_a, os_cancelada, gerador1, gerador2, outro, inativo])
        db.session.commit()
        ids = {
            "os": os_a.id, "cancelada": os_cancelada.id,
            "g1": gerador1.id, "g2": gerador2.id,
            "outro": outro.id, "inativo": inativo.id,
            "admin": admin.id, "comum": comum.id,
        }
        yield app, ids
        db.session.remove()
        db.drop_all()


def login(client, usuario="admin_g5f2"):
    resposta = client.post("/auth/login", data={
        "identificador": usuario, "senha": "TesteG5f2Senha123!",
    })
    assert resposta.status_code == 302


def csrf_do_formulario(client, os_id):
    resposta = client.get(f"/geradores/os/{os_id}/geradores")
    assert resposta.status_code == 200
    html = resposta.get_data(as_text=True)
    achou = re.search(r'name="csrf_token_g5" value="([^"]+)"', html)
    assert achou is not None
    return achou.group(1), html


def test_servico_vincula_sem_commit_ou_mudar_os(ctx):
    _, ids = ctx
    os = db.session.get(OrdemServico, ids["os"])
    anterior = (os.status, os.valor_total)
    link, novo = vincular_gerador_os(ids["os"], ids["g1"], usuario_id=ids["admin"])
    assert novo
    assert link.ordem_servico_id == ids["os"]
    assert link.gerador_id == ids["g1"]
    assert (os.status, os.valor_total) == anterior
    db.session.rollback()
    assert GeradorOSVinculo.query.count() == 0


def test_idempotencia_mesma_os_e_gerador(ctx):
    _, ids = ctx
    a, primeiro = vincular_gerador_os(ids["os"], ids["g1"], usuario_id=ids["admin"])
    b, segundo = vincular_gerador_os(ids["os"], ids["g1"], usuario_id=ids["admin"])
    assert primeiro is True and segundo is False
    assert a.id == b.id
    assert GeradorOSVinculo.query.count() == 1


def test_uma_os_com_dois_geradores(ctx):
    _, ids = ctx
    vincular_gerador_os(ids["os"], ids["g1"], usuario_id=ids["admin"])
    vincular_gerador_os(ids["os"], ids["g2"], usuario_id=ids["admin"])
    db.session.commit()
    assert {v.gerador_id for v in listar_vinculos_os(ids["os"])} == {ids["g1"], ids["g2"]}


def test_cliente_diferente_bloqueado(ctx):
    _, ids = ctx
    with pytest.raises(GeradorOSVinculoError, match="outro cliente"):
        vincular_gerador_os(ids["os"], ids["outro"], usuario_id=ids["admin"])
    assert GeradorOSVinculo.query.count() == 0


def test_inativo_bloqueado(ctx):
    _, ids = ctx
    with pytest.raises(GeradorOSVinculoError, match="inativo"):
        vincular_gerador_os(ids["os"], ids["inativo"], usuario_id=ids["admin"])
    assert GeradorOSVinculo.query.count() == 0


def test_os_cancelada_bloqueada(ctx):
    _, ids = ctx
    with pytest.raises(GeradorOSVinculoError, match="cancelada"):
        vincular_gerador_os(ids["cancelada"], ids["g1"], usuario_id=ids["admin"])
    assert GeradorOSVinculo.query.count() == 0


@pytest.mark.parametrize("valor", [None, "", 0, "-1", "1.0", True, "injection"])
def test_ids_invalidos_bloqueados(ctx, valor):
    _, ids = ctx
    with pytest.raises(GeradorOSVinculoError):
        vincular_gerador_os(ids["os"], valor, usuario_id=ids["admin"])


def test_listagem_limita_geradores_ao_cliente(ctx):
    _, ids = ctx
    encontrados = candidatos_da_os(ids["os"])
    assert {g.id for g in encontrados} == {ids["g1"], ids["g2"]}


def test_nao_autenticado_nao_acessa(ctx):
    app, ids = ctx
    client = app.test_client()
    assert client.get(f"/geradores/os/{ids['os']}/geradores").status_code == 302


def test_usuario_nao_admin_nao_acessa(ctx):
    app, ids = ctx
    client = app.test_client()
    login(client, "usuario_g5f2")
    assert client.get(f"/geradores/os/{ids['os']}/geradores").status_code == 403
    assert client.post(f"/geradores/os/{ids['os']}/geradores/vincular").status_code == 403


def test_get_admin_exibe_os_e_geradores(ctx):
    app, ids = ctx
    client = app.test_client()
    login(client)
    _, html = csrf_do_formulario(client, ids["os"])
    assert "OSG5F20001" in html
    assert "GER-G5F2-01" in html
    assert "GER-G5F2-02" in html
    assert "GER-G5F2-03" not in html


def test_post_csrf_invalido_e_rejeitado(ctx):
    app, ids = ctx
    client = app.test_client()
    login(client)
    url = f"/geradores/os/{ids['os']}/geradores/vincular"
    assert client.post(url, data={"gerador_id": ids["g1"]}).status_code == 400
    assert GeradorOSVinculo.query.count() == 0


def test_post_gerador_outro_cliente_nao_grava(ctx):
    app, ids = ctx
    client = app.test_client()
    login(client)
    csrf, _ = csrf_do_formulario(client, ids["os"])
    resp = client.post(
        f"/geradores/os/{ids['os']}/geradores/vincular",
        data={"csrf_token_g5": csrf, "gerador_id": ids["outro"]},
    )
    assert resp.status_code == 302
    assert GeradorOSVinculo.query.count() == 0


def test_post_do_formulario_cria_e_repete_sem_duplicar(ctx):
    app, ids = ctx
    client = app.test_client()
    login(client)
    csrf, _ = csrf_do_formulario(client, ids["os"])
    url = f"/geradores/os/{ids['os']}/geradores/vincular"
    for _ in range(2):
        resp = client.post(url, data={
            "csrf_token_g5": csrf, "gerador_id": ids["g1"]
        })
        assert resp.status_code == 302
    assert GeradorOSVinculo.query.count() == 1


def test_post_nao_altera_valor_status_os(ctx):
    app, ids = ctx
    client = app.test_client()
    login(client)
    csrf, _ = csrf_do_formulario(client, ids["os"])
    os = db.session.get(OrdemServico, ids["os"])
    antigo = (os.status, os.valor_total)
    client.post(
        f"/geradores/os/{ids['os']}/geradores/vincular",
        data={"csrf_token_g5": csrf, "gerador_id": ids["g1"]},
    )
    db.session.refresh(os)
    assert (os.status, os.valor_total) == antigo


def test_metodos_nao_autorizados(ctx):
    app, ids = ctx
    client = app.test_client()
    login(client)
    assert client.post(f"/geradores/os/{ids['os']}/geradores").status_code == 405
    assert client.get(f"/geradores/os/{ids['os']}/geradores/vincular").status_code == 405


def test_os_inexistente_http_404(ctx):
    app, _ = ctx
    client = app.test_client()
    login(client)
    assert client.get("/geradores/os/99999999/geradores").status_code == 404


def test_migration_g5_f2_aditiva():
    codigo = (
        Path(__file__).resolve().parents[2]
        / "migrations/versions/20261014_01_geradores_g5_vinculo_os.py"
    ).read_text(encoding="utf-8")
    assert 'revision = "20261014_01"' in codigo
    assert 'down_revision = "cdbaf09054ac"' in codigo
    assert "op.create_table(" in codigo
    assert "uq_gerador_os_vinculo_par" in codigo
    assert "Downgrade bloqueado" in codigo
    assert "op.alter_column" not in codigo


def test_servico_nao_faz_commit_sem_movimentacoes():
    texto = (
        Path(__file__).resolve().parents[2]
        / "app/geradores/gerador_os_vinculo_service.py"
    ).read_text(encoding="utf-8")
    assert "db.session.commit(" not in texto
    assert "movimentacoes_estoque" not in texto
    assert "LancamentoFinanceiro" not in texto
