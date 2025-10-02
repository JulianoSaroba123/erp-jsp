#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from aplicacao import create_app
from aplicacao.extensoes import db
from aplicacao.ordem_servico.os_model import OrdemServico
from aplicacao.cliente.cliente_model import Cliente

app = create_app()

with app.app_context():
    print("=== VERIFICAÇÃO DE ORDENS DE SERVIÇO ===")
    
    # 1. Contar todas as OS
    total_os = OrdemServico.query.count()
    print(f"Total de OS no banco: {total_os}")
    
    # 2. Contar OS ativas
    os_ativas = OrdemServico.query.filter_by(ativo=True).count()
    print(f"OS ativas: {os_ativas}")
    
    # 3. Listar últimas 5 OS
    ultimas_os = OrdemServico.query.order_by(OrdemServico.id.desc()).limit(5).all()
    print(f"\nÚltimas 5 OS criadas:")
    for os in ultimas_os:
        print(f"  ID {os.id}: {os.codigo} - {os.solicitante} - Ativo: {os.ativo}")
    
    # 4. Verificar se há OS criadas hoje
    from datetime import datetime, date
    hoje = date.today()
    os_hoje = OrdemServico.query.filter(OrdemServico.data_emissao == hoje).all()
    print(f"\nOS criadas hoje ({hoje}):")
    for os in os_hoje:
        print(f"  {os.codigo}: {os.solicitante} - Status: {os.status} - Ativo: {os.ativo}")
    
    # 5. Verificar query da listagem
    query_listagem = OrdemServico.query.filter(OrdemServico.ativo == True).order_by(OrdemServico.data_emissao.desc())
    print(f"\nQuery de listagem retorna: {query_listagem.count()} registros")
    
    # 6. Teste criar uma OS simples
    print("\n=== TESTE DE CRIAÇÃO ===")
    cliente = Cliente.query.first()
    if cliente:
        nova_os = OrdemServico()
        nova_os.codigo = nova_os.gerar_codigo()
        nova_os.cliente_id = cliente.id
        nova_os.solicitante = "Teste Listagem"
        nova_os.status = "Aberta"
        nova_os.ativo = True  # Garantir que está ativo
        
        db.session.add(nova_os)
        db.session.commit()
        
        print(f"OS criada: {nova_os.codigo} - ID: {nova_os.id}")
        
        # Verificar se aparece na query
        count_after = OrdemServico.query.filter_by(ativo=True).count()
        print(f"Contagem após criação: {count_after}")
    else:
        print("Nenhum cliente encontrado para teste")