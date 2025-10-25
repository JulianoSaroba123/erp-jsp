#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script direto para adicionar campos sem inicializar Flask
"""

import sqlite3
import os

def main():
    """Adiciona os campos diretamente no SQLite."""
    print("🔧 ADICIONANDO CAMPOS NO BANCO")
    print("=" * 40)
    
    # Conectar diretamente ao banco SQLite
    db_path = "c:\\ERP_JSP\\database\\database.db"
    if not os.path.exists(db_path):
        db_path = "c:\\ERP_JSP\\erp.db"
    if not os.path.exists(db_path):
        db_path = "c:\\ERP_JSP\\instance\\database.db"
    
    print(f"📁 Tentando usar banco: {db_path}")
    
    if not os.path.exists(db_path):
        print("❌ Banco de dados não encontrado!")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Verificar estrutura atual
        cursor.execute("PRAGMA table_info(ordem_servico)")
        columns = [row[1] for row in cursor.fetchall()]
        print(f"📋 Colunas atuais: {len(columns)} encontradas")
        
        # Adicionar campo solicitante
        if 'solicitante' not in columns:
            print("➕ Adicionando campo 'solicitante'...")
            cursor.execute("ALTER TABLE ordem_servico ADD COLUMN solicitante VARCHAR(200)")
            print("✅ Campo 'solicitante' adicionado")
        else:
            print("ℹ️ Campo 'solicitante' já existe")
        
        # Adicionar campo descricao_problema
        if 'descricao_problema' not in columns:
            print("➕ Adicionando campo 'descricao_problema'...")
            cursor.execute("ALTER TABLE ordem_servico ADD COLUMN descricao_problema TEXT")
            print("✅ Campo 'descricao_problema' adicionado")
        else:
            print("ℹ️ Campo 'descricao_problema' já existe")
        
        # Salvar mudanças
        conn.commit()
        
        # Verificar novamente
        cursor.execute("PRAGMA table_info(ordem_servico)")
        new_columns = [row[1] for row in cursor.fetchall()]
        
        print(f"\n🔍 VERIFICAÇÃO FINAL:")
        print(f"   Total de colunas: {len(new_columns)}")
        if 'solicitante' in new_columns:
            print("   ✅ solicitante: presente")
        if 'descricao_problema' in new_columns:
            print("   ✅ descricao_problema: presente")
        
        conn.close()
        print("\n🎉 Campos adicionados com sucesso!")
        return True
        
    except Exception as e:
        print(f"❌ Erro: {e}")
        return False

if __name__ == "__main__":
    success = main()
    if success:
        print("\n📝 PRÓXIMOS PASSOS:")
        print("1. Atualizar formulário HTML")
        print("2. Atualizar rotas para processar os campos")
        print("3. Adicionar campos no PDF")