#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Script para listar todos os projetos"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app.app import app
from app.extensoes import db
from app.energia_solar.catalogo_model import ProjetoSolar

with app.app_context():
    projetos = ProjetoSolar.query.order_by(ProjetoSolar.id.desc()).all()
    
    print("=" * 80)
    print(f"📋 TODOS OS PROJETOS NO BANCO (Total: {len(projetos)})")
    print("=" * 80)
    print()
    
    for projeto in projetos:
        print(f"ID: {projeto.id:2d} | Nome: {projeto.nome_cliente or 'SEM NOME':30s} | Economia: R$ {float(projeto.economia_mensal or 0):8.2f} | Valor: R$ {float(projeto.valor_venda or 0):10.2f}")
    
    print()
    print("=" * 80)
