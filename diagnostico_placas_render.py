#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Script para diagnosticar dimensões das placas no banco"""

import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

from app.app import create_app
from app.extensoes import db
from app.energia_solar.catalogo_model import PlacaSolar

app = create_app()

with app.app_context():
    placas = PlacaSolar.query.all()
    
    print(f"\n📊 Total de placas: {len(placas)}")
    print("\n🔍 Verificando dimensões:")
    print("-" * 80)
    
    placas_sem_dimensao = []
    placas_com_dimensao = []
    
    for placa in placas:
        if placa.largura and placa.comprimento:
            placas_com_dimensao.append(placa)
            print(f"✅ {placa.modelo} ({placa.fabricante})")
            print(f"   Largura: {placa.largura}mm | Comprimento: {placa.comprimento}mm")
        else:
            placas_sem_dimensao.append(placa)
            print(f"❌ {placa.modelo} ({placa.fabricante})")
            print(f"   Largura: {placa.largura or 'NULL'} | Comprimento: {placa.comprimento or 'NULL'}")
        print()
    
    print("-" * 80)
    print(f"\n📈 Resumo:")
    print(f"   ✅ Com dimensões: {len(placas_com_dimensao)}")
    print(f"   ❌ Sem dimensões: {len(placas_sem_dimensao)}")
    
    if placas_sem_dimensao:
        print(f"\n⚠️  ATENÇÃO: {len(placas_sem_dimensao)} placas sem dimensões cadastradas!")
        print("   O sistema usará valores padrão (992mm x 1650mm)")
