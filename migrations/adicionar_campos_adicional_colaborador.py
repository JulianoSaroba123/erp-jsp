# -*- coding: utf-8 -*-
"""
Script de migração para adicionar campos de controle de adicionais de horas.
=============================================================================

Adiciona campos para controlar percentual de adicional cobrado do cliente
e valores de custo/receita por hora dos colaboradores.

Uso: python migrations/adicionar_campos_adicional_colaborador.py

Autor: JSP Soluções
Data: Abril 2026
"""

import sys
import os

# Adicionar o diretório raiz ao path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sqlalchemy import inspect, text
from app.app import create_app
from app.extensoes import db


def adicionar_campos():
    """Adiciona campos de controle de adicionais na tabela ordem_servico_colaborador."""
    
    print("=" * 80)
    print("MIGRAÇÃO: Adicionais de Horas para Colaboradores")
    print("=" * 80)
    
    app = create_app()
    
    with app.app_context():
        try:
            inspector = inspect(db.engine)
            colunas_existentes = [col['name'] for col in inspector.get_columns('ordem_servico_colaborador')]
            
            print(f"\n📋 Tabela 'ordem_servico_colaborador' encontrada")
            print(f"   Total de colunas atuais: {len(colunas_existentes)}")
            
            # Campos a adicionar
            campos_novos = {
                'percentual_adicional_cobranca': 'NUMERIC(5,2)',
                'valor_hora_custo': 'NUMERIC(10,2)',
                'valor_hora_receita': 'NUMERIC(10,2)'
            }
            
            campos_adicionados = []
            campos_ja_existentes = []
            
            for campo, tipo in campos_novos.items():
                if campo in colunas_existentes:
                    campos_ja_existentes.append(campo)
                    print(f"   ⚠️  Campo '{campo}' já existe")
                else:
                    print(f"   ➕ Adicionando campo '{campo}' ({tipo})...")
                    sql = f'ALTER TABLE ordem_servico_colaborador ADD COLUMN {campo} {tipo}'
                    db.session.execute(text(sql))
                    campos_adicionados.append(campo)
                    print(f"   ✓ Campo '{campo}' adicionado com sucesso!")
            
            if campos_adicionados:
                db.session.commit()
                print(f"\n✅ {len(campos_adicionados)} campo(s) adicionado(s) com sucesso!")
            else:
                print("\n✓ Todos os campos já existem - nada a fazer")
            
            # Mostrar resumo
            print("\n" + "=" * 80)
            print("📊 RESUMO DA MIGRAÇÃO")
            print("=" * 80)
            print("\n🆕 Novos Campos Adicionados:")
            print("   - percentual_adicional_cobranca: Percentual customizado para cobrar do cliente")
            print("   - valor_hora_custo: Valor/hora pago ao colaborador (com adicional)")
            print("   - valor_hora_receita: Valor/hora cobrado do cliente (com adicional)")
            
            print("\n📌 Regras de Adicional (Padrão):")
            print("   - Após 17:00 em dias normais: 50%")
            print("   - Sábados: 50%")
            print("   - Domingos e feriados: 100%")
            
            print("\n💡 Como Usar:")
            print("   1. Ao lançar horas de colaborador, o sistema calcula automaticamente")
            print("      o percentual de adicional baseado no dia/horário")
            print("   2. Por padrão, cobra do cliente o mesmo percentual pago ao colaborador")
            print("   3. Se precisar negociar um percentual diferente com o cliente,")
            print("      preencha o campo 'percentual_adicional_cobranca'")
            print("   4. Exemplo: Paga 100% ao colaborador, mas cobra 50% do cliente")
            
            print("\n" + "=" * 80)
            print("✅ MIGRAÇÃO CONCLUÍDA COM SUCESSO!")
            print("=" * 80)
            
        except Exception as e:
            db.session.rollback()
            print(f"\n❌ ERRO ao adicionar campos: {str(e)}")
            print(f"\nDetalhes: {type(e).__name__}")
            import traceback
            traceback.print_exc()
            sys.exit(1)


if __name__ == "__main__":
    adicionar_campos()
