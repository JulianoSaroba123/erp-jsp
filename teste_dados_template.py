#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Teste simples dos dados sem renderização
"""

import sys
import os

# Adicionar o diretório raiz ao path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__))))

from app.app import create_app
from app.extensoes import db
from app.ordem_servico.ordem_servico_model import OrdemServico

def main():
    """Testa os dados que devem aparecer no template."""
    print("🎯 DADOS PARA TEMPLATE PDF")
    print("=" * 40)
    
    app = create_app()
    
    with app.app_context():
        ordem = OrdemServico.query.get(1)
        
        print("🔧 TEMPLATE DEVE MOSTRAR:")
        print("=" * 40)
        
        for servico in ordem.servicos:
            horas = servico.quantidade_horas or 0
            valor_hora = servico.valor_hora or 0
            total = horas * valor_hora
            
            print(f"📝 {servico.descricao}")
            print(f"   {{ servico.quantidade_horas or 0 }} = {horas}")
            print(f"   {{ servico.valor_hora or 0 }} = {valor_hora}")
            print(f"   Template calculará: {horas} × {valor_hora} = {total}")
            print()
        
        print("💰 SUBTOTAL:")
        subtotal = sum((s.quantidade_horas or 0) * (s.valor_hora or 0) for s in ordem.servicos)
        print(f"   Calculado pelos itens: R$ {subtotal:.2f}")
        print(f"   ordem.valor_servico: R$ {ordem.valor_servico:.2f}")
        
        print("\n✅ CONCLUSÃO:")
        if subtotal > 0:
            print("   Os dados estão CORRETOS no banco!")
            print("   O template DEVE mostrar valores não-zerados!")
            print("\n🔍 POSSÍVEIS CAUSAS DO PROBLEMA:")
            print("   1. Cache do navegador - tente Ctrl+F5")
            print("   2. PDF antigo ainda aberto")
            print("   3. Servidor renderizando template antigo")
        else:
            print("   ❌ Problema nos dados!")

if __name__ == "__main__":
    main()