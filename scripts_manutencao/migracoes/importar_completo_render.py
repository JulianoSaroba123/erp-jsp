"""
Script para importar CLIENTES e ORDENS DE SERVIÇO do banco local para o Render
Executa a importação na ordem correta respeitando foreign keys
"""
import sys
import os

# Adiciona o diretório raiz ao path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app.app import create_app
from app.extensoes import db
from app.cliente.cliente_model import Cliente
from app.ordem_servico.ordem_servico_model import OrdemServico
import sqlite3
from datetime import datetime

app = create_app()

with app.app_context():
    print("="*70)
    print("🔄 IMPORTAÇÃO COMPLETA: CLIENTES + ORDENS DE SERVIÇO")
    print("="*70)
    print()
    
    # Conecta ao banco local
    if not os.path.exists('erp.db'):
        print("❌ Arquivo erp.db não encontrado!")
        sys.exit(1)
    
    conn = sqlite3.connect('erp.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # ====================
    # PASSO 1: CLIENTES
    # ====================
    print("📋 PASSO 1: Importando CLIENTES")
    print("-" * 70)
    
    clientes_local = cursor.execute("SELECT * FROM clientes WHERE ativo = 1 ORDER BY id").fetchall()
    clientes_render = {c.cpf_cnpj: c for c in Cliente.query.all() if c.cpf_cnpj}
    
    clientes_importados = 0
    clientes_existentes = 0
    mapa_clientes = {}  # local_id -> render_id
    
    for cli_local in clientes_local:
        cpf_cnpj = cli_local['cpf_cnpj']
        
        # Se já existe no Render
        if cpf_cnpj and cpf_cnpj in clientes_render:
            cli_render = clientes_render[cpf_cnpj]
            mapa_clientes[cli_local['id']] = cli_render.id
            clientes_existentes += 1
            print(f"   ✓ {cli_local['nome'][:40]:40} (já existe - ID: {cli_render.id})")
            continue
        
        # Cria novo cliente
        novo_cliente = Cliente(
            nome=cli_local['nome'] or 'Cliente sem nome',
            nome_fantasia=cli_local['nome_fantasia'],
            razao_social=cli_local['razao_social'],
            tipo=cli_local['tipo'] or 'PF',
            cpf_cnpj=cpf_cnpj,
            telefone=cli_local['telefone'],
            email=cli_local['email'],
            endereco=cli_local['endereco'],
            cidade=cli_local['cidade'],
            estado=cli_local['estado'],
            cep=cli_local['cep'],
            ativo=True
        )
        
        db.session.add(novo_cliente)
        db.session.flush()  # Para obter o ID
        
        mapa_clientes[cli_local['id']] = novo_cliente.id
        clientes_importados += 1
        print(f"   + {cli_local['nome'][:40]:40} (novo - ID: {novo_cliente.id})")
    
    db.session.commit()
    
    print()
    print(f"✅ Clientes: {clientes_importados} importados, {clientes_existentes} já existentes")
    print(f"📊 Mapeamento criado: {len(mapa_clientes)} clientes mapeados")
    print()
    
    # ====================
    # PASSO 2: ORDENS DE SERVIÇO
    # ====================
    print("📋 PASSO 2: Importando ORDENS DE SERVIÇO")
    print("-" * 70)
    
    ordens_local = cursor.execute("SELECT * FROM ordem_servico WHERE ativo = 1 ORDER BY id").fetchall()
    ordens_render = {os.numero: os for os in OrdemServico.query.all()}
    
    os_importadas = 0
    os_existentes = 0
    os_sem_cliente = 0
    
    for os_local in ordens_local:
        numero = os_local['numero']
        
        # Se já existe no Render
        if numero in ordens_render:
            os_existentes += 1
            print(f"   ✓ {numero:15} (já existe)")
            continue
        
        # Verifica se o cliente foi mapeado
        cliente_id_render = mapa_clientes.get(os_local['cliente_id'])
        if not cliente_id_render:
            os_sem_cliente += 1
            print(f"   ⚠ {numero:15} (cliente local {os_local['cliente_id']} não encontrado)")
            continue
        
        # Cria nova OS
        nova_os = OrdemServico(
            numero=numero,
            cliente_id=cliente_id_render,
            titulo=os_local['titulo'] or 'Serviço',
            descricao=os_local['descricao'],
            status=os_local['status'] or 'aberta',
            prioridade=os_local['prioridade'] or 'normal',
            data_abertura=os_local['data_abertura'] if os_local['data_abertura'] else datetime.now().date(),
            data_previsao=os_local['data_previsao'] if os_local['data_previsao'] else None,
            data_conclusao=os_local['data_conclusao'] if os_local['data_conclusao'] else None,
            valor_mao_obra=os_local['valor_mao_obra'] or 0,
            valor_produtos=os_local['valor_produtos'] or 0,
            valor_total=os_local['valor_total'] or 0,
            forma_pagamento=os_local['forma_pagamento'] or 'a_vista',
            num_parcelas=os_local['num_parcelas'] or 1,
            valor_entrada=os_local['valor_entrada'] or 0,
            observacoes=os_local['observacoes'],
            ativo=True
        )
        
        db.session.add(nova_os)
        os_importadas += 1
        
        # Busca o nome do cliente para exibir
        cliente_nome = Cliente.query.get(cliente_id_render).nome if cliente_id_render else "?"
        print(f"   + {numero:15} → {cliente_nome[:30]:30}")
    
    db.session.commit()
    conn.close()
    
    print()
    print(f"✅ Ordens: {os_importadas} importadas, {os_existentes} já existentes")
    if os_sem_cliente > 0:
        print(f"⚠️  {os_sem_cliente} OS puladas (cliente não encontrado)")
    
    print()
    print("="*70)
    print("✅ IMPORTAÇÃO CONCLUÍDA COM SUCESSO!")
    print("="*70)
    print()
    print(f"📊 Resumo Final:")
    print(f"   • Clientes no Render: {Cliente.query.count()}")
    print(f"   • OS no Render: {OrdemServico.query.count()}")
    print()
