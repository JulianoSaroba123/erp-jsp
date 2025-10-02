#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Teste específico para diagnosticar problemas no CRUD de Ordem de Serviço
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from aplicacao import create_app
from aplicacao.extensoes import db
from aplicacao.ordem_servico.os_model import OrdemServico
from aplicacao.cliente.cliente_model import Cliente
from datetime import datetime

def test_crud_ordem_servico():
    """Teste completo do CRUD de Ordem de Serviço"""
    
    app = create_app()
    
    with app.app_context():
        print("=== TESTE CRUD ORDEM DE SERVIÇO ===")
        
        # 1. Verificar se há clientes no banco
        print("\n1. Verificando clientes disponíveis...")
        clientes = Cliente.query.all()
        print(f"   Clientes encontrados: {len(clientes)}")
        
        if not clientes:
            print("   ERROR: Nenhum cliente encontrado. Criando cliente de teste...")
            cliente_teste = Cliente(
                nome="Cliente Teste CRUD",
                cpf_cnpj="12345678901",
                telefone="(11) 99999-9999",
                email="teste@teste.com"
            )
            db.session.add(cliente_teste)
            db.session.commit()
            clientes = [cliente_teste]
            print(f"   Cliente teste criado com ID: {cliente_teste.id}")
        
        cliente = clientes[0]
        print(f"   Usando cliente: {cliente.nome} (ID: {cliente.id})")
        
        # 2. Testar criação de OS
        print("\n2. Testando criação de Ordem de Serviço...")
        try:
            nova_os = OrdemServico()
            nova_os.codigo = nova_os.gerar_codigo()
            nova_os.cliente_id = cliente.id
            nova_os.solicitante = "Teste Solicitante"
            nova_os.contato = "(11) 99999-9999"
            nova_os.data_emissao = datetime.now().date()
            nova_os.prioridade = "Normal"
            nova_os.status = "Aberta"
            nova_os.equipamento_nome = "Computador Teste"
            nova_os.problema_descrito = "Problema de teste"
            nova_os.valor_total = 100.0
            
            print(f"   Código gerado: {nova_os.codigo}")
            print(f"   Cliente ID: {nova_os.cliente_id}")
            
            db.session.add(nova_os)
            db.session.flush()  # Para obter o ID sem commit final
            
            print(f"   OS criada com ID: {nova_os.id}")
            
            # 3. Testar leitura
            print("\n3. Testando leitura...")
            os_lida = OrdemServico.query.get(nova_os.id)
            if os_lida:
                print(f"   OS encontrada: {os_lida.codigo} - {os_lida.solicitante}")
                print(f"   Status: {os_lida.status}")
                print(f"   Cliente: {os_lida.cliente.nome if os_lida.cliente else 'N/A'}")
            else:
                print("   ERROR: OS não encontrada após criação")
                return False
            
            # 4. Testar atualização
            print("\n4. Testando atualização...")
            os_lida.solicitante = "Solicitante Atualizado"
            os_lida.status = "Em Andamento"
            db.session.flush()
            
            os_verificacao = OrdemServico.query.get(nova_os.id)
            if os_verificacao.solicitante == "Solicitante Atualizado":
                print("   Atualização OK!")
            else:
                print("   ERROR: Atualização falhou")
                return False
            
            # 5. Testar listagem
            print("\n5. Testando listagem...")
            todas_os = OrdemServico.query.filter_by(ativo=True).all()
            print(f"   Total de OS ativas: {len(todas_os)}")
            
            # 6. Testar exclusão lógica
            print("\n6. Testando exclusão lógica...")
            os_lida.ativo = False
            db.session.flush()
            
            os_ativas = OrdemServico.query.filter_by(ativo=True).all()
            print(f"   OS ativas após exclusão: {len(os_ativas)}")
            
            # Rollback para não modificar o banco
            db.session.rollback()
            print("\n   Rollback executado - dados de teste removidos")
            
            print("\n=== TESTE CRUD COMPLETADO COM SUCESSO ===")
            return True
            
        except Exception as e:
            print(f"\n   ERROR: {str(e)}")
            import traceback
            traceback.print_exc()
            db.session.rollback()
            return False

if __name__ == "__main__":
    success = test_crud_ordem_servico()
    sys.exit(0 if success else 1)