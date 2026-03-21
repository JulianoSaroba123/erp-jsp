#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Lista todas as propostas disponíveis no sistema.
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app import create_app
from app.extensoes import db
from app.proposta.proposta_model import Proposta

def listar_propostas():
    """Lista todas as propostas no banco."""
    app = create_app()
    
    with app.app_context():
        print("=" * 80)
        print("📋 PROPOSTAS DISPONÍVEIS NO SISTEMA")
        print("=" * 80)
        
        # Buscar todas as propostas (ativas e inativas)
        propostas_ativas = Proposta.query.filter_by(ativo=True).order_by(Proposta.id).all()
        propostas_inativas = Proposta.query.filter_by(ativo=False).order_by(Proposta.id).all()
        
        print(f"\n✅ PROPOSTAS ATIVAS ({len(propostas_ativas)}):")
        print("-" * 80)
        
        if propostas_ativas:
            for p in propostas_ativas:
                print(f"   ID: {p.id:3d} | Código: {p.codigo:15s} | Status: {p.status:12s}")
                print(f"            Título: {p.titulo}")
                print(f"            Cliente: {p.cliente.nome if p.cliente else 'N/A'}")
                print(f"            URL: http://localhost:5000/propostas/{p.id}")
                print(f"            Valor: R$ {p.valor_total:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
                print("-" * 80)
        else:
            print("   Nenhuma proposta ativa encontrada.")
        
        if propostas_inativas:
            print(f"\n❌ PROPOSTAS INATIVAS ({len(propostas_inativas)}):")
            print("-" * 80)
            for p in propostas_inativas:
                print(f"   ID: {p.id:3d} | Código: {p.codigo:15s} | Status: {p.status:12s}")
                print(f"            Título: {p.titulo}")
                print("-" * 80)
        
        print(f"\n📊 TOTAL: {len(propostas_ativas) + len(propostas_inativas)} propostas no banco")
        print(f"   ✅ Ativas: {len(propostas_ativas)}")
        print(f"   ❌ Inativas: {len(propostas_inativas)}")
        
        if propostas_ativas:
            primeira = propostas_ativas[0]
            print(f"\n💡 DICA: Para visualizar uma proposta, acesse:")
            print(f"   http://localhost:5000/propostas/{primeira.id}")
            print(f"   ou")
            print(f"   https://erp-jsp-th5o.onrender.com/propostas/{primeira.id}")

if __name__ == '__main__':
    listar_propostas()
