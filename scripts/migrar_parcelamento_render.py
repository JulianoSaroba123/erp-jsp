# -*- coding: utf-8 -*-
"""
Script para adicionar campos de parcelamento - COMPATÍVEL COM POSTGRESQL
=========================================================================

Este script pode ser executado via SSH no Render ou localmente.

Para executar no Render via web service:
1. Adicione este arquivo ao repositório
2. No dashboard do Render, vá em "Shell"
3. Execute: python scripts/migrar_parcelamento_render.py

Uso local:
    python scripts/migrar_parcelamento_render.py
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
    """Adiciona colunas de parcelamento na tabela propostas (PostgreSQL compatible)."""
    
    app = create_app()
    
    with app.app_context():
        inspector = inspect(db.engine)
        
        # Verificar se a tabela propostas existe
        if 'propostas' not in inspector.get_table_names():
            print("❌ Tabela 'propostas' não encontrada!")
            return False
        
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
            return True
        
        print(f"\n📝 Adicionando {len(colunas_adicionar)} colunas:")
        
        try:
            for nome_coluna, tipo in colunas_adicionar:
                sql = f"ALTER TABLE propostas ADD COLUMN {nome_coluna} {tipo}"
                print(f"   ➕ {nome_coluna} ({tipo})... ", end='')
                db.session.execute(text(sql))
                db.session.commit()
                print("✅")
            
            print("\n✅ Colunas adicionadas com sucesso!")
            return True
            
        except Exception as e:
            print(f"❌ Erro: {str(e)}")
            db.session.rollback()
            return False


def criar_tabela_parcelas():
    """Cria a tabela parcelas_proposta se não existir (PostgreSQL compatible)."""
    
    app = create_app()
    
    with app.app_context():
        inspector = inspect(db.engine)
        
        # Verificar se a tabela já existe
        if 'parcelas_proposta' in inspector.get_table_names():
            print("✅ Tabela 'parcelas_proposta' já existe!")
            return True
        
        print("\n📝 Criando tabela parcelas_proposta...")
        
        try:
            # SQL compatível com PostgreSQL (usa SERIAL em vez de AUTOINCREMENT)
            sql = """
            CREATE TABLE parcelas_proposta (
                id SERIAL PRIMARY KEY,
                proposta_id INTEGER NOT NULL,
                numero_parcela INTEGER NOT NULL,
                valor_parcela NUMERIC(10, 2) NOT NULL,
                data_vencimento DATE NOT NULL,
                status VARCHAR(20) DEFAULT 'pendente',
                data_pagamento DATE,
                descricao VARCHAR(200),
                ativo BOOLEAN DEFAULT true,
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
            return True
            
        except Exception as e:
            print(f"❌ Erro: {str(e)}")
            db.session.rollback()
            return False


def main():
    """Executa ambas as operações."""
    
    print("=" * 70)
    print("🚀 MIGRAÇÃO DE PARCELAMENTO - RENDER (PostgreSQL)")
    print("=" * 70)
    print()
    
    sucesso = True
    
    # Adicionar colunas na tabela propostas
    if not adicionar_colunas_parcelamento():
        sucesso = False
    
    # Criar tabela de parcelas
    if not criar_tabela_parcelas():
        sucesso = False
    
    print()
    print("=" * 70)
    if sucesso:
        print("✅ MIGRAÇÃO CONCLUÍDA COM SUCESSO!")
    else:
        print("⚠️ MIGRAÇÃO CONCLUÍDA COM ERROS")
    print("=" * 70)
    print()
    
    if sucesso:
        print("📋 Próximos passos:")
        print("   1. Faça commit e push deste script")
        print("   2. O Render vai fazer deploy automaticamente")
        print("   3. A funcionalidade de parcelamento estará disponível!")
        print()
    else:
        print("⚠️ Verifique os erros acima e tente novamente")
        print()
    
    return 0 if sucesso else 1


if __name__ == '__main__':
    sys.exit(main())
