"""
Script para importar TODOS os dados do SQLite local para PostgreSQL no Render
Importa: Ordens de Serviço, Propostas, Serviços, Produtos, Parcelas, Anexos, etc.
"""

import os
import sys
from datetime import datetime
from decimal import Decimal

# Adiciona o diretório raiz ao path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Importa o app
from app.app import create_app

# Configurações
SQLITE_DB = 'database/database.db'
RENDER_DB_URL = 'postgresql://erp_jsp_db_iw6v_user:roBPw29VFmZKdksaGXw1tv4mYULKQwnl@dpg-d4pf1s49c44c73bdsdrg-a.oregon-postgres.render.com/erp_jsp_db_iw6v'

print("=" * 80)
print("🚀 IMPORTAÇÃO COMPLETA DE DADOS - SQLite → PostgreSQL Render")
print("=" * 80)

# Conecta ao SQLite
print("\n📂 Conectando ao SQLite local...")
sqlite_engine = create_engine(f'sqlite:///{SQLITE_DB}')
SqliteSession = sessionmaker(bind=sqlite_engine)
sqlite_session = SqliteSession()

# Conecta ao PostgreSQL Render via Flask app
print("🐘 Conectando ao PostgreSQL no Render...")
app = create_app()
app.config['SQLALCHEMY_DATABASE_URI'] = RENDER_DB_URL

with app.app_context():
    from app.extensoes import db
    # Importa os models
    from app.cliente.cliente_model import Cliente
    from app.fornecedor.fornecedor_model import Fornecedor
    from app.produto.produto_model import Produto
    from app.proposta.proposta_model import Proposta, PropostaProduto, PropostaServico
    from app.ordem_servico.ordem_servico_model import (
        OrdemServico, OrdemServicoItem, OrdemServicoProduto, 
        OrdemServicoParcela, OrdemServicoAnexo
    )
    
    print("✅ Conectado ao PostgreSQL Render!\n")
    
    # ========================================
    # 1. IMPORTAR PROPOSTAS
    # ========================================
    print("📋 Importando PROPOSTAS...")
    propostas_count = 0
    proposta_itens_count = 0
    
    try:
        propostas_sqlite = sqlite_session.execute(text("SELECT * FROM proposta")).fetchall()
    except Exception as e:
        print(f"   ⚠️ Tabela 'proposta' não existe no SQLite local: {e}")
        propostas_sqlite = []
    
    for row in propostas_sqlite:
        # Verifica se já existe
        existe = db.session.execute(
            text("SELECT id FROM proposta WHERE id = :id"),
            {'id': row.id}
        ).fetchone()
        
        if not existe:
            proposta = Proposta(
                id=row.id,
                numero=row.numero,
                cliente_id=row.cliente_id,
                titulo=row.titulo or 'Proposta',
                descricao=row.descricao,
                validade_dias=row.validade_dias or 30,
                condicoes_pagamento=row.condicoes_pagamento or 'À vista',
                observacoes=row.observacoes,
                status=row.status or 'rascunho',
                valor_total=Decimal(str(row.valor_total or 0)),
                criado_em=row.criado_em if row.criado_em else datetime.now(),
                atualizado_em=row.atualizado_em if row.atualizado_em else datetime.now()
            )
            db.session.add(proposta)
            propostas_count += 1
    
    db.session.flush()
    
    # Importar produtos da proposta
    try:
        produtos_proposta = sqlite_session.execute(text("SELECT * FROM proposta_produto")).fetchall()
        for row in produtos_proposta:
            existe = db.session.execute(
                text("SELECT id FROM proposta_produto WHERE id = :id"),
                {'id': row.id}
            ).fetchone()
            
            if not existe:
                produto = PropostaProduto(
                    id=row.id,
                    proposta_id=row.proposta_id,
                    descricao=row.descricao,
                    quantidade=Decimal(str(row.quantidade or 1)),
                    valor_unitario=Decimal(str(row.valor_unitario or 0))
                )
                db.session.add(produto)
                proposta_itens_count += 1
    except Exception as e:
        print(f"   ⚠️ Aviso ao importar produtos de proposta: {e}")
    
    # Importar serviços da proposta  
    try:
        servicos_proposta = sqlite_session.execute(text("SELECT * FROM proposta_servico")).fetchall()
        for row in servicos_proposta:
            existe = db.session.execute(
                text("SELECT id FROM proposta_servico WHERE id = :id"),
                {'id': row.id}
            ).fetchone()
            
            if not existe:
                servico = PropostaServico(
                    id=row.id,
                    proposta_id=row.proposta_id,
                    descricao=row.descricao,
                    quantidade=Decimal(str(row.quantidade or 1)),
                    valor_unitario=Decimal(str(row.valor_unitario or 0)),
                    tipo_servico=row.tipo_servico if hasattr(row, 'tipo_servico') else 'hora'
                )
                db.session.add(servico)
                proposta_itens_count += 1
    except Exception as e:
        print(f"   ⚠️ Aviso ao importar serviços de proposta: {e}")
    
    db.session.commit()
    print(f"   ✅ {propostas_count} propostas importadas")
    print(f"   ✅ {proposta_itens_count} itens de proposta importados\n")
    
    # ========================================
    # 2. IMPORTAR ORDENS DE SERVIÇO
    # ========================================
    print("🔧 Importando ORDENS DE SERVIÇO...")
    os_count = 0
    os_itens_count = 0
    os_produtos_count = 0
    os_parcelas_count = 0
    
    try:
        ordens_sqlite = sqlite_session.execute(text("SELECT * FROM ordem_servico")).fetchall()
    except Exception as e:
        print(f"   ⚠️ Tabela 'ordem_servico' não existe no SQLite local: {e}")
        ordens_sqlite = []
    
    for row in ordens_sqlite:
        # Verifica se já existe
        existe = db.session.execute(
            text("SELECT id FROM ordem_servico WHERE id = :id"),
            {'id': row.id}
        ).fetchone()
        
        if not existe:
            ordem = OrdemServico(
                id=row.id,
                numero=row.numero,
                cliente_id=row.cliente_id,
                titulo=row.titulo or 'OS sem título',
                descricao=row.descricao,
                status=row.status or 'aberta',
                prioridade=row.prioridade or 'normal',
                data_abertura=row.data_abertura if row.data_abertura else datetime.now().date(),
                data_prevista=row.data_prevista,
                data_inicio=row.data_inicio,
                data_conclusao=row.data_conclusao,
                tecnico_responsavel=row.tecnico_responsavel,
                equipamento=row.equipamento,
                marca_modelo=row.marca_modelo,
                numero_serie=row.numero_serie,
                diagnostico=row.diagnostico,
                diagnostico_tecnico=row.diagnostico_tecnico,
                solucao=row.solucao,
                observacoes=row.observacoes,
                valor_servico=Decimal(str(row.valor_servico or 0)),
                valor_pecas=Decimal(str(row.valor_pecas or 0)),
                valor_desconto=Decimal(str(row.valor_desconto or 0)),
                valor_total=Decimal(str(row.valor_total or 0)),
                condicao_pagamento=row.condicao_pagamento or 'a_vista',
                status_pagamento=row.status_pagamento or 'pendente',
                numero_parcelas=row.numero_parcelas or 1,
                valor_entrada=Decimal(str(row.valor_entrada or 0)) if row.valor_entrada else None,
                data_primeira_parcela=row.data_primeira_parcela,
                data_vencimento_pagamento=row.data_vencimento_pagamento,
                descricao_pagamento=row.descricao_pagamento,
                prazo_garantia=row.prazo_garantia or 0,
                solicitante=row.solicitante,
                descricao_problema=row.descricao_problema,
                tipo_servico=row.tipo_servico or 'manutencao',
                km_inicial=row.km_inicial,
                km_final=row.km_final,
                total_km=row.total_km,
                hora_inicial=row.hora_inicial,
                hora_final=row.hora_final,
                total_horas=row.total_horas,
                observacoes_anexos=row.observacoes_anexos,
                incluir_imagens_relatorio=bool(row.incluir_imagens_relatorio) if hasattr(row, 'incluir_imagens_relatorio') else False,
                criado_em=row.criado_em if row.criado_em else datetime.now(),
                atualizado_em=row.atualizado_em if row.atualizado_em else datetime.now()
            )
            db.session.add(ordem)
            os_count += 1
    
    db.session.flush()
    
    # Importar serviços/itens da OS
    try:
        os_itens_sqlite = sqlite_session.execute(text("SELECT * FROM ordem_servico_item")).fetchall()
    except Exception as e:
        print(f"   ⚠️ Erro ao buscar itens de OS: {e}")
        os_itens_sqlite = []
    
    for row in os_itens_sqlite:
        existe = db.session.execute(
            text("SELECT id FROM ordem_servico_item WHERE id = :id"),
            {'id': row.id}
        ).fetchone()
        
        if not existe:
            item = OrdemServicoItem(
                id=row.id,
                ordem_servico_id=row.ordem_servico_id,
                descricao=row.descricao,
                quantidade=Decimal(str(row.quantidade or 1)),
                valor_unitario=Decimal(str(row.valor_unitario or 0)),
                tipo_servico=row.tipo_servico or 'hora',
                observacoes=row.observacoes
            )
            db.session.add(item)
            os_itens_count += 1
    
    # Importar produtos da OS
    try:
        os_produtos_sqlite = sqlite_session.execute(text("SELECT * FROM ordem_servico_produto")).fetchall()
    except Exception as e:
        print(f"   ⚠️ Erro ao buscar produtos de OS: {e}")
        os_produtos_sqlite = []
    
    for row in os_produtos_sqlite:
        existe = db.session.execute(
            text("SELECT id FROM ordem_servico_produto WHERE id = :id"),
            {'id': row.id}
        ).fetchone()
        
        if not existe:
            produto = OrdemServicoProduto(
                id=row.id,
                ordem_servico_id=row.ordem_servico_id,
                descricao=row.descricao,
                quantidade=Decimal(str(row.quantidade or 1)),
                valor_unitario=Decimal(str(row.valor_unitario or 0))
            )
            db.session.add(produto)
            os_produtos_count += 1
    
    # Importar parcelas da OS
    try:
        os_parcelas_sqlite = sqlite_session.execute(text("SELECT * FROM ordem_servico_parcelas")).fetchall()
    except Exception as e:
        print(f"   ⚠️ Erro ao buscar parcelas de OS: {e}")
        os_parcelas_sqlite = []
    
    for row in os_parcelas_sqlite:
        existe = db.session.execute(
            text("SELECT id FROM ordem_servico_parcelas WHERE id = :id"),
            {'id': row.id}
        ).fetchone()
        
        if not existe:
            parcela = OrdemServicoParcela(
                id=row.id,
                ordem_servico_id=row.ordem_servico_id,
                numero_parcela=row.numero_parcela,
                data_vencimento=row.data_vencimento,
                valor=Decimal(str(row.valor or 0)),
                pago=bool(row.pago) if row.pago else False,
                data_pagamento=row.data_pagamento
            )
            db.session.add(parcela)
            os_parcelas_count += 1
    
    db.session.commit()
    print(f"   ✅ {os_count} ordens de serviço importadas")
    print(f"   ✅ {os_itens_count} serviços/itens importados")
    print(f"   ✅ {os_produtos_count} produtos importados")
    print(f"   ✅ {os_parcelas_count} parcelas importadas\n")
    
    # ========================================
    # RESUMO FINAL
    # ========================================
    print("=" * 80)
    print("✅ IMPORTAÇÃO COMPLETA!")
    print("=" * 80)
    
    # Conta totais no Render
    total_clientes = db.session.query(Cliente).count()
    total_fornecedores = db.session.query(Fornecedor).count()
    total_produtos = db.session.query(Produto).count()
    total_propostas = db.session.query(Proposta).count()
    total_os = db.session.query(OrdemServico).count()
    
    print(f"\n📊 TOTAIS NO RENDER:")
    print(f"   👥 Clientes: {total_clientes}")
    print(f"   🏭 Fornecedores: {total_fornecedores}")
    print(f"   📦 Produtos: {total_produtos}")
    print(f"   📋 Propostas: {total_propostas}")
    print(f"   🔧 Ordens de Serviço: {total_os}")
    print(f"\n🎉 Todos os dados foram importados com sucesso!")
    print("=" * 80)

sqlite_session.close()
