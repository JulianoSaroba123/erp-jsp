from app.app import app
from app.extensoes import db
from app.ordem_servico.ordem_servico_model import OrdemServico
from app.colaborador.colaborador_model import Colaborador, OrdemServicoColaborador
from datetime import datetime, time

with app.app_context():
    os = OrdemServico.query.get(2)
    colaborador = Colaborador.query.get(1)
    
    if os and colaborador:
        print(f"\n=== Adicionando colaborador na OS #{os.id} ===")
        
        # Criar registro de trabalho
        trabalho = OrdemServicoColaborador(
            ordem_servico_id=os.id,
            colaborador_id=colaborador.id,
            data_trabalho=datetime(2026, 3, 20),  # Hoje
            hora_inicio=time(8, 0),   # 08:00
            hora_fim=time(17, 0),     # 17:00
            descricao_atividade="Instalação de sistema elétrico e verificação de conexões",
            ativo=True
        )
        
        # Calcular horas automaticamente
        trabalho.calcular_horas_automatico()
        
        db.session.add(trabalho)
        db.session.commit()
        
        print(f"✅ Colaborador: {colaborador.nome}")
        print(f"✅ Data: 20/03/2026")
        print(f"✅ Período: 08:00 - 17:00")
        print(f"✅ Total: {trabalho.total_horas_formatado}")
        print(f"✅ Atividade: {trabalho.descricao_atividade}")
        print(f"\n🎉 Colaborador adicionado com sucesso!")
        print(f"\nAgora acesse: http://127.0.0.1:5000/ordem_servico/{os.id}/relatorio-pdf")
    else:
        print("⚠️ OS ou Colaborador não encontrado!")
