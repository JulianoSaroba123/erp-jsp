#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Adiciona novos campos: solicitante e descricao_problema
"""

import sys
import os

# Adicionar o diretório raiz ao path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__))))

from app.app import create_app
from app.extensoes import db

def main():
    """Adiciona os novos campos ao banco de dados."""
    print("🔧 ADICIONANDO NOVOS CAMPOS")
    print("=" * 40)
    
    app = create_app()
    
    with app.app_context():
        try:
            # Adicionar coluna solicitante
            print("📝 Adicionando campo 'solicitante'...")
            db.engine.execute("ALTER TABLE ordem_servico ADD COLUMN solicitante VARCHAR(200)")
            print("✅ Campo 'solicitante' adicionado")
            
        except Exception as e:
            if "duplicate column name" in str(e).lower() or "already exists" in str(e).lower():
                print("ℹ️ Campo 'solicitante' já existe")
            else:
                print(f"⚠️ Erro ao adicionar 'solicitante': {e}")
        
        try:
            # Adicionar coluna descricao_problema
            print("📝 Adicionando campo 'descricao_problema'...")
            db.engine.execute("ALTER TABLE ordem_servico ADD COLUMN descricao_problema TEXT")
            print("✅ Campo 'descricao_problema' adicionado")
            
        except Exception as e:
            if "duplicate column name" in str(e).lower() or "already exists" in str(e).lower():
                print("ℹ️ Campo 'descricao_problema' já existe")
            else:
                print(f"⚠️ Erro ao adicionar 'descricao_problema': {e}")
        
        # Verificar se os campos foram adicionados
        print("\n🔍 VERIFICANDO ESTRUTURA DA TABELA...")
        try:
            result = db.engine.execute("PRAGMA table_info(ordem_servico)")
            columns = [row[1] for row in result]
            
            if 'solicitante' in columns:
                print("✅ Campo 'solicitante' presente na tabela")
            else:
                print("❌ Campo 'solicitante' não encontrado")
                
            if 'descricao_problema' in columns:
                print("✅ Campo 'descricao_problema' presente na tabela")
            else:
                print("❌ Campo 'descricao_problema' não encontrado")
                
        except Exception as e:
            print(f"❌ Erro ao verificar tabela: {e}")
        
        print("\n🎉 Processo concluído!")
        print("👥 Campo 'solicitante': Nome da pessoa que solicitou")
        print("📋 Campo 'descricao_problema': Descrição do problema/defeito")

if __name__ == "__main__":
    main()