# -*- coding: utf-8 -*-
"""
Diagnóstico: Integração Ordem de Serviço → Financeiro
======================================================
Verifica se os lançamentos financeiros estão sendo criados
quando as ordens de serviço são finalizadas.
"""

from app import create_app
from app.ordem_servico.ordem_servico_model import OrdemServico
from app.financeiro.financeiro_model import LancamentoFinanceiro
from app.extensoes import db

app = create_app()

with app.app_context():
    print("\n" + "="*70)
    print("🔍 DIAGNÓSTICO: Integração OS → Financeiro")
    print("="*70 + "\n")
    
    # 1. Buscar todas as OS finalizadas
    os_finalizadas = OrdemServico.query.filter_by(
        status='finalizada',
        ativo=True
    ).all()
    
    print(f"📊 Total de OS finalizadas: {len(os_finalizadas)}")
    print()
    
    # 2. Verificar quais têm lançamento financeiro
    os_com_lancamento = []
    os_sem_lancamento = []
    
    for os in os_finalizadas:
        lancamento = LancamentoFinanceiro.query.filter_by(
            ordem_servico_id=os.id,
            ativo=True
        ).first()
        
        if lancamento:
            os_com_lancamento.append((os, lancamento))
        else:
            os_sem_lancamento.append(os)
    
    print(f"✅ OS com lançamento financeiro: {len(os_com_lancamento)}")
    print(f"⚠️  OS SEM lançamento financeiro: {len(os_sem_lancamento)}")
    print()
    
    # 3. Exibir OS sem lançamento (problema!)
    if os_sem_lancamento:
        print("="*70)
        print("⚠️  ORDENS DE SERVIÇO FINALIZADAS SEM LANÇAMENTO FINANCEIRO:")
        print("="*70)
        for os in os_sem_lancamento:
            print(f"\n   🔴 OS #{os.numero} (ID: {os.id})")
            print(f"      Título: {os.titulo}")
            print(f"      Cliente: {os.cliente.nome if os.cliente else 'N/A'}")
            print(f"      Valor Total: R$ {os.valor_total:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
            print(f"      Data Conclusão: {os.data_conclusao.strftime('%d/%m/%Y %H:%M') if os.data_conclusao else 'N/A'}")
            print(f"      Status: {os.status}")
    
    # 4. Verificar método gerar_lancamento_financeiro
    print("\n" + "="*70)
    print("🧪 TESTANDO MÉTODO gerar_lancamento_financeiro()")
    print("="*70)
    
    if os_sem_lancamento:
        os_teste = os_sem_lancamento[0]
        print(f"\n   Testando OS #{os_teste.numero} (ID: {os_teste.id})...")
        print(f"   Status: {os_teste.status}")
        print(f"   Valor Total: R$ {os_teste.valor_total:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
        print(f"   Cliente ID: {os_teste.cliente_id}")
        
        try:
            print(f"\n   🔄 Chamando gerar_lancamento_financeiro()...")
            lancamento = os_teste.gerar_lancamento_financeiro()
            
            if lancamento:
                print(f"   ✅ Lançamento criado com sucesso!")
                print(f"      ID: {lancamento.id}")
                print(f"      Descrição: {lancamento.descricao}")
                print(f"      Valor: R$ {lancamento.valor:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
                print(f"      Tipo: {lancamento.tipo}")
                print(f"      Status: {lancamento.status}")
            else:
                print(f"   ⚠️  Método retornou None (possíveis causas:")
                print(f"      - Status não é 'finalizada': {os_teste.status}")
                print(f"      - Valor total <= 0: {os_teste.valor_total}")
                print(f"      - Lançamento já existe")
        except Exception as e:
            print(f"   ❌ ERRO ao gerar lançamento: {e}")
            import traceback
            print(f"\n   Stack trace:")
            traceback.print_exc()
    else:
        print("\n   ✅ Todas as OS finalizadas têm lançamento financeiro!")
    
    # 5. Verificar relacionamento inverso
    print("\n" + "="*70)
    print("🔗 VERIFICANDO RELACIONAMENTOS")
    print("="*70)
    
    if os_com_lancamento:
        os_exemplo, lanc_exemplo = os_com_lancamento[0]
        print(f"\n   OS #{os_exemplo.numero}:")
        print(f"      Lançamentos vinculados: {len(os_exemplo.lancamentos_financeiros)}")
        
        print(f"\n   Lançamento #{lanc_exemplo.id}:")
        print(f"      Vinculado à OS: #{os_exemplo.numero if lanc_exemplo.ordem_servico else 'NENHUMA'}")
    
    # 6. Resumo final
    print("\n" + "="*70)
    print("📋 RESUMO DO DIAGNÓSTICO")
    print("="*70)
    print(f"   Total de OS finalizadas: {len(os_finalizadas)}")
    print(f"   Com lançamento: {len(os_com_lancamento)} ({len(os_com_lancamento)/len(os_finalizadas)*100 if os_finalizadas else 0:.1f}%)")
    print(f"   Sem lançamento: {len(os_sem_lancamento)} ({len(os_sem_lancamento)/len(os_finalizadas)*100 if os_finalizadas else 0:.1f}%)")
    
    if os_sem_lancamento:
        print(f"\n   ⚠️  AÇÃO NECESSÁRIA: {len(os_sem_lancamento)} OS precisam de correção!")
        print(f"   Execute: python corrigir_os_sem_lancamento.py")
    else:
        print(f"\n   ✅ Sistema funcionando corretamente!")
    
    print()
