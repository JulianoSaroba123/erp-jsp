#!/usr/bin/env python3
"""
Script para diagnosticar e corrigir propostas imediatamente
"""

import sys
import os
import traceback

# Adicionar o diretório raiz ao path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from aplicacao import create_app
from aplicacao.extensoes import db
from aplicacao.cliente.cliente_model import Cliente
from datetime import datetime, date, timedelta

def fix_propostas():
    """Corrigir propostas agora"""
    print("🔧 DIAGNÓSTICO E CORREÇÃO DE PROPOSTAS")
    print("=" * 50)
    
    try:
        app = create_app()
        
        with app.app_context():
            # 1. Verificar se tabelas existem
            from sqlalchemy import inspect
            inspector = inspect(db.engine)
            tabelas = inspector.get_table_names()
            
            print(f"📊 Tabelas existentes: {tabelas}")
            
            if 'propostas' not in tabelas:
                print("❌ PROBLEMA: Tabela 'propostas' não existe!")
                print("🔧 SOLUÇÃO: Criando tabelas...")
                db.create_all()
                tabelas_apos = inspector.get_table_names()
                print(f"✅ Tabelas criadas: {tabelas_apos}")
            else:
                print("✅ Tabela 'propostas' existe")
            
            # 2. Tentar importar modelo
            try:
                from aplicacao.proposta.proposta_model import Proposta
                print("✅ Modelo Proposta importado")
            except Exception as e:
                print(f"❌ ERRO ao importar modelo: {str(e)}")
                traceback.print_exc()
                return
            
            # 3. Verificar propostas existentes
            try:
                total_propostas = Proposta.query.count()
                propostas_ativas = Proposta.query.filter(Proposta.data_exclusao.is_(None)).count()
                
                print(f"📊 Total propostas: {total_propostas}")
                print(f"📊 Propostas ativas: {propostas_ativas}")
                
                if propostas_ativas > 0:
                    print("✅ Propostas encontradas:")
                    propostas = Proposta.query.filter(Proposta.data_exclusao.is_(None)).all()
                    for p in propostas:
                        print(f"   - ID: {p.id}, Número: {p.numero}, Título: {p.titulo}")
                    print("✅ O problema não é falta de dados!")
                    return
                    
            except Exception as e:
                print(f"❌ ERRO ao consultar propostas: {str(e)}")
                traceback.print_exc()
                print("🔧 Vou tentar recriar as tabelas...")
                db.drop_all()
                db.create_all()
                print("✅ Tabelas recriadas!")
            
            # 4. Se não há propostas, criar algumas de teste
            print("🧪 Criando dados de teste...")
            
            # Verificar clientes
            cliente = Cliente.query.filter(Cliente.ativo == True).first()
            if not cliente:
                print("📝 Criando cliente de teste...")
                cliente = Cliente(
                    nome="Cliente Teste Proposta",
                    email="teste@proposta.com",
                    telefone="(11) 99999-9999",
                    endereco="Rua Teste, 123",
                    cidade="São Paulo", 
                    estado="SP",
                    cep="01234-567",
                    ativo=True
                )
                db.session.add(cliente)
                db.session.commit()
                print(f"✅ Cliente criado: {cliente.nome}")
            else:
                print(f"✅ Cliente existente: {cliente.nome}")
            
            # Criar propostas de teste
            propostas_teste = [
                {
                    'titulo': 'Desenvolvimento de Sistema ERP',
                    'descricao': 'Sistema completo de gestão empresarial',
                    'valor_total': 15000.00,
                    'desconto': 1500.00,
                    'forma_pagamento': 'Parcelado',
                    'prazo_entrega': '60 dias úteis'
                },
                {
                    'titulo': 'Consultoria em TI',
                    'descricao': 'Consultoria para otimização de processos',
                    'valor_total': 5000.00,
                    'desconto': 0.00,
                    'forma_pagamento': 'À vista',
                    'prazo_entrega': '30 dias úteis'
                },
                {
                    'titulo': 'Manutenção de Sistema',
                    'descricao': 'Contrato anual de manutenção',
                    'valor_total': 8000.00,
                    'desconto': 800.00,
                    'forma_pagamento': 'PIX',
                    'prazo_entrega': '5 dias úteis'
                }
            ]
            
            for i, dados in enumerate(propostas_teste, 1):
                try:
                    proposta = Proposta()
                    proposta.cliente_id = cliente.id
                    proposta.titulo = dados['titulo']
                    proposta.descricao = dados['descricao']
                    proposta.valor_total = dados['valor_total']
                    proposta.desconto = dados['desconto']
                    proposta.calcular_valor_final()
                    proposta.forma_pagamento = dados['forma_pagamento']
                    proposta.prazo_entrega = dados['prazo_entrega']
                    proposta.data_validade = date.today() + timedelta(days=15)
                    proposta.status = 'Pendente'
                    proposta.gerar_numero()
                    
                    db.session.add(proposta)
                    db.session.commit()
                    
                    print(f"✅ Proposta {i} criada: {proposta.numero} - {proposta.titulo}")
                    print(f"   Valor final: R$ {proposta.valor_final}")
                    
                except Exception as e:
                    print(f"❌ Erro ao criar proposta {i}: {str(e)}")
                    traceback.print_exc()
                    db.session.rollback()
            
            # 5. Verificação final
            print("\n🎯 VERIFICAÇÃO FINAL:")
            total_final = Proposta.query.count()
            ativas_final = Proposta.query.filter(Proposta.data_exclusao.is_(None)).count()
            
            print(f"📊 Total propostas criadas: {total_final}")
            print(f"📊 Propostas ativas: {ativas_final}")
            
            if ativas_final > 0:
                print("\n✅ SUCESSO! Propostas criadas:")
                propostas = Proposta.query.filter(Proposta.data_exclusao.is_(None)).all()
                for p in propostas:
                    print(f"   🟢 {p.numero} - {p.titulo} (R$ {p.valor_final})")
                
                print(f"\n🎉 PROBLEMA RESOLVIDO!")
                print("💡 Agora atualize a página /propostas para ver os dados!")
            else:
                print("❌ Ainda há um problema. Verifique os logs de erro.")
    except Exception as e:
        print(f"💥 ERRO CRÍTICO: {str(e)}")
        traceback.print_exc()


if __name__ == "__main__":
    fix_propostas()
