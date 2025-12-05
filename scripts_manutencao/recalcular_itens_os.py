#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script para recalcular totais dos itens de serviço
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.app import create_app
from app.extensoes import db
from app.ordem_servico.ordem_servico_model import OrdemServico, OrdemServicoItem

def recalcular_itens():
    """Recalcula totais de todos os itens de serviço."""
    app = create_app()
    
    with app.app_context():
        # Busca todos os itens
        itens = OrdemServicoItem.query.all()
        
        print(f"\n🔧 Recalculando {len(itens)} itens de serviço...\n")
        
        corrigidos = 0
        for item in itens:
            total_antigo = float(item.valor_total or 0)
            
            # Recalcula
            item.calcular_total()
            total_novo = float(item.valor_total or 0)
            
            if abs(total_antigo - total_novo) > 0.01:
                print(f"OS {item.ordem_servico.numero} - {item.descricao}:")
                print(f"  {item.quantidade} × R$ {item.valor_unitario} = R$ {total_antigo:.2f} → R$ {total_novo:.2f}")
                corrigidos += 1
        
        # Salva alterações
        if corrigidos > 0:
            db.session.commit()
            print(f"\n✅ {corrigidos} itens corrigidos!")
            
            # Agora recalcula valores das OSs
            print("\n🔧 Recalculando totais das OSs...\n")
            ordens = OrdemServico.query.filter_by(ativo=True).all()
            
            for ordem in ordens:
                ordem.valor_servico = ordem.valor_total_servicos
                ordem.valor_pecas = ordem.valor_total_produtos
                ordem.valor_total = ordem.valor_total_calculado_novo
                print(f"OS {ordem.numero}: Serviços R$ {ordem.valor_servico:.2f} | Total R$ {ordem.valor_total:.2f}")
            
            db.session.commit()
            print("\n✅ Todas as OSs recalculadas!")
        else:
            print("\n✅ Todos os totais já estão corretos!")

if __name__ == '__main__':
    recalcular_itens()
