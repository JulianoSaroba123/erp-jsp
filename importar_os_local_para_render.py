"""
Script para importar ORDENS DE SERVIÇO do banco local (produção) para o Render
"""

import os
import sys
from datetime import datetime
from decimal import Decimal

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

print("=" * 80)
print("🚀 IMPORTAÇÃO DE ORDENS DE SERVIÇO - Local → Render")
print("=" * 80)

# Primeiro conecta ao banco LOCAL para buscar as OS
print("\n📂 Conectando ao banco LOCAL (produção)...")
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Banco LOCAL
local_engine = create_engine('sqlite:///database/database.db')
LocalSession = sessionmaker(bind=local_engine)
local_session = LocalSession()

# Busca todas as OS do banco local
from sqlalchemy import text

try:
    os_local = local_session.execute(text("SELECT * FROM ordem_servico")).fetchall()
    print(f"✅ Encontradas {len(os_local)} ordens de serviço no banco local")
except Exception as e:
    print(f"❌ Erro ao buscar OS local: {e}")
    os_local = []

if not os_local:
    print("⚠️ Nenhuma OS encontrada no banco local!")
    sys.exit(0)

# Agora conecta ao RENDER
print("\n🐘 Conectando ao PostgreSQL no Render...")
from app.app import create_app

RENDER_DB_URL = 'postgresql://erp_jsp_db_iw6v_user:roBPw29VFmZKdksaGXw1tv4mYULKQwnl@dpg-d4pf1s49c44c73bdsdrg-a.oregon-postgres.render.com/erp_jsp_db_iw6v'

app = create_app()
app.config['SQLALCHEMY_DATABASE_URI'] = RENDER_DB_URL

with app.app_context():
    from app.extensoes import db
    from app.ordem_servico.ordem_servico_model import (
        OrdemServico, OrdemServicoItem, OrdemServicoProduto, OrdemServicoParcela
    )
    
    print("✅ Conectado ao Render!\n")
    
    os_importadas = 0
    itens_importados = 0
    produtos_importados = 0
    parcelas_importadas = 0
    
    for row in os_local:
        print(f"📋 Processando OS: {row.numero}...")
        
        # Verifica se já existe
        existe = OrdemServico.query.filter_by(id=row.id).first()
        
        if existe:
            print(f"   ⚠️ OS {row.numero} já existe no Render (ID: {row.id})")
            continue
        
        try:
            # Cria a OS
            nova_os = OrdemServico(
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
                valor_entrada=Decimal(str(row.valor_entrada)) if row.valor_entrada else None,
                data_primeira_parcela=row.data_primeira_parcela,
                data_vencimento_pagamento=row.data_vencimento_pagamento,
                descricao_pagamento=row.descricao_pagamento,
                prazo_garantia=row.prazo_garantia or 0,
                solicitante=row.solicitante,
                descricao_problema=row.descricao_problema,
                tipo_servico=row.tipo_servico if hasattr(row, 'tipo_servico') else 'manutencao',
                km_inicial=row.km_inicial if hasattr(row, 'km_inicial') else None,
                km_final=row.km_final if hasattr(row, 'km_final') else None,
                total_km=row.total_km if hasattr(row, 'total_km') else None,
                hora_inicial=row.hora_inicial if hasattr(row, 'hora_inicial') else None,
                hora_final=row.hora_final if hasattr(row, 'hora_final') else None,
                total_horas=row.total_horas if hasattr(row, 'total_horas') else None,
                observacoes_anexos=row.observacoes_anexos if hasattr(row, 'observacoes_anexos') else None,
                incluir_imagens_relatorio=bool(row.incluir_imagens_relatorio) if hasattr(row, 'incluir_imagens_relatorio') else False,
                criado_em=row.criado_em if row.criado_em else datetime.now(),
                atualizado_em=row.atualizado_em if row.atualizado_em else datetime.now()
            )
            
            db.session.add(nova_os)
            db.session.flush()
            
            # Busca e importa itens/serviços da OS
            try:
                itens = local_session.execute(
                    text("SELECT * FROM ordem_servico_item WHERE ordem_servico_id = :os_id"),
                    {'os_id': row.id}
                ).fetchall()
                
                for item in itens:
                    novo_item = OrdemServicoItem(
                        ordem_servico_id=nova_os.id,
                        descricao=item.descricao,
                        quantidade=Decimal(str(item.quantidade or 1)),
                        valor_unitario=Decimal(str(item.valor_unitario or 0)),
                        tipo_servico=item.tipo_servico if hasattr(item, 'tipo_servico') else 'hora',
                        observacoes=item.observacoes if hasattr(item, 'observacoes') else None
                    )
                    db.session.add(novo_item)
                    itens_importados += 1
            except Exception as e:
                print(f"   ⚠️ Erro ao importar itens: {e}")
            
            # Busca e importa produtos da OS
            try:
                produtos = local_session.execute(
                    text("SELECT * FROM ordem_servico_produto WHERE ordem_servico_id = :os_id"),
                    {'os_id': row.id}
                ).fetchall()
                
                for prod in produtos:
                    novo_prod = OrdemServicoProduto(
                        ordem_servico_id=nova_os.id,
                        descricao=prod.descricao,
                        quantidade=Decimal(str(prod.quantidade or 1)),
                        valor_unitario=Decimal(str(prod.valor_unitario or 0))
                    )
                    db.session.add(novo_prod)
                    produtos_importados += 1
            except Exception as e:
                print(f"   ⚠️ Erro ao importar produtos: {e}")
            
            # Busca e importa parcelas da OS
            try:
                parcelas = local_session.execute(
                    text("SELECT * FROM ordem_servico_parcelas WHERE ordem_servico_id = :os_id"),
                    {'os_id': row.id}
                ).fetchall()
                
                for parc in parcelas:
                    nova_parc = OrdemServicoParcela(
                        ordem_servico_id=nova_os.id,
                        numero_parcela=parc.numero_parcela,
                        data_vencimento=parc.data_vencimento,
                        valor=Decimal(str(parc.valor or 0)),
                        pago=bool(parc.pago) if parc.pago else False,
                        data_pagamento=parc.data_pagamento if hasattr(parc, 'data_pagamento') else None
                    )
                    db.session.add(nova_parc)
                    parcelas_importadas += 1
            except Exception as e:
                print(f"   ⚠️ Erro ao importar parcelas: {e}")
            
            db.session.commit()
            os_importadas += 1
            print(f"   ✅ OS {row.numero} importada com sucesso!")
            
        except Exception as e:
            print(f"   ❌ Erro ao importar OS {row.numero}: {e}")
            db.session.rollback()
    
    print("\n" + "=" * 80)
    print("✅ IMPORTAÇÃO CONCLUÍDA!")
    print("=" * 80)
    print(f"\n📊 RESUMO:")
    print(f"   🔧 Ordens de Serviço: {os_importadas}")
    print(f"   📝 Serviços/Itens: {itens_importados}")
    print(f"   📦 Produtos: {produtos_importados}")
    print(f"   💰 Parcelas: {parcelas_importadas}")
    
    # Mostra total no Render
    total_os_render = OrdemServico.query.count()
    print(f"\n🐘 Total de OS no Render agora: {total_os_render}")
    print("=" * 80)

local_session.close()
