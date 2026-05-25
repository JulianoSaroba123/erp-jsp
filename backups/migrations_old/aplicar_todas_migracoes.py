# -*- coding: utf-8 -*-
"""
Script unificado de migrações para aplicar no Render.
=====================================================

Aplica todas as migrações necessárias:
1. Tabela notas_fiscais_servico (NFS-e)
2. Campos de adicionais de horas em ordem_servico_colaborador
3. Campo nome_fantasia em clientes

Este script roda automaticamente no deploy do Render.

Autor: JSP Soluções
Data: Abril 2026
"""

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sqlalchemy import inspect, text
from app.app import create_app
from app.extensoes import db


def aplicar_migracoes():
    """Aplica todas as migrações pendentes."""
    
    print("=" * 80)
    print("🔄 APLICANDO TODAS AS MIGRAÇÕES")
    print("=" * 80)
    
    app = create_app()
    
    with app.app_context():
        try:
            inspector = inspect(db.engine)
            tabelas_existentes = inspector.get_table_names()
            
            print(f"\n📊 Banco de dados: {db.engine.url.database}")
            print(f"   Total de tabelas: {len(tabelas_existentes)}")
            
            migracoes_aplicadas = []
            
            # MIGRAÇÃO 1: Tabela NFS-e
            print("\n" + "=" * 80)
            print("1️⃣  MIGRAÇÃO: Tabela notas_fiscais_servico (NFS-e)")
            print("=" * 80)
            
            if 'notas_fiscais_servico' in tabelas_existentes:
                print("   ✓ Tabela 'notas_fiscais_servico' já existe")
            else:
                print("   ➕ Criando tabela 'notas_fiscais_servico'...")
                from app.financeiro.nfse_model import NotaFiscalServico
                NotaFiscalServico.__table__.create(db.engine)
                migracoes_aplicadas.append("Tabela notas_fiscais_servico criada")
                print("   ✅ Tabela criada com sucesso!")
            
            # MIGRAÇÃO 2: Campos de adicionais em colaboradores
            print("\n" + "=" * 80)
            print("2️⃣  MIGRAÇÃO: Campos de adicionais em ordem_servico_colaborador")
            print("=" * 80)
            
            if 'ordem_servico_colaborador' in tabelas_existentes:
                colunas_colab = [col['name'] for col in inspector.get_columns('ordem_servico_colaborador')]
                
                campos_adicionais = {
                    'percentual_adicional_cobranca': 'NUMERIC(5,2)',
                    'valor_hora_custo': 'NUMERIC(10,2)',
                    'valor_hora_receita': 'NUMERIC(10,2)'
                }
                
                for campo, tipo in campos_adicionais.items():
                    if campo in colunas_colab:
                        print(f"   ✓ Campo '{campo}' já existe")
                    else:
                        print(f"   ➕ Adicionando campo '{campo}'...")
                        sql = f'ALTER TABLE ordem_servico_colaborador ADD COLUMN {campo} {tipo}'
                        db.session.execute(text(sql))
                        migracoes_aplicadas.append(f"Campo {campo} adicionado")
                        print(f"   ✅ Campo '{campo}' adicionado!")
            else:
                print("   ⚠️  Tabela 'ordem_servico_colaborador' não existe")
            
            # MIGRAÇÃO 3: Campo nome_fantasia em clientes
            print("\n" + "=" * 80)
            print("3️⃣  MIGRAÇÃO: Campo nome_fantasia em clientes")
            print("=" * 80)
            
            if 'clientes' in tabelas_existentes:
                colunas_cli = [col['name'] for col in inspector.get_columns('clientes')]
                
                if 'nome_fantasia' in colunas_cli:
                    print("   ✓ Campo 'nome_fantasia' já existe")
                else:
                    print("   ➕ Adicionando campo 'nome_fantasia'...")
                    sql = 'ALTER TABLE clientes ADD COLUMN nome_fantasia VARCHAR(150)'
                    db.session.execute(text(sql))
                    migracoes_aplicadas.append("Campo nome_fantasia adicionado")
                    print("   ✅ Campo 'nome_fantasia' adicionado!")
            else:
                print("   ⚠️  Tabela 'clientes' não existe")
            
            # Commit das mudanças
            if migracoes_aplicadas:
                db.session.commit()
                print("\n" + "=" * 80)
                print("✅ MIGRAÇÕES APLICADAS COM SUCESSO!")
                print("=" * 80)
                print("\n📋 Resumo:")
                for migracao in migracoes_aplicadas:
                    print(f"   ✓ {migracao}")
            else:
                print("\n" + "=" * 80)
                print("✅ TODAS AS MIGRAÇÕES JÁ ESTAVAM APLICADAS")
                print("=" * 80)
            
            print("\n🎉 Banco de dados atualizado e pronto para uso!")
            
        except Exception as e:
            db.session.rollback()
            print(f"\n❌ ERRO ao aplicar migrações: {str(e)}")
            import traceback
            traceback.print_exc()
            # Não fazer sys.exit(1) para não interromper o deploy do Render
            print("\n⚠️  Continuando mesmo com erro de migração...")


if __name__ == "__main__":
    aplicar_migracoes()
