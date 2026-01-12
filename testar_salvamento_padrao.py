#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Script para testar salvamento dos dados do padrão de entrada"""

import os
import sys

# Adicionar o diretório raiz ao path
sys.path.insert(0, os.path.dirname(__file__))

from app.app import create_app
from app.extensoes import db
from app.energia_solar.catalogo_model import ProjetoSolar

# Criar app
app = create_app()

with app.app_context():
    # Buscar um projeto existente
    projeto = ProjetoSolar.query.first()
    
    if not projeto:
        print("❌ Nenhum projeto encontrado no banco")
        sys.exit(1)
    
    print(f"📋 Projeto ID: {projeto.id}")
    print(f"   Cliente ID: {projeto.cliente_id or 'N/A'}")
    print("\n✅ Dados do Padrão de Entrada salvos:")
    print(f"  - Tipo instalação: {projeto.tipo_instalacao or 'N/A'}")
    print(f"  - Quantidade de fases: {projeto.qtd_fases or 'N/A'}")
    print(f"  - Cabo fase bitola: {projeto.cabo_fase_bitola or 'N/A'} mm²")
    print(f"  - Cabo neutro bitola: {projeto.cabo_neutro_bitola or 'N/A'} mm²")
    print(f"  - Quantidade terra: {projeto.qtd_terra or 'N/A'}")
    print(f"  - Cabo terra bitola: {projeto.cabo_terra_bitola or 'N/A'} mm²")
    print(f"  - Observações: {projeto.padrao_observacoes or 'N/A'}")
    print(f"  - Disjuntor CA: {projeto.disjuntor_ca or 'N/A'} A")
    
    print("\n✅ Proteções String Box:")
    print(f"  - Proteção CC: {projeto.protecao_cc_tipo or 'N/A'} - {projeto.protecao_cc_corrente or '-'}A")
    print(f"  - Proteção CA: {projeto.protecao_ca_tipo or 'N/A'} - {projeto.protecao_ca_corrente or '-'}A")
    
    print("\n✅ Cabos:")
    print(f"  - Cabo CC: {projeto.cabo_cc or 'N/A'} mm²")
    print(f"  - Cabo CA: {projeto.cabo_ca or 'N/A'} mm²")
