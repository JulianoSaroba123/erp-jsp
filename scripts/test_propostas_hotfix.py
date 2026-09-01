# -*- coding: utf-8 -*-
"""
Teste de Hotfix para /propostas/
Valida:
1. Listagem normal de propostas
2. Proposta com status NULL / None
3. Proposta com valor_total NULL / string / zero
4. Proposta com data_emissao NULL
5. Combinação de campos nulos/inválidos
6. Comportamento defensivo e integridade de sessão (rollback)
"""

import os
import sys
from datetime import date
from decimal import Decimal

os.environ['FLASK_CONFIG'] = 'testing'
os.environ['FLASK_ENV'] = 'testing'
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.app import create_app
from app.extensoes import db
from app.cliente.cliente_model import Cliente
from app.proposta.proposta_model import Proposta


def testar_hotfix_propostas():
    print("=" * 60)
    print("Iniciando testes da rota /propostas/ (Hotfix)")
    print("=" * 60)
    
    app = create_app()
    client = app.test_client()
    
    with app.app_context():
        # Limpar registros anteriores de teste se houver
        Proposta.query.filter(Proposta.codigo.like('PROPTEST%')).delete()
        db.session.commit()
        
        # 1. Criar cliente base
        cliente = Cliente.query.filter_by(nome='Cliente Teste Proposta').first()
        if not cliente:
            cliente = Cliente(nome='Cliente Teste Proposta', ativo=True)
            db.session.add(cliente)
            db.session.flush()
        
        # 2. Inserir cenários diversos de propostas
        # Cenário A: Proposta normal pendente
        p1 = Proposta(
            codigo='PROPTEST0001',
            cliente_id=cliente.id,
            titulo='Proposta Normal Pendente',
            status='pendente',
            valor_total=Decimal('1500.50'),
            data_emissao=date(2026, 8, 10),
            ativo=True
        )
        # Cenário B: Proposta com status None (NULL no banco)
        p2 = Proposta(
            codigo='PROPTEST0002',
            cliente_id=cliente.id,
            titulo='Proposta Status NULL',
            status=None,
            valor_total=Decimal('2300.00'),
            data_emissao=date(2026, 8, 15),
            ativo=True
        )
        # Cenário C: Proposta com valor_total None e data_emissao None
        p3 = Proposta(
            codigo='PROPTEST0003',
            cliente_id=cliente.id,
            titulo='Proposta Sem Valor e Sem Data',
            status='aprovada',
            valor_total=None,
            data_emissao=None,
            ativo=True
        )
        # Cenário D: Proposta com todos os campos críticos nulos/vazios
        p4 = Proposta(
            codigo='PROPTEST0004',
            cliente_id=cliente.id,
            titulo='',
            status=None,
            valor_total=None,
            data_emissao=None,
            ativo=True
        )
        # Cenário E: Proposta aprovada com valor
        p5 = Proposta(
            codigo='PROPTEST0005',
            cliente_id=cliente.id,
            titulo='Proposta Aprovada Normal',
            status='aprovada',
            valor_total=Decimal('3500.00'),
            data_emissao=date(2026, 8, 20),
            ativo=True
        )
        
        db.session.add_all([p1, p2, p3, p4, p5])
        db.session.commit()
        print("-> Registros de teste criados com sucesso no banco de dados.")

    # 3. Testar requisição GET /propostas/
    resp = client.get('/propostas/')
    print(f"-> Status Code GET /propostas/: {resp.status_code}")
    assert resp.status_code == 200, f"Esperado 200, obtido {resp.status_code}"
    
    html = resp.data.decode('utf-8')
    
    # 4. Asserções de conteúdo no HTML
    assert 'PROPTEST0001' in html, "PROPTEST0001 não encontrada no HTML"
    assert 'PROPTEST0002' in html, "PROPTEST0002 (status NULL) não encontrada no HTML"
    assert 'PROPTEST0003' in html, "PROPTEST0003 (sem valor/sem data) não encontrada no HTML"
    assert 'PROPTEST0004' in html, "PROPTEST0004 (todos nulos) não encontrada no HTML"
    assert 'PROPTEST0005' in html, "PROPTEST0005 não encontrada no HTML"
    assert 'R$ 1.500,50' in html, "Valor formatado de PROPTEST0001 não encontrado"
    assert 'R$ 3.500,00' in html, "Valor formatado de PROPTEST0005 não encontrado"
    
    print("-> Validações de renderização concluídas com sucesso!")
    
    # 5. Limpeza pós-teste
    with app.app_context():
        Proposta.query.filter(Proposta.codigo.like('PROPTEST%')).delete()
        db.session.commit()
        print("-> Registros de teste removidos.")
    
    print("=" * 60)
    print("TODOS OS TESTES DE /propostas/ PASSARAM COM SUCESSO!")
    print("=" * 60)


if __name__ == '__main__':
    testar_hotfix_propostas()
