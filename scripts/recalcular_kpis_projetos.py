"""
Script para recalcular KPIs de todos os projetos solares
- Área necessária
- Economia mensal
- Economia anual
- Payback
"""
import os
import sys

# Adicionar diretório raiz ao path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.app import create_app
from app.extensoes import db
from app.energia_solar.catalogo_model import ProjetoSolar, PlacaSolar

def recalcular_kpis():
    """Recalcula KPIs de todos os projetos"""
    app = create_app()
    
    with app.app_context():
        projetos = ProjetoSolar.query.all()
        
        print(f"📊 Encontrados {len(projetos)} projetos para processar")
        print("="*60)
        
        atualizados = 0
        
        for projeto in projetos:
            print(f"\n🔍 Processando Projeto ID {projeto.id}:")
            alterado = False
            
            # 1. Recalcular área necessária
            if projeto.largura_area and projeto.comprimento_area:
                area_nova = projeto.largura_area * projeto.comprimento_area
                if projeto.area_necessaria != area_nova:
                    print(f"   📐 Área: {projeto.area_necessaria or 0:.2f} → {area_nova:.2f} m²")
                    projeto.area_necessaria = area_nova
                    alterado = True
            elif projeto.placa_id and projeto.linhas_placas and projeto.colunas_placas:
                # Calcular área se não houver largura/comprimento
                placa = PlacaSolar.query.get(projeto.placa_id)
                if placa:
                    largura_placa = (placa.largura / 1000) if placa.largura else 0.992
                    comprimento_placa = (placa.comprimento / 1000) if placa.comprimento else 1.650
                    
                    if projeto.orientacao == 'PAISAGEM':
                        largura_placa, comprimento_placa = comprimento_placa, largura_placa
                    
                    espacamento = 0.10
                    largura_total = (projeto.colunas_placas * largura_placa) + ((projeto.colunas_placas - 1) * espacamento)
                    comprimento_total = (projeto.linhas_placas * comprimento_placa) + ((projeto.linhas_placas - 1) * espacamento)
                    
                    projeto.largura_area = largura_total
                    projeto.comprimento_area = comprimento_total
                    projeto.area_necessaria = largura_total * comprimento_total
                    
                    print(f"   📐 Área calculada: {projeto.area_necessaria:.2f} m²")
                    alterado = True
            
            # 2. Recalcular economia mensal
            if projeto.consumo_kwh_mes and projeto.tarifa_kwh:
                consumo = float(projeto.consumo_kwh_mes)
                tarifa = float(projeto.tarifa_kwh)
                economia_mensal_nova = consumo * tarifa
                
                if not projeto.economia_mensal or projeto.economia_mensal == 0:
                    print(f"   💰 Economia mensal: R$ 0 → R$ {economia_mensal_nova:.2f}")
                    projeto.economia_mensal = economia_mensal_nova
                    alterado = True
            
            # 3. Recalcular economia anual
            if projeto.economia_mensal and projeto.economia_mensal > 0:
                economia_anual_nova = float(projeto.economia_mensal) * 12
                
                if not projeto.economia_anual or abs(float(projeto.economia_anual) - economia_anual_nova) > 0.01:
                    print(f"   📅 Economia anual: R$ {float(projeto.economia_anual or 0):.2f} → R$ {economia_anual_nova:.2f}")
                    projeto.economia_anual = economia_anual_nova
                    alterado = True
            
            # 4. Recalcular payback
            if projeto.valor_venda and projeto.economia_anual and float(projeto.economia_anual) > 0:
                payback_novo = float(projeto.valor_venda) / float(projeto.economia_anual)
                
                if not projeto.payback_anos or abs(float(projeto.payback_anos or 0) - payback_novo) > 0.01:
                    print(f"   ⏱️ Payback: {float(projeto.payback_anos or 0):.1f} → {payback_novo:.1f} anos")
                    projeto.payback_anos = payback_novo
                    alterado = True
            
            if alterado:
                atualizados += 1
                print(f"   ✅ Projeto {projeto.id} atualizado!")
            else:
                print(f"   ⏭️ Projeto {projeto.id} já está correto")
        
        # Commit no banco
        db.session.commit()
        
        print("="*60)
        print(f"\n✅ Recálculo concluído!")
        print(f"📊 Projetos processados: {len(projetos)}")
        print(f"🔄 Projetos atualizados: {atualizados}")
        print(f"⏭️ Projetos sem mudanças: {len(projetos) - atualizados}")

if __name__ == '__main__':
    recalcular_kpis()
