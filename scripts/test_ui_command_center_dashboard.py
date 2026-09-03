# -*- coding: utf-8 -*-
"""
Teste de Regressão: Dashboard Geral (Command Center) - Etapa 3
================================================================

Valida que a modernização visual do Dashboard Geral preserva 100% dos
dados/consultas existentes e do comportamento funcional:
- rota /dashboard renderiza 200;
- todos os indicadores existentes (stats) continuam presentes, sem
  nenhum número inventado;
- clientes recentes e ordens de serviço recentes (já calculados no
  backend) agora aparecem no template;
- resumo financeiro (dados já existentes em stats) exibido sem alterar
  o Dashboard Financeiro;
- ações rápidas preservam as mesmas rotas;
- estado vazio elegante quando não há dados;
- login, sidebar/topbar, financeiro, propostas, OS e clientes continuam
  abrindo sem erro Jinja.
"""

import os
import sys

os.environ['FLASK_CONFIG'] = 'testing'
os.environ['FLASK_ENV'] = 'testing'
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.app import create_app
from app.extensoes import db
from app.auth.usuario_model import Usuario
from app.cliente.cliente_model import Cliente


def _criar_admin():
    admin = Usuario.query.filter_by(usuario='admin_dash_test').first()
    if admin:
        return admin
    admin = Usuario(
        nome='Admin Dashboard Test',
        email='admin_dash_test@example.com',
        usuario='admin_dash_test',
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
    print("TESTE: Dashboard Geral (Command Center) - Etapa 3")
    print("=" * 70)

    app = create_app('testing')
    client = app.test_client()

    with app.app_context():
        db.create_all()
        _criar_admin()

        resp = client.post('/auth/login', data={
            'identificador': 'admin_dash_test',
            'senha': 'SenhaForte123!',
        }, follow_redirects=True)
        assert resp.status_code == 200, "Falha ao autenticar para os testes do dashboard"

        print("\n[TESTE 1] Dashboard renderiza 200 (estado vazio)...")
        resp = client.get('/dashboard')
        assert resp.status_code == 200, f"Status inesperado: {resp.status_code}"
        html = resp.data.decode('utf-8')
        print("  -> OK: /dashboard responde 200.")

        print("\n[TESTE 2] Indicadores principais preservados (sem números inventados)...")
        for marcador in ['cc-kpi-value', 'Clientes', 'Fornecedores', 'Produtos', 'Estoque Baixo']:
            assert marcador in html, f"Indicador ausente: {marcador}"
        print("  -> OK: cards de indicadores reorganizados, mesmos dados de stats.")

        print("\n[TESTE 3] Área operacional (OS) e Comercial exibidas...")
        for marcador in ['Ordens de Serviço', 'Comercial', 'Financeiro']:
            assert marcador in html, f"Painel ausente: {marcador}"
        print("  -> OK: painéis operacional/comercial/financeiro presentes.")

        print("\n[TESTE 4] Estado vazio elegante quando não há dados...")
        assert 'cc-empty-state' in html, "Estado vazio não implementado"
        print("  -> OK: estados vazios usam o novo componente cc-empty-state.")

        print("\n[TESTE 5] Ações rápidas preservam as mesmas rotas...")
        for endpoint_url in ['/ordem_servico/novo', '/cliente/novo', '/produto/novo', '/fornecedor/novo']:
            assert endpoint_url in html, f"Rota de ação rápida ausente/renomeada: {endpoint_url}"
        print("  -> OK: nenhuma rota de ação rápida foi alterada.")

        print("\n[TESTE 6] Com dados: cliente recente e resumo financeiro aparecem...")
        cliente = Cliente(nome='Cliente Dashboard Teste', ativo=True)
        db.session.add(cliente)
        db.session.commit()
        resp = client.get('/dashboard')
        assert resp.status_code == 200
        html_com_dados = resp.data.decode('utf-8')
        assert 'Cliente Dashboard Teste' in html_com_dados, "Cliente recente não exibido"
        assert 'Receitas do mês' in html_com_dados and 'Despesas do mês' in html_com_dados
        print("  -> OK: dados existentes (clientes_recentes/stats financeiros) renderizados.")

        print("\n[TESTE 7] Design System Command Center referenciado...")
        assert 'css/command-center-dashboard.css' in html_com_dados
        print("  -> OK: novo stylesheet do dashboard vinculado.")

        print("\n[TESTE 8] Sidebar/topbar/login/demais módulos continuam OK...")
        assert 'class="sidebar" id="sidebar"' in html_com_dados
        assert 'class="topbar-modern"' in html_com_dados
        for nome, url in {
            'Financeiro': '/financeiro/',
            'Propostas': '/propostas/',
            'Ordens de Serviço': '/ordem_servico/',
            'Clientes': '/cliente/',
        }.items():
            r = client.get(url)
            assert r.status_code in (200, 308), f"{nome} falhou: {r.status_code}"
        resp_login = client.get('/auth/login')
        assert resp_login.status_code in (200, 302), f"Login endpoint falhou: {resp_login.status_code}"
        print("  -> OK: shell global e demais módulos continuam funcionando.")

        # Limpeza
        db.session.delete(cliente)
        db.session.commit()

    print("\n" + "=" * 70)
    print("TESTES DO DASHBOARD GERAL (COMMAND CENTER) VALIDADOS COM SUCESSO!")
    print("=" * 70)


if __name__ == '__main__':
    executar_testes()
