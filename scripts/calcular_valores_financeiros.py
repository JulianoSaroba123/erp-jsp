"""
Script para calcular e preencher valores financeiros faltantes
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.app import app
from app.extensoes import db
from app.energia_solar.catalogo_model import ProjetoSolar, KitSolar

with app.app_context():
    print("💰 Calculando valores financeiros dos projetos...")
    
    projetos = ProjetoSolar.query.all()
    atualizados = 0
    
    for projeto in projetos:
        if projeto.custo_total and projeto.custo_total > 0:
            # Calcular margem de lucro
            if projeto.valor_venda and projeto.valor_venda > 0:
                margem = ((projeto.valor_venda - projeto.custo_total) / projeto.custo_total * 100)
                projeto.margem_lucro = margem
                
                print(f"📊 Projeto ID {projeto.id}:")
                print(f"   Custo Total: R$ {projeto.custo_total:.2f}")
                print(f"   Valor Venda: R$ {projeto.valor_venda:.2f}")
                print(f"   Margem Lucro: {margem:.1f}%")
                
                # Se tem kit, colocar valor do kit em equipamentos
                if projeto.kit_id:
                    kit = KitSolar.query.get(projeto.kit_id)
                    if kit:
                        projeto.custo_equipamentos = kit.preco
                        # Resto vai para instalação
                        projeto.custo_instalacao = projeto.custo_total - kit.preco
                        projeto.custo_projeto = 0.0
                        
                        print(f"   ✅ Kit encontrado: R$ {kit.preco:.2f}")
                        print(f"   📦 Equipamentos: R$ {projeto.custo_equipamentos:.2f}")
                        print(f"   🔧 Instalação: R$ {projeto.custo_instalacao:.2f}")
                else:
                    # Se não tem kit, distribuir 70% equipamentos, 25% instalação, 5% projeto
                    projeto.custo_equipamentos = projeto.custo_total * 0.70
                    projeto.custo_instalacao = projeto.custo_total * 0.25
                    projeto.custo_projeto = projeto.custo_total * 0.05
                    
                    print(f"   📦 Equipamentos (70%): R$ {projeto.custo_equipamentos:.2f}")
                    print(f"   🔧 Instalação (25%): R$ {projeto.custo_instalacao:.2f}")
                    print(f"   📄 Projeto (5%): R$ {projeto.custo_projeto:.2f}")
                
                atualizados += 1
        else:
            print(f"⚠️ Projeto ID {projeto.id} sem custo total")
    
    db.session.commit()
    print(f"\n✅ {atualizados} projeto(s) atualizado(s) com sucesso!")
