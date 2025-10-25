#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Adicionar Colunas de Anexos e Pagamento
======================================

Adiciona as novas colunas na tabela ordem_servico:
- descricao_pagamento: TEXT (descrição detalhada das condições de pagamento)  
- observacoes_anexos: TEXT (observações sobre os anexos enviados)

Garante que os dados existentes sejam preservados.
"""

from app.app import create_app
from app.extensoes import db
from sqlalchemy import text
import sys

def add_new_columns():
    """Adiciona as novas colunas na tabela ordem_servico"""
    
    app = create_app()
    
    with app.app_context():
        print("ADICIONANDO NOVAS COLUNAS - ANEXOS E PAGAMENTO")
        print("=" * 50)
        
        try:
            # Verifica se as colunas já existem
            print("1. Verificando colunas existentes...")
            
            result = db.session.execute(text("PRAGMA table_info(ordem_servico)"))
            columns = [row[1] for row in result.fetchall()]  # row[1] é o nome da coluna
            
            print(f"   Colunas atuais: {len(columns)}")
            
            # Adiciona descricao_pagamento se não existir
            if 'descricao_pagamento' not in columns:
                print("2. Adicionando coluna 'descricao_pagamento'...")
                db.session.execute(text("""
                    ALTER TABLE ordem_servico 
                    ADD COLUMN descricao_pagamento TEXT
                """))
                print("   ✅ Coluna 'descricao_pagamento' adicionada!")
            else:
                print("2. Coluna 'descricao_pagamento' já existe")
            
            # Adiciona observacoes_anexos se não existir  
            if 'observacoes_anexos' not in columns:
                print("3. Adicionando coluna 'observacoes_anexos'...")
                db.session.execute(text("""
                    ALTER TABLE ordem_servico 
                    ADD COLUMN observacoes_anexos TEXT
                """))
                print("   ✅ Coluna 'observacoes_anexos' adicionada!")
            else:
                print("3. Coluna 'observacoes_anexos' já existe")
            
            # Verifica se a tabela de anexos existe
            print("4. Verificando tabela de anexos...")
            
            try:
                result = db.session.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name='ordem_servico_anexo'"))
                anexo_table_exists = result.fetchone() is not None
                
                if not anexo_table_exists:
                    print("   Criando tabela ordem_servico_anexo...")
                    db.session.execute(text("""
                        CREATE TABLE ordem_servico_anexo (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            ordem_servico_id INTEGER NOT NULL,
                            nome_original VARCHAR(255) NOT NULL,
                            nome_arquivo VARCHAR(255) NOT NULL,
                            tipo_arquivo VARCHAR(100),
                            tamanho INTEGER,
                            data_upload DATETIME DEFAULT CURRENT_TIMESTAMP,
                            criado_em DATETIME DEFAULT CURRENT_TIMESTAMP,
                            atualizado_em DATETIME DEFAULT CURRENT_TIMESTAMP,
                            ativo BOOLEAN DEFAULT 1,
                            FOREIGN KEY (ordem_servico_id) REFERENCES ordem_servico (id)
                        )
                    """))
                    print("   ✅ Tabela ordem_servico_anexo criada!")
                else:
                    print("   Tabela ordem_servico_anexo já existe")
                    
            except Exception as e:
                print(f"   ⚠️ Erro ao verificar/criar tabela anexo: {e}")
            
            # Confirma as mudanças
            db.session.commit()
            
            print("\n5. Verificando resultado final...")
            
            # Verifica novamente as colunas
            result = db.session.execute(text("PRAGMA table_info(ordem_servico)"))
            new_columns = [row[1] for row in result.fetchall()]
            
            print(f"   Total de colunas: {len(new_columns)}")
            print(f"   Tem descricao_pagamento: {'descricao_pagamento' in new_columns}")
            print(f"   Tem observacoes_anexos: {'observacoes_anexos' in new_columns}")
            
            print("\n" + "=" * 50)
            print("✅ COLUNAS ADICIONADAS COM SUCESSO!")
            print("\n💡 Próximos passos:")
            print("   1. Execute: python test_anexos_complete.py server")
            print("   2. Acesse: http://localhost:5007/ordem_servico/novo") 
            print("   3. Teste os novos campos de anexos e pagamento")
            
        except Exception as e:
            print(f"❌ Erro: {e}")
            db.session.rollback()
            return False
            
        return True

if __name__ == '__main__':
    success = add_new_columns()
    if not success:
        sys.exit(1)