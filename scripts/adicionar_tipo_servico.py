# -*- coding: utf-8 -*-
"""
Script para adicionar o campo tipo_servico na tabela ordem_servico
==================================================================

Este script adiciona a nova coluna tipo_servico para classificação dos serviços.

Autor: JSP Soluções
Data: 2025
"""

import sys
import os

# Adiciona o diretório raiz ao path para importações
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.app import create_app
from app.extensoes import db
import sqlite3

def adicionar_campo_tipo_servico():
    """Adiciona o campo tipo_servico à tabela ordem_servico."""
    
    app = create_app()
    
    with app.app_context():
        print("🔧 Verificando necessidade de adicionar campo tipo_servico...")
        
        try:
            # Tenta acessar o campo para ver se já existe
            db.engine.execute("SELECT tipo_servico FROM ordem_servico LIMIT 1")
            print("✅ Campo tipo_servico já existe na tabela!")
            return
            
        except Exception:
            print("➕ Adicionando campo tipo_servico...")
            
            try:
                # Adiciona a nova coluna
                db.engine.execute("ALTER TABLE ordem_servico ADD COLUMN tipo_servico VARCHAR(100)")
                print("✅ Campo tipo_servico adicionado com sucesso!")
                
                # Atualiza alguns registros existentes com tipos de exemplo
                db.engine.execute("""
                    UPDATE ordem_servico 
                    SET tipo_servico = 'Manutenção Preventiva' 
                    WHERE tipo_servico IS NULL AND status = 'concluida'
                """)
                
                db.engine.execute("""
                    UPDATE ordem_servico 
                    SET tipo_servico = 'Manutenção Corretiva' 
                    WHERE tipo_servico IS NULL AND status IN ('aberta', 'em_andamento')
                """)
                
                print("✅ Tipos de serviço de exemplo adicionados!")
                
            except Exception as e:
                print(f"❌ Erro ao adicionar campo: {e}")
                return False
                
        return True

if __name__ == '__main__':
    print("=" * 60)
    print("🚀 JSP ERP v3.0 - Adição de Campo tipo_servico")
    print("=" * 60)
    
    if adicionar_campo_tipo_servico():
        print("\n✅ Campo tipo_servico configurado com sucesso!")
        print("\nAgora você pode classificar seus serviços com tipos como:")
        print("  • Manutenção Preventiva")
        print("  • Manutenção Corretiva") 
        print("  • Instalação")
        print("  • Reparo")
        print("  • Inspeção")
        print("  • Emergência")
    else:
        print("\n❌ Falha na configuração do campo.")
    
    print("\n" + "=" * 60)