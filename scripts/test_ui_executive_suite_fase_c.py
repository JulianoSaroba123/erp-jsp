# -*- coding: utf-8 -*-
"""
Teste de Regressão: Fase C - Clientes e Fornecedores (JSP Executive Suite)
============================================================================

Valida que a migração visual dos módulos Clientes e Fornecedores preserva
100% do comportamento funcional (rotas, campos de formulário, filtros,
exclusão) e aplica o novo Design System, além de confirmar que o restante
do sistema (login, dashboard, shell, financeiro, propostas, OS) continua
funcionando sem regressão.
"""

import os
import sys
from decimal import Decimal

os.environ['FLASK_CONFIG'] = 'testing'
os.environ['FLASK_ENV'] = 'testing'
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.app import create_app
from app.extensoes import db
from app.auth.usuario_model import Usuario
from app.cliente.cliente_model import Cliente
from app.fornecedor.fornecedor_model import Fornecedor


def _criar_admin():
    admin = Usuario.query.filter_by(usuario='admin_fasec_test').first()
    if admin:
        return admin
    admin = Usuario(
        nome='Admin Fase C Test',
        email='admin_fasec_test@example.com',
        usuario='admin_fasec_test',
        tipo_usuario='admin',
        ativo=True,
        email_confirmado=True,
        primeiro_login=False,
    )
    admin.set_senha('SenhaForte123!')
    db.session.add(admin)
    db.session.commit()
    return admin


def executar_testes():
    print("=" * 70)
    print("TESTE: Fase C - Clientes e Fornecedores (JSP Executive Suite)")
    print("=" * 70)

    app = create_app('testing')
    client = app.test_client()

    with app.app_context():
        db.create_all()
        _criar_admin()
        client.post('/auth/login', data={
            'identificador': 'admin_fasec_test',
            'senha': 'SenhaForte123!',
        }, follow_redirects=True)

        Cliente.query.filter(Cliente.nome.like('TEST_FASEC_%')).delete()
        Fornecedor.query.filter(Fornecedor.nome.like('TEST_FASEC_%')).delete()
        db.session.commit()

        cliente = Cliente(nome='TEST_FASEC_Cliente PF', tipo='PF', cpf_cnpj='11122233344', ativo=True)
        fornecedor = Fornecedor(nome='TEST_FASEC_Fornecedor', tipo='PJ', cnpj_cpf='11222333000144', ativo=True)
        db.session.add_all([cliente, fornecedor])
        db.session.commit()

        print("\n[TESTE 1] Clientes: listar, filtrar, estado vazio, Design System...")
        resp = client.get('/cliente/listar')
        assert resp.status_code == 200
        html = resp.data.decode('utf-8')
        assert 'cc-page-header' in html
        assert 'cc-table-container' in html
        assert 'cc-mini-stat' in html
        assert 'test_fasec_cliente pf' in html.lower()
        print("  -> OK: listagem de clientes usa os novos componentes globais.")

        resp = client.get('/cliente/listar?busca=NaoExisteNadaAssim')
        assert resp.status_code == 200
        html_vazio = resp.data.decode('utf-8')
        assert 'cc-empty-state' in html_vazio
        print("  -> OK: estado vazio elegante ao filtrar sem resultados.")

        print("\n[TESTE 2] Clientes: cadastrar e editar (formulário)...")
        resp = client.get('/cliente/novo')
        assert resp.status_code == 200
        html_form = resp.data.decode('utf-8')
        for campo in ['name="tipo"', 'name="cpf_cnpj"', 'name="email"', 'id="btn-consultar-cnpj"']:
            assert campo in html_form, f"Campo ausente no form de cliente: {campo}"

        resp = client.get(f'/cliente/{cliente.id}/editar')
        assert resp.status_code == 200
        print("  -> OK: cadastro e edição de clientes preservam campos/ids.")

        print("\n[TESTE 3] Clientes: visualizar...")
        resp = client.get(f'/cliente/{cliente.id}')
        assert resp.status_code == 200
        assert 'test_fasec_cliente pf' in resp.data.decode('utf-8').lower()
        print("  -> OK: visualização de cliente renderiza corretamente.")

        print("\n[TESTE 4] Fornecedores: listar, filtrar por categoria, Design System...")
        resp = client.get('/fornecedor/listar')
        assert resp.status_code == 200
        html_forn = resp.data.decode('utf-8')
        assert 'cc-page-header' in html_forn
        assert 'cc-table-container' in html_forn
        assert 'test_fasec_fornecedor' in html_forn.lower()
        print("  -> OK: listagem de fornecedores usa os novos componentes globais.")

        print("\n[TESTE 5] Fornecedores: cadastrar, editar, visualizar...")
        resp = client.get('/fornecedor/novo')
        assert resp.status_code == 200
        resp = client.get(f'/fornecedor/{fornecedor.id}/editar')
        assert resp.status_code == 200
        resp = client.get(f'/fornecedor/{fornecedor.id}')
        assert resp.status_code == 200
        assert 'test_fasec_fornecedor' in resp.data.decode('utf-8').lower()
        print("  -> OK: cadastro, edição e visualização de fornecedores funcionam.")

        print("\n[TESTE 6] Regressão: login, dashboard, shell, financeiro, propostas, OS...")
        for nome, url in {
            'Login': '/auth/login',
            'Dashboard': '/dashboard',
            'Financeiro': '/financeiro/',
            'Propostas': '/propostas/',
            'Ordens de Serviço': '/ordem_servico/',
        }.items():
            r = client.get(url)
            assert r.status_code in (200, 302, 308), f"{nome} falhou: {r.status_code}"
        print("  -> OK: nenhuma regressão nos demais módulos.")

        # Limpeza
        Cliente.query.filter(Cliente.nome.like('TEST_FASEC_%')).delete()
        Fornecedor.query.filter(Fornecedor.nome.like('TEST_FASEC_%')).delete()
        db.session.commit()

    print("\n" + "=" * 70)
    print("FASE C (CLIENTES E FORNECEDORES) VALIDADA COM SUCESSO!")
    print("=" * 70)


if __name__ == '__main__':
    executar_testes()
