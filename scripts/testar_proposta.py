#!/usr/bin/env python3
"""
Script para testar criação de proposta manualmente
"""

import sys
import os

# Adicionar o diretório raiz ao path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from aplicacao import create_app
from aplicacao.extensoes import db
from aplicacao.cliente.cliente_model import Cliente
from aplicacao.proposta.proposta_model import Proposta
from datetime import date, timedelta

def testar_proposta():
    """Testar criação de proposta"""
    print("🧪 Testando criação de proposta...")
    
    try:
        app = create_app()
        
        with app.app_context():
            # Verificar clientes
            clientes = Cliente.query.filter(Cliente.ativo == True).all()
            print(f"📋 {len(clientes)} clientes ativos encontrados")
            
            if not clientes:
                print("❌ Nenhum cliente ativo! Criando um cliente para teste...")
                cliente = Cliente(nome="Cliente Teste", ativo=True)
                db.session.add(cliente)
                db.session.commit()
                print("✅ Cliente teste criado")
                clientes = [cliente]
            
            # Tentar criar uma proposta
            print("\n🆕 Criando proposta de teste...")
            proposta = Proposta()
            proposta.cliente_id = clientes[0].id
            proposta.titulo = "Proposta de Teste"
            proposta.descricao = "Teste de criação automática"
            proposta.valor_total = 1000.00
            proposta.desconto = 0.00
            proposta.calcular_valor_final()
            proposta.data_validade = date.today() + timedelta(days=30)
            
            # Validações
            print(f"📝 Cliente ID: {proposta.cliente_id}")
            print(f"📝 Título: {proposta.titulo}")
            print(f"📝 Valor Total: {proposta.valor_total}")
            
            # Gerar número
            print("🔢 Gerando número...")
            proposta.gerar_numero()
            print(f"📝 Número gerado: {proposta.numero}")
            
            # Salvar
            print("💾 Salvando no banco...")
            db.session.add(proposta)
            db.session.commit()
            
            print(f"✅ Proposta {proposta.numero} criada com sucesso!")
            print(f"📝 ID: {proposta.id}")
            
            # Verificar se foi salva
            proposta_verificacao = Proposta.query.get(proposta.id)
            if proposta_verificacao:
                print("✅ Proposta confirmada no banco de dados!")
            else:
                print("❌ Proposta NÃO foi salva no banco!")
                
    except Exception as e:
        print(f"❌ Erro no teste: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    testar_proposta()