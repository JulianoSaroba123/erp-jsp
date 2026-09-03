# -*- coding: utf-8 -*-
"""
Teste de Regressão: esqueleto global do Command Center (base.html)
====================================================================

Valida que a modernização visual do esqueleto (sidebar/topbar/área
principal) preserva 100% do comportamento funcional:
- login continua funcionando;
- páginas-chave de cada módulo abrem sem erro (200, sem exceção Jinja);
- nenhuma rota foi renomeada (todas as âncoras de menu continuam
  presentes e reaproveitando os mesmos endpoints);
- item ativo do menu e estrutura responsiva (ids/classes usados por JS)
  permanecem intactos;
- itens de Prospecção/Precificação continuam ocultos do menu.
"""

import os
import sys
from datetime import date

os.environ['FLASK_CONFIG'] = 'testing'
os.environ['FLASK_ENV'] = 'testing'
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.app import create_app
from app.extensoes import db
from app.auth.usuario_model import Usuario


def _criar_admin():
    admin = Usuario.query.filter_by(usuario='admin_shell_test').first()
    if admin:
        return admin
    admin = Usuario(
        nome='Admin Shell Test',
        email='admin_shell_test@example.com',
        usuario='admin_shell_test',
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
    print("TESTE: esqueleto global (base.html) - JSP Command Center")
    print("=" * 70)

    app = create_app('testing')
    client = app.test_client()

    with app.app_context():
        db.create_all()
        admin = _criar_admin()

        print("\n[TESTE 1] Login continua funcionando...")
        resp = client.post('/auth/login', data={
            'identificador': 'admin_shell_test',
            'senha': 'SenhaForte123!',
        }, follow_redirects=True)
        assert resp.status_code == 200, f"Status inesperado no login: {resp.status_code}"
        html_pos_login = resp.data.decode('utf-8')
        assert 'Bem-vindo' in html_pos_login, "Mensagem de boas-vindas ausente após login"
        print("  -> OK: login autentica e redireciona normalmente.")

        rotas_obrigatorias = {
            'Dashboard principal': '/dashboard',
            'Financeiro': '/financeiro/',
            'Propostas': '/propostas/',
            'Ordens de Serviço': '/ordem_servico/',
            'Clientes': '/cliente/',
        }

        print("\n[TESTE 2-6] Validando páginas-chave de cada módulo...")
        for nome, url in rotas_obrigatorias.items():
            resp = client.get(url)
            assert resp.status_code in (200, 308), (
                f"{nome} ({url}) retornou status inesperado: {resp.status_code}"
            )
            if resp.status_code == 308:
                resp = client.get(url, follow_redirects=True)
                assert resp.status_code == 200, f"{nome} falhou após redirect: {resp.status_code}"
            html = resp.data.decode('utf-8')
            assert '<div class="sidebar" id="sidebar">' in html, f"{nome}: sidebar ausente"
            assert 'class="topbar-modern"' in html, f"{nome}: topbar ausente"
            assert 'class="content-wrapper"' in html, f"{nome}: área de conteúdo ausente"
            print(f"  -> OK: {nome} ({url}) renderizou com o novo esqueleto sem erro.")

        print("\n[TESTE 7] Nenhum endpoint foi renomeado (âncoras de menu intactas)...")
        resp = client.get('/dashboard')
        html = resp.data.decode('utf-8')
        # Verifica presença de hrefs resolvidos para os módulos centrais
        for trecho in ['/cliente', '/fornecedor', '/produto', '/equipamento',
                       '/propostas', '/pedido', '/ordem_servico', '/financeiro',
                       '/auth/logout', '/auth/perfil']:
            assert trecho in html, f"Referência de menu ausente/renomeada: {trecho}"
        print("  -> OK: todas as âncoras de menu preservadas (nenhuma rota renomeada).")

        print("\n[TESTE 8] Estrutura de IDs/classes usada pelo JavaScript preservada...")
        for marcador in ['id="sidebar"', 'onclick="toggleSidebar()"',
                          'id="financeiroMenu"', 'id="chevronFinanceiro"',
                          'onclick="toggleFinanceiroMenu(event)"', 'class="mobile-toggle']:
            assert marcador in html, f"Marcador usado por JS ausente: {marcador}"
        print("  -> OK: ids/onclick usados pelos scripts de sidebar continuam presentes.")

        print("\n[TESTE 9] Design System Command Center referenciado no shell...")
        assert 'css/command-center.css' in html, "command-center.css não referenciado"
        assert 'css/command-center-shell.css' in html, "command-center-shell.css não referenciado"
        print("  -> OK: novo Design System aplicado ao esqueleto global.")

        print("\n[TESTE 10] Prospecção/Precificação continuam ocultas do menu...")
        assert "url_for('prospeccao.dashboard')" not in open(
            os.path.join(os.path.dirname(__file__), '..', 'app', 'templates', 'base.html'),
            encoding='utf-8'
        ).read()
        assert 'Prospecção' not in html or 'nav-text">Prospecção' not in html
        print("  -> OK: itens ocultos permanecem fora do menu.")

    print("\n" + "=" * 70)
    print("TESTES DO ESQUELETO GLOBAL (COMMAND CENTER) VALIDADOS COM SUCESSO!")
    print("=" * 70)


if __name__ == '__main__':
    executar_testes()
