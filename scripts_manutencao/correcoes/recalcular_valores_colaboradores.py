# -*- coding: utf-8 -*-
"""
Script para recalcular valores de colaboradores com a nova fórmula.
Nova fórmula: salário ÷ 22 dias ÷ 8.8 horas (ao invés de ÷ 220)
"""

import sys
import os
from decimal import Decimal

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.app import create_app
from app.extensoes import db
from app.colaborador.colaborador_model import OrdemServicoColaborador, Colaborador

def recalcular_valores():
    """Recalcula valores de custo e receita para todos os colaboradores em OSs."""
    
    print("=" * 80)
    print("🔄 RECALCULAR VALORES DE COLABORADORES")
    print("=" * 80)
    print("\n📊 Nova fórmula: salário ÷ 22 dias ÷ 8.8 horas")
    print("   Antiga: R$ 3.000 ÷ 220 = R$ 13,64/h")
    print("   Nova:   R$ 3.000 ÷ 22 ÷ 8.8 = R$ 15,49/h")
    print()
    
    app = create_app()
    
    with app.app_context():
        try:
            # Buscar todos os trabalhos de colaboradores ativos
            trabalhos = OrdemServicoColaborador.query.filter_by(ativo=True).all()
            
            print(f"📋 Total de registros encontrados: {len(trabalhos)}")
            
            if not trabalhos:
                print("\n⚠️  Nenhum registro encontrado para atualizar.")
                return
            
            print("\n" + "-" * 80)
            
            atualizados = 0
            erros = 0
            sem_dados = 0
            
            for trabalho in trabalhos:
                colaborador = trabalho.colaborador
                
                if not colaborador:
                    print(f"⚠️  Trabalho ID {trabalho.id}: Colaborador não encontrado")
                    sem_dados += 1
                    continue
                
                salario = colaborador.salario_mensal or Decimal('0')
                valor_hora_cliente = colaborador.valor_hora or Decimal('0')
                
                if salario == 0 and valor_hora_cliente == 0:
                    print(f"⚠️  Trabalho ID {trabalho.id} ({colaborador.nome}): Sem dados financeiros")
                    sem_dados += 1
                    continue
                
                # Recalcular valores com a nova fórmula
                try:
                    trabalho.atualizar_valores_com_adicional(salario, valor_hora_cliente)
                    
                    os_id = trabalho.ordem_servico.id if trabalho.ordem_servico else trabalho.ordem_servico_id
                    data = trabalho.data_trabalho.strftime('%d/%m/%Y') if trabalho.data_trabalho else '—'
                    
                    print(f"✅ OS #{os_id} - {colaborador.nome} ({data})")
                    print(f"   Custo: R$ {trabalho.valor_hora_custo:.2f}/h | Receita: R$ {trabalho.valor_hora_receita:.2f}/h")
                    
                    atualizados += 1
                    
                except Exception as e:
                    print(f"❌ Erro ao recalcular ID {trabalho.id}: {str(e)}")
                    erros += 1
            
            if atualizados > 0:
                db.session.commit()
                print("\n" + "-" * 80)
                print(f"✅ Commit realizado com sucesso!")
            
            # Resumo
            print("\n" + "=" * 80)
            print("📊 RESUMO DA ATUALIZAÇÃO")
            print("=" * 80)
            print(f"✅ Atualizados: {atualizados}")
            print(f"⚠️  Sem dados: {sem_dados}")
            print(f"❌ Erros: {erros}")
            print(f"📋 Total processado: {len(trabalhos)}")
            print()
            
            if atualizados > 0:
                print("🎉 TODOS OS VALORES FORAM RECALCULADOS COM SUCESSO!")
                print("\n💡 Os PDFs agora mostrarão os valores corretos quando regenerados.")
            else:
                print("⚠️  Nenhum registro foi atualizado.")
            
            print("=" * 80)
            
        except Exception as e:
            db.session.rollback()
            print(f"\n❌ ERRO CRÍTICO: {str(e)}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    recalcular_valores()
