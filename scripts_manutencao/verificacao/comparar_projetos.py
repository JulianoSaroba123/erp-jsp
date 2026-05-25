#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Script para comparar Projeto #2 (Michel) com outros projetos"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app.app import app
from app.extensoes import db
from app.energia_solar.catalogo_model import ProjetoSolar

with app.app_context():
    # Buscar todos os projetos
    projetos = ProjetoSolar.query.order_by(ProjetoSolar.id).all()
    
    if not projetos:
        print("❌ Nenhum projeto encontrado!")
        sys.exit(1)
    
    print("=" * 80)
    print("📊 COMPARAÇÃO DE PROJETOS - Economia Mensal")
    print("=" * 80)
    print()
    
    for projeto in projetos:
        print(f"📋 Projeto #{projeto.id} - {projeto.nome_cliente}")
        print(f"   Consumo: {projeto.consumo_kwh_mes or 0} kWh/mês")
        print(f"   Tarifa: R$ {float(projeto.tarifa_kwh or 0):.4f}")
        print(f"   📊 economia_mensal (tipo): {type(projeto.economia_mensal)}")
        print(f"   💰 economia_mensal (valor): {projeto.economia_mensal}")
        print(f"   💰 economia_mensal (repr): {repr(projeto.economia_mensal)}")
        
        # Verificar se é None, 0, ou tem valor
        if projeto.economia_mensal is None:
            print(f"   ⚠️  STATUS: economia_mensal é None")
        elif projeto.economia_mensal == 0:
            print(f"   ⚠️  STATUS: economia_mensal é ZERO")
        elif float(projeto.economia_mensal) == 0:
            print(f"   ⚠️  STATUS: economia_mensal converte para zero")
        else:
            print(f"   ✅ STATUS: economia_mensal = R$ {float(projeto.economia_mensal):.2f}")
        
        # Testar a condição do if
        if projeto.economia_mensal and projeto.economia_mensal > 0:
            print(f"   ✅ Passa no IF: (economia_mensal and economia_mensal > 0)")
        else:
            print(f"   ❌ NÃO passa no IF: vai recalcular")
            calc = float(projeto.consumo_kwh_mes or 0) * float(projeto.tarifa_kwh or 0)
            print(f"   🔢 Cálculo: {projeto.consumo_kwh_mes or 0} × {float(projeto.tarifa_kwh or 0):.4f} = R$ {calc:.2f}")
        
        print("-" * 80)
        print()
    
    print("=" * 80)
    print("🔍 ANÁLISE")
    print("=" * 80)
    print("Se algum projeto tiver 'NÃO passa no IF', o valor está sendo recalculado")
    print("ao invés de usar o valor salvo no banco.")
    print()
