# -*- coding: utf-8 -*-
"""
Script para adicionar campos de parcelamento na tabela propostas
=================================================================

Adiciona as colunas:
- numero_parcelas (INTEGER)
- intervalo_parcelas (INTEGER)  
- data_primeira_parcela (DATE)

Também cria a tabela parcelas_proposta se não existir.

Uso:
    python scripts/adicionar_campos_parcelamento_proposta.py
"""

import sys
import os
from pathlib import Path

# Adiciona o diretório raiz ao path
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))

from app.app import create_app
from app.extensoes import db
from sqlalchemy import text, inspect

def adicionar_colunas_parcelamento():
    """Adiciona colunas de parcelamento na tabela propostas."""
    
    app = create_app()
    
    with app.app_context():
        inspector = inspect(db.engine)
        
        # Verificar se a tabela propostas existe
        if 'propostas' not in inspector.get_table_names():
            print("❌ Tabela 'propostas' não encontrada!")
            return
        
        # Obter colunas existentes
        colunas_existentes = [col['name'] for col in inspector.get_columns('propostas')]
        
        print("🔍 Verificando colunas de parcelamento...")
        print(f"   Colunas existentes: {len(colunas_existentes)}")
        
        # Colunas a adicionar
        colunas_adicionar = []
        
        if 'numero_parcelas' not in colunas_existentes:
            colunas_adicionar.append(('numero_parcelas', 'INTEGER DEFAULT 1'))
        
        if 'intervalo_parcelas' not in colunas_existentes:
            colunas_adicionar.append(('intervalo_parcelas', 'INTEGER DEFAULT 30'))
        
        if 'data_primeira_parcela' not in colunas_existentes:
            colunas_adicionar.append(('data_primeira_parcela', 'DATE'))
        
        if not colunas_adicionar:
            print("✅ Todas as colunas já existem!")
            return
        
        print(f"\n📝 Adicionando {len(colunas_adicionar)} colunas:")
        
        try:
            for nome_coluna, tipo in colunas_adicionar:
                sql = f"ALTER TABLE propostas ADD COLUMN {nome_coluna} {tipo}"
                print(f"   ➕ {nome_coluna} ({tipo})... ", end='')
                db.session.execute(text(sql))
                db.session.commit()
                print("✅")
            
            print("\n✅ Colunas adicionadas com sucesso!")
            
        except Exception as e:
            print(f"❌ Erro: {str(e)}")
            db.session.rollback()
            return


def criar_tabela_parcelas():
    """Cria a tabela parcelas_proposta se não existir."""
    
    app = create_app()
    
    with app.app_context():
        inspector = inspect(db.engine)
        
        # Verificar se a tabela já existe
        if 'parcelas_proposta' in inspector.get_table_names():
            print("✅ Tabela 'parcelas_proposta' já existe!")
            return
        
        print("\n📝 Criando tabela parcelas_proposta...")
        
        try:
            sql = """
            CREATE TABLE parcelas_proposta (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                proposta_id INTEGER NOT NULL,
                numero_parcela INTEGER NOT NULL,
                valor_parcela NUMERIC(10, 2) NOT NULL,
                data_vencimento DATE NOT NULL,
                status VARCHAR(20) DEFAULT 'pendente',
                data_pagamento DATE,
                descricao VARCHAR(200),
                ativo BOOLEAN DEFAULT 1,
                data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                data_atualizacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                usuario_criacao VARCHAR(100),
                usuario_atualizacao VARCHAR(100),
                FOREIGN KEY (proposta_id) REFERENCES propostas (id)
            )
            """
            
            db.session.execute(text(sql))
            db.session.commit()
            
            print("✅ Tabela criada com sucesso!")
            
        except Exception as e:
            print(f"❌ Erro: {str(e)}")
            db.session.rollback()


def main():
    """Executa ambas as operações."""
    
    print("=" * 60)
    print("🚀 ADICIONAR CAMPOS DE PARCELAMENTO EM PROPOSTAS")
    print("=" * 60)
    print()
    
    # Adicionar colunas na tabela propostas
    adicionar_colunas_parcelamento()
    
    # Criar tabela de parcelas
    criar_tabela_parcelas()
    
    print()
    print("=" * 60)
    print("✅ SCRIPT CONCLUÍDO!")
    print("=" * 60)
    print()
    print("📋 Próximos passos:")
    print("   1. Teste criando uma nova proposta com parcelamento")
    print("   2. Verifique se as parcelas são geradas automaticamente")
    print("   3. Edite a proposta e veja se as parcelas são atualizadas")
    print()


if __name__ == '__main__':
    main()
