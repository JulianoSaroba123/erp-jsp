#!/usr/bin/env python3
"""
Script para debugar problemas com proposta
"""

import sys
import os

# Adicionar o diretório raiz ao path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from aplicacao import create_app
from aplicacao.extensoes import db
from aplicacao.cliente.cliente_model import Cliente

def debug_proposta():
    """Debug do módulo proposta"""
    print("🔍 Debugando módulo proposta...")
    
    try:
        app = create_app()
        
        with app.app_context():
            # Verificar se há clientes
            print("📋 Verificando clientes...")
            clientes = Cliente.query.filter(Cliente.ativo == True).all()
            print(f"✅ {len(clientes)} clientes encontrados")
            
            if clientes:
                for cliente in clientes[:3]:  # Mostrar apenas os primeiros 3
                    print(f"   - ID: {cliente.id}, Nome: {cliente.nome}")
            else:
                print("⚠️  Nenhum cliente encontrado! Isso pode causar erro no formulário.")
                
            # Verificar se as tabelas de proposta existem
            from sqlalchemy import inspect
            inspector = inspect(db.engine)
            tabelas = inspector.get_table_names()
            
            print("\n📊 Verificando tabelas de proposta...")
            if 'propostas' in tabelas:
                print("✅ Tabela 'propostas' existe")
            else:
                print("❌ Tabela 'propostas' NÃO existe!")
                
            if 'proposta_itens' in tabelas:
                print("✅ Tabela 'proposta_itens' existe")
            else:
                print("❌ Tabela 'proposta_itens' NÃO existe!")
                
            # Tentar importar modelos
            print("\n🔧 Testando imports dos modelos...")
            try:
                from aplicacao.proposta.proposta_model import Proposta, PropostaItem
                print("✅ Modelos de proposta importados com sucesso")
                
                # Contar propostas
                total_propostas = Proposta.query.count()
                print(f"✅ {total_propostas} propostas no banco")
                
            except Exception as e:
                print(f"❌ Erro ao importar modelos: {str(e)}")
                
            print("\n🎉 Debug concluído!")
            
    except Exception as e:
        print(f"❌ Erro no debug: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_proposta()