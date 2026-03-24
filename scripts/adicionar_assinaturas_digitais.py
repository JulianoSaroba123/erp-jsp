# -*- coding: utf-8 -*-
"""
Adiciona colunas de assinaturas digitais na tabela ordem_servico.

Execução:
    python scripts/adicionar_assinaturas_digitais.py
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import inspect, text
from app.app import create_app
from app.extensoes import db


COLUNAS = {
    'assinatura_cliente': 'TEXT',
    'assinatura_cliente_nome': 'VARCHAR(200)',
    'assinatura_cliente_data': 'TIMESTAMP',
    'assinatura_tecnico': 'TEXT',
    'assinatura_tecnico_nome': 'VARCHAR(200)',
    'assinatura_tecnico_data': 'TIMESTAMP',
}


def main():
    app = create_app()
    
    with app.app_context():
        inspector = inspect(db.engine)
        colunas_existentes = [col['name'] for col in inspector.get_columns('ordem_servico')]
        
        print("=" * 60)
        print("ADIÇÃO DE ASSINATURAS DIGITAIS")
        print("=" * 60)
        print(f"Tabela: ordem_servico")
        print(f"Novas colunas: {len(COLUNAS)}")
        print("-" * 60)
        
        adicionadas = 0
        ja_existem = 0
        
        for coluna, tipo in COLUNAS.items():
            if coluna in colunas_existentes:
                print(f"  ℹ️  {coluna:<30} - JÁ EXISTE")
                ja_existem += 1
            else:
                try:
                    sql = f"ALTER TABLE ordem_servico ADD COLUMN {coluna} {tipo}"
                    db.session.execute(text(sql))
                    db.session.commit()
                    print(f"  ✅ {coluna:<30} - ADICIONADA")
                    adicionadas += 1
                except Exception as e:
                    print(f"  ❌ {coluna:<30} - ERRO: {e}")
                    db.session.rollback()
        
        print("-" * 60)
        print(f"Resultado:")
        print(f"  ✅ Adicionadas: {adicionadas}")
        print(f"  ℹ️  Já existiam: {ja_existem}")
        print("=" * 60)
        
        if adicionadas > 0:
            print("\n✨ Migração concluída com sucesso!")
            print("💡 Você pode agora usar o sistema de assinaturas digitais.")
        else:
            print("\n⚠️  Nenhuma coluna foi adicionada (todas já existem).")


if __name__ == '__main__':
    main()
