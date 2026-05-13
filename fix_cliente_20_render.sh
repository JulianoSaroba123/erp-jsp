#!/bin/bash
# Script para corrigir Cliente 20 diretamente no Render
# Execute este comando no Shell do Render

echo "🔧 Corrigindo Cliente ID 20 no Render..."
python -c "
from app import create_app
from app.extensoes import db
from app.cliente.cliente_model import Cliente

app = create_app()
with app.app_context():
    cliente = Cliente.query.get(20)
    if not cliente:
        print('❌ Cliente 20 não encontrado')
        exit(0)
    
    print(f'✅ Cliente encontrado: {cliente.nome}')
    print('🔧 Aplicando correções...')
    
    # Garantir campos obrigatórios
    if not cliente.nome or cliente.nome.strip() == '':
        cliente.nome = cliente.nome_fantasia or f'Cliente {cliente.id}'
    
    if not cliente.tipo or cliente.tipo not in ['PF', 'PJ']:
        cliente.tipo = 'PF'
    
    if not cliente.status:
        cliente.status = 'ativo'
    
    if not cliente.ativo:
        cliente.ativo = True
    
    if cliente.limite_credito is None:
        cliente.limite_credito = 0
    
    if cliente.desconto_padrao is None:
        cliente.desconto_padrao = 0
    
    if cliente.prazo_pagamento_padrao is None:
        cliente.prazo_pagamento_padrao = 30
    
    if not cliente.classificacao or cliente.classificacao not in ['A', 'B', 'C']:
        cliente.classificacao = 'A'
    
    try:
        db.session.commit()
        print('✅ Cliente 20 corrigido com sucesso!')
    except Exception as e:
        db.session.rollback()
        print(f'❌ Erro: {e}')
"
