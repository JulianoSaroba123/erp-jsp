#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script para ativar o cliente João Silva Santos
"""

from app.app import create_app
from app.cliente.cliente_model import Cliente
from app.extensoes import db

def ativar_cliente():
    """Ativa o cliente João Silva Santos"""
    
    app = create_app()
    
    with app.app_context():
        print("🔧 CORRIGINDO: Ativando cliente João Silva Santos...")
        
        cliente = Cliente.query.get(1)
        
        if cliente:
            print(f"📋 Cliente encontrado: {cliente.nome}")
            print(f"   - Status atual: {'Ativo' if cliente.ativo else 'Inativo'}")
            
            if not cliente.ativo:
                cliente.ativo = True
                cliente.save()
                print("✅ Cliente ativado com sucesso!")
            else:
                print("✅ Cliente já estava ativo")
                
            # Verifica se agora aparece na lista
            clientes_ativos = Cliente.query.filter_by(ativo=True).order_by(Cliente.nome).all()
            print(f"\n📊 Clientes ativos após correção: {len(clientes_ativos)}")
            
            for c in clientes_ativos:
                print(f"   - ID: {c.id}, Nome: {c.nome}")
                
        else:
            print("❌ Cliente não encontrado")

if __name__ == '__main__':
    ativar_cliente()