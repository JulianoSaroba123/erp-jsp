#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Fix database columns on Render"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.app import create_app
from app.extensoes import db
from sqlalchemy import text

print("Iniciando correcao do banco de dados...")

app = create_app()

with app.app_context():
    print("Criando tabelas base...")
    db.create_all()
    print("Tabelas base OK")
    
    # Lista de comandos SQL - cada um será tentado individualmente
    comandos = [
        # Colunas da tabela ordem_servico
        ("ordem_servico", "intervalo_almoco", 
         "ALTER TABLE ordem_servico ADD COLUMN intervalo_almoco INTEGER DEFAULT 60"),
        
        ("ordem_servico", "hora_saida_almoco",
         "ALTER TABLE ordem_servico ADD COLUMN hora_saida_almoco TIME"),
        
        ("ordem_servico", "hora_retorno_almoco",
         "ALTER TABLE ordem_servico ADD COLUMN hora_retorno_almoco TIME"),
        
        ("ordem_servico", "hora_saida",
         "ALTER TABLE ordem_servico ADD COLUMN hora_saida TIME"),
        
        ("ordem_servico", "hora_entrada_extra",
         "ALTER TABLE ordem_servico ADD COLUMN hora_entrada_extra TIME"),
        
        ("ordem_servico", "hora_saida_extra",
         "ALTER TABLE ordem_servico ADD COLUMN hora_saida_extra TIME"),
        
        ("ordem_servico", "horas_normais",
         "ALTER TABLE ordem_servico ADD COLUMN horas_normais NUMERIC(10,2)"),
        
        ("ordem_servico", "horas_extras",
         "ALTER TABLE ordem_servico ADD COLUMN horas_extras NUMERIC(10,2)"),
        
        # Colunas da tabela ordem_servico_colaborador
        ("ordem_servico_colaborador", "hora_entrada_manha",
         "ALTER TABLE ordem_servico_colaborador ADD COLUMN hora_entrada_manha TIME"),
        
        ("ordem_servico_colaborador", "hora_saida_manha",
         "ALTER TABLE ordem_servico_colaborador ADD COLUMN hora_saida_manha TIME"),
        
        ("ordem_servico_colaborador", "hora_entrada_tarde",
         "ALTER TABLE ordem_servico_colaborador ADD COLUMN hora_entrada_tarde TIME"),
        
        ("ordem_servico_colaborador", "hora_saida_tarde",
         "ALTER TABLE ordem_servico_colaborador ADD COLUMN hora_saida_tarde TIME"),
        
        ("ordem_servico_colaborador", "hora_entrada_extra",
         "ALTER TABLE ordem_servico_colaborador ADD COLUMN hora_entrada_extra TIME"),
        
        ("ordem_servico_colaborador", "hora_saida_extra",
         "ALTER TABLE ordem_servico_colaborador ADD COLUMN hora_saida_extra TIME"),
        
        ("ordem_servico_colaborador", "horas_normais",
         "ALTER TABLE ordem_servico_colaborador ADD COLUMN horas_normais NUMERIC(10,2)"),
        
        ("ordem_servico_colaborador", "horas_extras",
         "ALTER TABLE ordem_servico_colaborador ADD COLUMN horas_extras NUMERIC(10,2)"),
        
        ("ordem_servico_colaborador", "km_inicial",
         "ALTER TABLE ordem_servico_colaborador ADD COLUMN km_inicial INTEGER"),
        
        ("ordem_servico_colaborador", "km_final",
         "ALTER TABLE ordem_servico_colaborador ADD COLUMN km_final INTEGER"),
    ]
    
    sucesso = 0
    ja_existe = 0
    erros = 0
    
    print(f"\nProcessando {len(comandos)} colunas...\n")
    
    for tabela, coluna, sql in comandos:
        try:
            db.session.execute(text(sql))
            db.session.commit()
            print(f"[OK] {tabela}.{coluna} - ADICIONADA")
            sucesso += 1
        except Exception as e:
            erro_str = str(e).lower()
            if 'already exists' in erro_str or 'duplicate column' in erro_str:
                print(f"[INFO] {tabela}.{coluna} - JA EXISTE")
                ja_existe += 1
                db.session.rollback()
            else:
                print(f"[ERRO] {tabela}.{coluna} - {e}")
                erros += 1
                db.session.rollback()
    
    print(f"\n{'='*60}")
    print(f"RESUMO:")
    print(f"   Adicionadas: {sucesso}")
    print(f"   Ja existiam: {ja_existe}")
    print(f"   Erros: {erros}")
    print(f"{'='*60}")
    
    if erros == 0:
        print("\nMIGRACAO CONCLUIDA COM SUCESSO!")
    else:
        print(f"\nMIGRACAO CONCLUIDA COM {erros} ERRO(S)")
        sys.exit(1)
