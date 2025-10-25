#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script para testar os dados da ordem de serviço e cliente na edição
"""

from app.app import create_app
from app.ordem_servico.ordem_servico_model import OrdemServico
from app.cliente.cliente_model import Cliente
from app.extensoes import db

def testar_dados_edicao():
    """Testa se os dados estão sendo carregados corretamente na edição"""
    
    app = create_app()
    
    with app.app_context():
        print("🔍 TESTE: Verificando dados de edição...")
        
        # Busca uma ordem específica
        ordem = OrdemServico.query.filter_by(numero='OS20250001').first()
        
        if not ordem:
            print("❌ Ordem OS20250001 não encontrada")
            return
            
        print(f"✅ Ordem encontrada: {ordem.numero}")
        print(f"   - ID: {ordem.id}")
        print(f"   - Título: {ordem.titulo}")
        print(f"   - Cliente ID: {ordem.cliente_id}")
        
        # Verifica se o cliente existe
        if ordem.cliente:
            print(f"   - Cliente: {ordem.cliente.nome}")
            print(f"   - Cliente ID real: {ordem.cliente.id}")
        else:
            print("❌ Cliente não encontrado/vinculado")
        
        # Lista todos os clientes disponíveis
        clientes = Cliente.query.filter_by(ativo=True).order_by(Cliente.nome).all()
        print(f"\n📋 Total de clientes ativos: {len(clientes)}")
        
        for cliente in clientes[:5]:  # Mostra apenas os primeiros 5
            print(f"   - ID: {cliente.id}, Nome: {cliente.nome}")
            
        print("\n🔍 Verificando se o cliente da ordem está na lista:")
        if ordem.cliente_id:
            cliente_encontrado = any(c.id == ordem.cliente_id for c in clientes)
            print(f"   - Cliente da ordem na lista: {'✅ Sim' if cliente_encontrado else '❌ Não'}")
        
        print(f"\n📊 Dados completos da ordem:")
        print(f"   - Solicitante: {ordem.solicitante}")
        print(f"   - Descrição problema: {ordem.descricao_problema}")
        print(f"   - Status: {ordem.status}")

if __name__ == '__main__':
    testar_dados_edicao()