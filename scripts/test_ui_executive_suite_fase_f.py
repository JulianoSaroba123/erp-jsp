# -*- coding: utf-8 -*-
"""Regressao visual da Fase F: Ordens de Servico."""
import os
import sys

os.environ['FLASK_CONFIG'] = 'testing'
os.environ['FLASK_ENV'] = 'testing'
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.app import create_app
from app.auth.usuario_model import Usuario
from app.cliente.cliente_model import Cliente
from app.configuracao import configuracao_utils
from app.extensoes import db
from app.ordem_servico.ordem_servico_model import OrdemServico


def executar_testes():
    configuracao_utils.get_config = lambda: None
    app = create_app('testing')
    client = app.test_client()
    with app.app_context():
        db.create_all()
        admin = Usuario(nome='Admin Fase F', email='admin_fasef@example.com', usuario='admin_fasef', tipo_usuario='admin', ativo=True, email_confirmado=True, primeiro_login=False)
        admin.set_senha('SenhaForte123!')
        cliente = Cliente(nome='TEST_FASEF_Cliente', tipo='PF', cpf_cnpj='12345678901', ativo=True)
        db.session.add_all([admin, cliente])
        db.session.commit()
        ordem = OrdemServico(numero='OSFASEF001', cliente_id=cliente.id, titulo='TEST_FASEF_OS', status='pendente', ativo=True)
        db.session.add(ordem)
        db.session.commit()
        ordem_id = ordem.id

    client.post('/auth/login', data={'identificador': 'admin_fasef', 'senha': 'SenhaForte123!'})
    paginas = {
        '/ordem_servico/listar': ('cc-table', 'jsp-executive-suite-phase-f.css'),
        '/ordem_servico/novo': ('id="cliente_select_os"', 'id="servicosContainer"', 'id="produtosContainer"', 'id="anexos_input"', 'id="assinatura_cliente"'),
        f'/ordem_servico/{ordem_id}': ('TEST_FASEF_OS', 'jsp-executive-suite-phase-f.css'),
        f'/ordem_servico/{ordem_id}/editar': ('id="equipamento_cadastrado"', 'id="valorTotal"', 'id="assinatura_tecnico"'),
        f'/ordem_servico/{ordem_id}/excluir': ('Confirmar Exclusão', 'jsp-executive-suite-phase-f.css'),
    }
    for url, expected in paginas.items():
        response = client.get(url)
        assert response.status_code == 200, (url, response.status_code)
        html = response.get_data(as_text=True)
        for marker in expected:
            assert marker in html, (url, marker)

    for url in ['/auth/login', '/dashboard', '/cliente/listar', '/fornecedor/listar', '/produto/listar', '/servico/listar', '/equipamentos/listar', '/propostas/', '/pedido/', '/pedido-compra/', '/financeiro/']:
        response = client.get(url)
        assert response.status_code in (200, 302, 308), (url, response.status_code)
    print('FASE F: Ordens de Servico OK')


if __name__ == '__main__':
    executar_testes()
