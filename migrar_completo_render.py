#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script COMPLETO de migração para o Render
==========================================

Adiciona:
1. Coluna tipo_os na tabela ordem_servico
2. Tabela colaborador
3. Tabela ordem_servico_colaborador
"""

import os
import sys

# Adiciona o diretório raiz ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.app import create_app
from app.extensoes import db

def migrar_render():
    """Executa migração completa no Render."""
    
    app = create_app()
    
    with app.app_context():
        try:
            print("=" * 80)
            print("🚀 INICIANDO MIGRAÇÃO COMPLETA NO RENDER")
            print("=" * 80)
            
            # ====================================================================
            # 1. ADICIONAR COLUNA tipo_os
            # ====================================================================
            print("\n📝 1. Verificando coluna tipo_os...")
            
            check_tipo_os = """
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name='ordem_servico' AND column_name='tipo_os';
            """
            
            result = db.session.execute(db.text(check_tipo_os)).fetchone()
            
            if not result:
                print("   ➕ Adicionando coluna tipo_os...")
                db.session.execute(db.text("""
                    ALTER TABLE ordem_servico 
                    ADD COLUMN tipo_os VARCHAR(20) DEFAULT 'comercial';
                """))
                db.session.commit()
                print("   ✅ Coluna tipo_os adicionada!")
            else:
                print("   ✅ Coluna tipo_os já existe!")
            
            # ====================================================================
            # 2. CRIAR TABELA colaborador
            # ====================================================================
            print("\n📝 2. Verificando tabela colaborador...")
            
            check_colaborador = """
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'colaborador'
            );
            """
            
            existe_colaborador = db.session.execute(db.text(check_colaborador)).scalar()
            
            if not existe_colaborador:
                print("   ➕ Criando tabela colaborador...")
                db.session.execute(db.text("""
                    CREATE TABLE colaborador (
                        id SERIAL PRIMARY KEY,
                        nome VARCHAR(200) NOT NULL,
                        cpf VARCHAR(14),
                        cargo VARCHAR(100),
                        celular VARCHAR(20),
                        telefone VARCHAR(20),
                        especialidade TEXT,
                        valor_hora NUMERIC(10, 2) DEFAULT 0.00,
                        criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        atualizado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        ativo BOOLEAN DEFAULT true
                    );
                """))
                db.session.commit()
                print("   ✅ Tabela colaborador criada!")
            else:
                print("   ✅ Tabela colaborador já existe!")
            
            # ====================================================================
            # 3. CRIAR TABELA ordem_servico_colaborador
            # ====================================================================
            print("\n📝 3. Verificando tabela ordem_servico_colaborador...")
            
            check_os_colab = """
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'ordem_servico_colaborador'
            );
            """
            
            existe_os_colab = db.session.execute(db.text(check_os_colab)).scalar()
            
            if not existe_os_colab:
                print("   ➕ Criando tabela ordem_servico_colaborador...")
                db.session.execute(db.text("""
                    CREATE TABLE ordem_servico_colaborador (
                        id SERIAL PRIMARY KEY,
                        colaborador_id INTEGER NOT NULL,
                        ordem_servico_id INTEGER NOT NULL,
                        data_trabalho DATE NOT NULL,
                        hora_inicio TIME,
                        hora_fim TIME,
                        descricao_atividade TEXT,
                        total_horas NUMERIC(10, 2),
                        criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        atualizado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        ativo BOOLEAN DEFAULT true,
                        FOREIGN KEY (colaborador_id) REFERENCES colaborador(id),
                        FOREIGN KEY (ordem_servico_id) REFERENCES ordem_servico(id)
                    );
                """))
                db.session.commit()
                print("   ✅ Tabela ordem_servico_colaborador criada!")
            else:
                print("   ✅ Tabela ordem_servico_colaborador já existe!")
            
            # ====================================================================
            # 4. ATUALIZAR REGISTROS EXISTENTES
            # ====================================================================
            print("\n📝 4. Atualizando registros existentes...")
            
            db.session.execute(db.text("""
                UPDATE ordem_servico 
                SET tipo_os = 'comercial' 
                WHERE tipo_os IS NULL;
            """))
            db.session.commit()
            
            # Contar registros
            count_os = db.session.execute(db.text("SELECT COUNT(*) FROM ordem_servico")).scalar()
            count_comercial = db.session.execute(db.text("SELECT COUNT(*) FROM ordem_servico WHERE tipo_os = 'comercial'")).scalar()
            count_operacional = db.session.execute(db.text("SELECT COUNT(*) FROM ordem_servico WHERE tipo_os = 'operacional'")).scalar()
            count_colaboradores = db.session.execute(db.text("SELECT COUNT(*) FROM colaborador")).scalar()
            
            print(f"   ✅ Total de OS: {count_os}")
            print(f"   ✅ OS Comerciais: {count_comercial}")
            print(f"   ✅ OS Operacionais: {count_operacional}")
            print(f"   ✅ Colaboradores cadastrados: {count_colaboradores}")
            
            print("\n" + "=" * 80)
            print("✅ MIGRAÇÃO CONCLUÍDA COM SUCESSO!")
            print("=" * 80)
            
        except Exception as e:
            print(f"\n❌ ERRO: {e}")
            import traceback
            traceback.print_exc()
            db.session.rollback()
            raise

if __name__ == '__main__':
    migrar_render()
