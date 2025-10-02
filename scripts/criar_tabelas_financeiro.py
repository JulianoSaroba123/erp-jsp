#!/usr/bin/env python3
"""
Script para criar as tabelas do módulo financeiro
"""

import sys
import os

# Adicionar o caminho do projeto
sys.path.append(os.path.abspath('.'))

from aplicacao import create_app
from aplicacao.extensoes import db

# Importar os modelos para que sejam registrados
from aplicacao.financeiro.financeiro_model import LancamentoFinanceiro
from aplicacao.financeiro.formacao_preco.modelos import FormacaoPrecoConfig

def criar_tabelas_financeiro():
    """Cria as tabelas do módulo financeiro"""
    
    app = create_app()
    
    with app.app_context():
        try:
            print("🔧 Criando tabelas do módulo financeiro...")
            
            # Criar apenas as tabelas específicas do financeiro
            tabelas_financeiro = [
                LancamentoFinanceiro.__table__,
                FormacaoPrecoConfig.__table__
            ]
            
            for tabela in tabelas_financeiro:
                print(f"  Criando tabela: {tabela.name}")
                tabela.create(db.engine, checkfirst=True)
            
            print("✅ Tabelas do módulo financeiro criadas com sucesso!")
            
            # Verificar se foram criadas
            print("\n📋 Verificando tabelas criadas:")
            inspector = db.inspect(db.engine)
            tabelas_existentes = inspector.get_table_names()
            
            for nome_tabela in ['lancamentos_financeiros', 'formacao_preco_config']:
                if nome_tabela in tabelas_existentes:
                    print(f"  ✅ {nome_tabela}")
                else:
                    print(f"  ❌ {nome_tabela}")
            
        except Exception as e:
            print(f"❌ Erro ao criar tabelas: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    criar_tabelas_financeiro()