#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Script para diagnosticar Projeto #8"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app.app import app
from app.extensoes import db
from app.energia_solar.catalogo_model import ProjetoSolar
from app.cliente.cliente_model import Cliente

with app.app_context():
    projeto = ProjetoSolar.query.get(8)
    
    if not projeto:
        print("❌ Projeto #8 não encontrado!")
        sys.exit(1)
    
    print("=" * 80)
    print(f"🔍 DIAGNÓSTICO COMPLETO - PROJETO #{projeto.id}")
    print("=" * 80)
    print()
    
    # PROBLEMA 1: Economia Mensal
    print("💰 PROBLEMA 1: ECONOMIA MENSAL")
    print("-" * 80)
    print(f"  • Consumo mensal: {projeto.consumo_kwh_mes} kWh")
    print(f"  • Tarifa: R$ {float(projeto.tarifa_kwh or 0):.4f}")
    print(f"  • economia_mensal (banco): {projeto.economia_mensal}")
    print(f"  • economia_anual (banco): {projeto.economia_anual}")
    if projeto.consumo_kwh_mes and projeto.tarifa_kwh:
        calculado = float(projeto.consumo_kwh_mes) * float(projeto.tarifa_kwh)
        print(f"  • Cálculo esperado: {projeto.consumo_kwh_mes} × {float(projeto.tarifa_kwh):.4f} = R$ {calculado:.2f}")
    else:
        print(f"  ⚠️ PROBLEMA: Consumo ou tarifa está vazio/zerado!")
    print()
    
    # PROBLEMA 2: Nome do Cliente
    print("👤 PROBLEMA 2: NOME DO CLIENTE")
    print("-" * 80)
    print(f"  • cliente_id: {projeto.cliente_id}")
    print(f"  • nome_cliente (campo): {projeto.nome_cliente}")
    if projeto.cliente_id:
        cliente = Cliente.query.get(projeto.cliente_id)
        if cliente:
            print(f"  • Cliente encontrado: {cliente.nome}")
            print(f"  ✅ Cliente existe no banco")
        else:
            print(f"  ❌ PROBLEMA: cliente_id existe mas cliente não foi encontrado!")
    else:
        print(f"  ⚠️ PROBLEMA: Projeto não tem cliente_id vinculado!")
    print()
    
    # PROBLEMA 3: Área Necessária
    print("📐 PROBLEMA 3: ÁREA NECESSÁRIA")
    print("-" * 80)
    print(f"  • area_necessaria: {projeto.area_necessaria} m²")
    print(f"  • qtd_placas: {projeto.qtd_placas}")
    print(f"  • placa_id: {projeto.placa_id}")
    if projeto.placa_id:
        from app.energia_solar.catalogo_model import PlacaSolar
        placa = PlacaSolar.query.get(projeto.placa_id)
        if placa:
            print(f"  • Placa: {placa.modelo}")
            print(f"  • Dimensões placa: {placa.comprimento}m × {placa.largura}m")
            if placa.comprimento and placa.largura and projeto.qtd_placas:
                area_calc = float(placa.comprimento) * float(placa.largura) * projeto.qtd_placas
                print(f"  • Área calculada: {area_calc:.2f} m²")
                print(f"  • Fórmula: {placa.comprimento} × {placa.largura} × {projeto.qtd_placas} placas")
            else:
                print(f"  ⚠️ PROBLEMA: Placa sem dimensões ou qtd_placas vazio!")
        else:
            print(f"  ❌ PROBLEMA: placa_id existe mas placa não encontrada!")
    else:
        print(f"  ⚠️ PROBLEMA: Projeto não tem placa_id!")
    print()
    
    # PROBLEMA 4: Dados Financeiros
    print("💵 PROBLEMA 4: VALORES FINANCEIROS")
    print("-" * 80)
    print(f"  • valor_venda: R$ {float(projeto.valor_venda or 0):,.2f}")
    print(f"  • custo_total: R$ {float(projeto.custo_total or 0):,.2f}")
    print(f"  • custo_equipamentos: R$ {float(projeto.custo_equipamentos or 0):,.2f}")
    print(f"  • custo_instalacao: R$ {float(projeto.custo_instalacao or 0):,.2f}")
    print(f"  • custo_projeto: R$ {float(projeto.custo_projeto or 0):,.2f}")
    print()
    
    # RESUMO
    print("=" * 80)
    print("📊 RESUMO DOS PROBLEMAS")
    print("=" * 80)
    
    problemas = []
    
    if not projeto.economia_mensal or projeto.economia_mensal == 0:
        problemas.append("❌ Economia mensal zerada - Preencher 'Dados Financeiros'")
    
    if not projeto.nome_cliente and not projeto.cliente_id:
        problemas.append("❌ Sem nome do cliente - Vincular cliente ou preencher nome")
    
    if not projeto.area_necessaria or projeto.area_necessaria == 0:
        problemas.append("❌ Área zerada - Verificar dimensões da placa e quantidade")
    
    if not projeto.valor_venda or projeto.valor_venda == 0:
        problemas.append("❌ Valor zerado - Preencher 'Dados Comerciais' ou 'Financiamento'")
    
    if problemas:
        for p in problemas:
            print(p)
    else:
        print("✅ Nenhum problema encontrado!")
    
    print()
    print("💡 AÇÕES RECOMENDADAS:")
    print("  1. Abrir o Dashboard do Projeto #8")
    print("  2. Clicar em '$ Dados Financeiros' e salvar")
    print("  3. Clicar em '💰 Editar Orçamento' e salvar")
    print("  4. Vincular um cliente ou preencher nome manualmente")
    print("=" * 80)
