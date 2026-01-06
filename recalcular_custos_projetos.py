"""
Script para recalcular custos separados dos projetos solares existentes
Distribui o custo_total em: 70% equipamentos, 20% instalação, 10% projeto
"""
from app import create_app
from app.extensoes import db
from app.energia_solar.catalogo_model import ProjetoSolar

def recalcular_custos():
    app = create_app()
    
    with app.app_context():
        projetos = ProjetoSolar.query.all()
        print(f"📊 Encontrados {len(projetos)} projetos para recalcular\n")
        
        atualizados = 0
        for projeto in projetos:
            if projeto.custo_total and projeto.custo_total > 0:
                # Se os custos já estão zerados, recalcular
                if not projeto.custo_equipamentos or projeto.custo_equipamentos == 0:
                    # Distribuição padrão: 70% equipamentos, 20% instalação, 10% projeto
                    projeto.custo_equipamentos = projeto.custo_total * 0.70
                    projeto.custo_instalacao = projeto.custo_total * 0.20
                    projeto.custo_projeto = projeto.custo_total * 0.10
                    
                    print(f"✅ Projeto #{projeto.id} - {projeto.nome_cliente}")
                    print(f"   Custo Total: R$ {projeto.custo_total:.2f}")
                    print(f"   → Equipamentos (70%): R$ {projeto.custo_equipamentos:.2f}")
                    print(f"   → Instalação (20%): R$ {projeto.custo_instalacao:.2f}")
                    print(f"   → Projeto (10%): R$ {projeto.custo_projeto:.2f}\n")
                    
                    atualizados += 1
        
        if atualizados > 0:
            db.session.commit()
            print(f"🎉 {atualizados} projetos atualizados com sucesso!")
        else:
            print("ℹ️ Nenhum projeto precisou de atualização")

if __name__ == '__main__':
    recalcular_custos()
