# -*- coding: utf-8 -*-
"""
Teste Completo: Integração OS → Financeiro
===========================================
Cria uma OS de teste, finaliza e verifica se o lançamento
financeiro é criado automaticamente.
"""

from app import create_app
from app.ordem_servico.ordem_servico_model import OrdemServico
from app.financeiro.financeiro_model import LancamentoFinanceiro
from app.cliente.cliente_model import Cliente
from app.extensoes import db
from datetime import datetime, date

app = create_app()

with app.app_context():
    print("\n" + "="*70)
    print("🧪 TESTE COMPLETO: Integração OS → Financeiro")
    print("="*70 + "\n")
    
    # 1. Buscar ou criar cliente de teste
    print("📋 ETAPA 1: Preparando cliente de teste...")
    cliente = Cliente.query.filter_by(ativo=True).first()
    
    if not cliente:
        print("   ⚠️  Nenhum cliente ativo encontrado!")
        print("   Criando cliente de teste...")
        cliente = Cliente(
            nome="Cliente Teste - Integração",
            tipo="PJ",
            cpf_cnpj="12.345.678/0001-90",
            telefone="(11) 99999-9999",
            email="teste@teste.com",
            status="ativo",
            ativo=True
        )
        cliente.save()
        print(f"   ✅ Cliente criado: {cliente.nome} (ID: {cliente.id})")
    else:
        print(f"   ✅ Usando cliente: {cliente.nome} (ID: {cliente.id})")
    
    print()
    
    # 2. Criar OS de teste
    print("📋 ETAPA 2: Criando Ordem de Serviço de teste...")
    os_teste = OrdemServico(
        numero=f"TESTE-{datetime.now().strftime('%H%M%S')}",
        titulo="Teste de Integração OS → Financeiro",
        descricao="OS criada automaticamente para testar integração com módulo financeiro",
        cliente_id=cliente.id,
        data_abertura=date.today(),
        status='pendente',
        tipo_os='comercial',
        valor_total=1500.00,
        ativo=True
    )
    os_teste.save()
    print(f"   ✅ OS criada: {os_teste.numero} (ID: {os_teste.id})")
    print(f"      Valor Total: R$ 1.500,00")
    print(f"      Status inicial: {os_teste.status}")
    print()
    
    # 3. Verificar que NÃO existe lançamento antes de finalizar
    print("📋 ETAPA 3: Verificando lançamentos ANTES da finalização...")
    lancamento_antes = LancamentoFinanceiro.query.filter_by(
        ordem_servico_id=os_teste.id
    ).first()
    
    if lancamento_antes:
        print(f"   ⚠️  ERRO: Já existe lançamento antes da finalização!")
        print(f"      ID: {lancamento_antes.id}")
    else:
        print(f"   ✅ OK: Nenhum lançamento existe (esperado)")
    print()
    
    # 4. Finalizar a OS (deve gerar lançamento automaticamente)
    print("📋 ETAPA 4: Finalizando a Ordem de Serviço...")
    print(f"   Status antes: {os_teste.status}")
    
    try:
        os_teste.concluir_servico()
        print(f"   ✅ Método concluir_servico() executado")
        print(f"   Status depois: {os_teste.status}")
        print(f"   Data conclusão: {os_teste.data_conclusao.strftime('%d/%m/%Y %H:%M') if os_teste.data_conclusao else 'N/A'}")
    except Exception as e:
        print(f"   ❌ ERRO ao finalizar: {e}")
        import traceback
        traceback.print_exc()
    print()
    
    # 5. Verificar se o lançamento foi criado
    print("📋 ETAPA 5: Verificando lançamento DEPOIS da finalização...")
    
    # Refresh da sessão para garantir que pegamos dados atualizados
    db.session.refresh(os_teste)
    
    lancamento_depois = LancamentoFinanceiro.query.filter_by(
        ordem_servico_id=os_teste.id,
        ativo=True
    ).first()
    
    if lancamento_depois:
        print(f"   ✅ SUCESSO: Lançamento criado automaticamente!")
        print(f"      ID: {lancamento_depois.id}")
        print(f"      Descrição: {lancamento_depois.descricao}")
        print(f"      Tipo: {lancamento_depois.tipo}")
        print(f"      Valor: R$ {lancamento_depois.valor:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
        print(f"      Status: {lancamento_depois.status}")
        print(f"      Data Lançamento: {lancamento_depois.data_lancamento.strftime('%d/%m/%Y')}")
        print(f"      Data Vencimento: {lancamento_depois.data_vencimento.strftime('%d/%m/%Y')}")
        print(f"      Cliente ID: {lancamento_depois.cliente_id}")
        print(f"      OS ID: {lancamento_depois.ordem_servico_id}")
        print(f"      Origem: {lancamento_depois.origem if hasattr(lancamento_depois, 'origem') else 'N/A'}")
    else:
        print(f"   ❌ FALHA: Lançamento NÃO foi criado!")
        print(f"\n   🔍 Investigando motivo...")
        print(f"      Status da OS: {os_teste.status}")
        print(f"      Valor Total: {os_teste.valor_total}")
        print(f"      Cliente ID: {os_teste.cliente_id}")
        
        # Tentar criar manualmente para ver erro
        print(f"\n   🔄 Tentando criar lançamento manualmente...")
        try:
            lancamento_manual = os_teste.gerar_lancamento_financeiro()
            if lancamento_manual:
                print(f"   ✅ Lançamento criado manualmente!")
                print(f"      ID: {lancamento_manual.id}")
            else:
                print(f"   ⚠️  Método retornou None")
        except Exception as e:
            print(f"   ❌ Erro: {e}")
            import traceback
            traceback.print_exc()
    print()
    
    # 6. Verificar relacionamento bidirecional
    print("📋 ETAPA 6: Verificando relacionamentos bidirecionais...")
    print(f"   OS → Lançamentos: {len(os_teste.lancamentos_financeiros)} lançamento(s)")
    if lancamento_depois:
        print(f"   Lançamento → OS: #{lancamento_depois.ordem_servico.numero if lancamento_depois.ordem_servico else 'NENHUMA'}")
    print()
    
    # 7. Resumo final
    print("="*70)
    print("📊 RESULTADO DO TESTE")
    print("="*70)
    
    sucesso = lancamento_depois is not None
    
    if sucesso:
        print("   ✅ INTEGRAÇÃO FUNCIONANDO CORRETAMENTE!")
        print("   ✅ OS finalizada gera lançamento financeiro automaticamente")
        print(f"   ✅ OS #{os_teste.numero} → Lançamento #{lancamento_depois.id}")
    else:
        print("   ❌ PROBLEMA DETECTADO!")
        print("   ❌ OS finalizada NÃO gerou lançamento financeiro")
        print("   ❌ Verifique o método gerar_lancamento_financeiro()")
    
    print()
    
    # 8. Limpeza (opcional)
    print("="*70)
    print("🧹 LIMPEZA")
    print("="*70)
    print("\nDeseja manter ou excluir os dados de teste?")
    print("   - OS criada: #{os_teste.numero} (ID: {os_teste.id})")
    if lancamento_depois:
        print(f"   - Lançamento: #{lancamento_depois.id}")
    print("\n   Para excluir, execute:")
    print(f"   python -c \"from app import create_app; from app.extensoes import db; from app.ordem_servico.ordem_servico_model import OrdemServico; app=create_app(); app.app_context().push(); os=OrdemServico.get_by_id({os_teste.id}); os.delete() if os else None; db.session.commit(); print('✅ OS de teste excluída')\"")
    print()
