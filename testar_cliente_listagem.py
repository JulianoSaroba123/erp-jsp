# -*- coding: utf-8 -*-
"""Testa a listagem de clientes para encontrar o erro."""

import os
os.environ['DATABASE_URL'] = 'postgresql://postgres:postgres@localhost/erp_jsp_local'

from app.app import create_app
from app.cliente.cliente_model import Cliente

app = create_app()

with app.app_context():
    print("Buscando clientes...")
    try:
        clientes = Cliente.query.filter_by(ativo=True).order_by(Cliente.nome).all()
        print(f"✓ {len(clientes)} clientes encontrados")
        
        for cliente in clientes:
            print(f"\nCliente ID {cliente.id}:")
            print(f"  - Nome: {cliente.nome}")
            print(f"  - Tipo: {cliente.tipo}")
            try:
                print(f"  - Nome Display: {cliente.nome_display}")
            except Exception as e:
                print(f"  ✗ ERRO ao acessar nome_display: {e}")
            
            try:
                print(f"  - Documento: {cliente.documento_formatado}")
            except Exception as e:
                print(f"  ✗ ERRO ao acessar documento_formatado: {e}")
                
    except Exception as e:
        print(f"✗ ERRO ao buscar clientes: {e}")
        import traceback
        traceback.print_exc()
