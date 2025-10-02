#!/usr/bin/env python3
"""
Script para criar as tabelas de proposta no banco de dados
"""

import sys
import os

# Adicionar o diretório raiz ao path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from aplicacao import create_app
from aplicacao.extensoes import db
from aplicacao.proposta.proposta_model import Proposta, PropostaItem

def main():
    """Criar tabelas de proposta"""
    print("🔄 Criando tabelas de propostas...")
    
    try:
        app = create_app()
        
        with app.app_context():
            # Criar tabelas
            db.create_all()
            print("✅ Tabelas de propostas criadas com sucesso!")
            
            # Verificar se as tabelas foram criadas
            from sqlalchemy import inspect
            inspector = inspect(db.engine)
            tabelas = inspector.get_table_names()
            
            if 'propostas' in tabelas:
                print("✓ Tabela 'propostas' criada")
            if 'proposta_itens' in tabelas:
                print("✓ Tabela 'proposta_itens' criada")
                
            print("\n🎉 Sistema de propostas pronto para uso!")
            
    except Exception as e:
        print(f"❌ Erro ao criar tabelas: {str(e)}")
        return False
    
    return True

if __name__ == "__main__":
    main()