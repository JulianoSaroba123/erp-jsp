# -*- coding: utf-8 -*-
"""
Diagnóstico: Cliente ID 20
===========================
Verifica se o cliente 20 existe e se há algum erro ao carregá-lo.
"""

import os
import sys

# Adiciona o diretório raiz ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.extensoes import db
from app.cliente.cliente_model import Cliente

def diagnosticar():
    """Diagnostica o cliente ID 20."""
    app = create_app()
    
    with app.app_context():
        print(f"\n{'='*60}")
        print(f"🔍 DIAGNÓSTICO: Cliente ID 20")
        print(f"{'='*60}\n")
        
        # Verificar se existe
        cliente = Cliente.query.get(20)
        
        if not cliente:
            print("❌ Cliente 20 NÃO ENCONTRADO no banco de dados")
            print("\n📋 Listando últimos 10 clientes:")
            ultimos = Cliente.query.order_by(Cliente.id.desc()).limit(10).all()
            for c in ultimos:
                print(f"   ID {c.id}: {c.nome} (ativo={c.ativo})")
            return
        
        print(f"✅ Cliente 20 ENCONTRADO\n")
        print(f"📋 Dados básicos:")
        print(f"   ID: {cliente.id}")
        print(f"   Nome: {cliente.nome}")
        print(f"   Tipo: {cliente.tipo}")
        print(f"   CPF/CNPJ: {cliente.cpf_cnpj}")
        print(f"   Ativo: {cliente.ativo}")
        print(f"   Status: {cliente.status}")
        
        # Testar properties que podem dar erro
        print(f"\n🧪 Testando properties:")
        
        try:
            print(f"   nome_display: {cliente.nome_display}")
        except Exception as e:
            print(f"   ❌ ERRO em nome_display: {e}")
        
        try:
            print(f"   documento_formatado: {cliente.documento_formatado}")
        except Exception as e:
            print(f"   ❌ ERRO em documento_formatado: {e}")
        
        try:
            print(f"   endereco_completo: {cliente.endereco_completo}")
        except Exception as e:
            print(f"   ❌ ERRO em endereco_completo: {e}")
        
        try:
            print(f"   total_compras: {cliente.total_compras}")
        except Exception as e:
            print(f"   ❌ ERRO em total_compras: {e}")
        
        # Verificar relacionamentos
        print(f"\n🔗 Verificando relacionamentos:")
        
        try:
            print(f"   Propostas: {len(cliente.propostas)} registros")
        except Exception as e:
            print(f"   ❌ ERRO ao carregar propostas: {e}")
        
        try:
            print(f"   Ordens de Serviço: {len(cliente.ordens_servico)} registros")
        except Exception as e:
            print(f"   ❌ ERRO ao carregar ordens_servico: {e}")
        
        print(f"\n{'='*60}")
        print("✅ Diagnóstico concluído")
        print(f"{'='*60}\n")

if __name__ == '__main__':
    diagnosticar()
