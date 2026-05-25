"""
Importa ORDENS DE SERVIÇO com mapeamento correto de IDs de clientes
"""
import sqlite3
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from datetime import datetime

print("=" * 80)
print("🚀 IMPORTAÇÃO DE ORDENS DE SERVIÇO COM MAPEAMENTO DE CLIENTES")
print("=" * 80)

# Conecta ao SQLite LOCAL (erp.db)
print("\n📂 Conectando ao SQLite local (erp.db)...")
conn_local = sqlite3.connect('erp.db')
conn_local.row_factory = sqlite3.Row
cursor = conn_local.cursor()

# Conecta ao Render
print("🐘 Conectando ao PostgreSQL Render...")
RENDER_DB_URL = 'postgresql://erp_jsp_db_iw6v_user:roBPw29VFmZKdksaGXw1tv4mYULKQwnl@dpg-d4pf1s49c44c73bdsdrg-a.oregon-postgres.render.com/erp_jsp_db_iw6v'

engine = create_engine(RENDER_DB_URL)
Session = sessionmaker(bind=engine)
session = Session()

try:
    # ====================================================================
    # PASSO 1: CRIAR MAPEAMENTO DE IDS (LOCAL → RENDER)
    # ====================================================================
    print("\n" + "=" * 80)
    print("🔗 CRIANDO MAPEAMENTO DE IDs DE CLIENTES")
    print("=" * 80)
    
    # Busca clientes do banco local
    clientes_local = cursor.execute("SELECT id, nome, cpf_cnpj FROM clientes").fetchall()
    
    # Busca clientes do Render
    clientes_render = session.execute(text("SELECT id, nome, cpf_cnpj FROM clientes")).fetchall()
    
    # Cria dicionário de mapeamento: {id_local: id_render}
    mapa_clientes = {}
    
    print(f"\n📊 Clientes locais: {len(clientes_local)}")
    print(f"📊 Clientes Render: {len(clientes_render)}")
    print("\n🔗 Mapeamento:")
    
    for cli_local in clientes_local:
        # Procura o cliente no Render pelo CPF/CNPJ ou nome
        id_render = None
        
        # Primeiro tenta por CPF/CNPJ
        if cli_local['cpf_cnpj']:
            for cli_render in clientes_render:
                if cli_render[2] and cli_render[2] == cli_local['cpf_cnpj']:
                    id_render = cli_render[0]
                    break
        
        # Se não achou, tenta por nome
        if not id_render:
            for cli_render in clientes_render:
                if cli_render[1] and cli_render[1].strip().lower() == cli_local['nome'].strip().lower():
                    id_render = cli_render[0]
                    break
        
        if id_render:
            mapa_clientes[cli_local['id']] = id_render
            print(f"   Local ID {cli_local['id']} → Render ID {id_render} | {cli_local['nome']}")
        else:
            print(f"   ⚠️ Local ID {cli_local['id']} ({cli_local['nome']}) - NÃO ENCONTRADO no Render!")
    
    print(f"\n✅ {len(mapa_clientes)} clientes mapeados")
    
    # ====================================================================
    # PASSO 2: IMPORTAR ORDENS DE SERVIÇO
    # ====================================================================
    print("\n" + "=" * 80)
    print("🔧 IMPORTANDO ORDENS DE SERVIÇO")
    print("=" * 80)
    
    ordens = cursor.execute("SELECT * FROM ordem_servico ORDER BY id").fetchall()
    print(f"\n📊 Encontradas {len(ordens)} ordens de serviço no banco local\n")
    
    stats = {'importadas': 0, 'puladas': 0, 'erros': 0}
    
    for row in ordens:
        try:
            # Verifica se já existe
            result = session.execute(
                text("SELECT id FROM ordem_servico WHERE numero = :numero"),
                {'numero': row['numero']}
            )
            if result.fetchone():
                print(f"   ⚠️ OS {row['numero']} já existe - pulando")
                stats['puladas'] += 1
                continue
            
            # Mapeia o cliente_id
            cliente_id_local = row['cliente_id']
            cliente_id_render = mapa_clientes.get(cliente_id_local)
            
            if not cliente_id_render:
                print(f"   ⚠️ OS {row['numero']}: Cliente local ID {cliente_id_local} não encontrado no mapeamento - pulando")
                stats['puladas'] += 1
                continue
            
            # Insere OS com o cliente_id mapeado
            session.execute(text("""
                INSERT INTO ordem_servico (
                    numero, cliente_id, titulo, descricao, status, prioridade,
                    data_abertura, data_prevista, data_inicio, data_conclusao,
                    tecnico_responsavel, equipamento, marca_modelo, numero_serie,
                    diagnostico, diagnostico_tecnico, solucao, observacoes,
                    valor_servico, valor_pecas, valor_desconto, valor_total,
                    condicao_pagamento, status_pagamento, numero_parcelas,
                    valor_entrada, data_primeira_parcela, data_vencimento_pagamento,
                    descricao_pagamento, prazo_garantia, solicitante, descricao_problema,
                    tipo_servico, km_inicial, km_final, total_km,
                    hora_inicial, hora_final, total_horas,
                    ativo, criado_em, atualizado_em
                ) VALUES (
                    :numero, :cliente_id, :titulo, :descricao, :status, :prioridade,
                    :data_abertura, :data_prevista, :data_inicio, :data_conclusao,
                    :tecnico_responsavel, :equipamento, :marca_modelo, :numero_serie,
                    :diagnostico, :diagnostico_tecnico, :solucao, :observacoes,
                    :valor_servico, :valor_pecas, :valor_desconto, :valor_total,
                    :condicao_pagamento, :status_pagamento, :numero_parcelas,
                    :valor_entrada, :data_primeira_parcela, :data_vencimento_pagamento,
                    :descricao_pagamento, :prazo_garantia, :solicitante, :descricao_problema,
                    :tipo_servico, :km_inicial, :km_final, :total_km,
                    :hora_inicial, :hora_final, :total_horas,
                    :ativo, :criado_em, :atualizado_em
                )
                RETURNING id
            """), {
                'numero': row['numero'],
                'cliente_id': cliente_id_render,  # USA O ID MAPEADO
                'titulo': row['titulo'] or 'OS sem título',
                'descricao': row['descricao'],
                'status': row['status'] or 'aberta',
                'prioridade': row['prioridade'] or 'normal',
                'data_abertura': row['data_abertura'] if row['data_abertura'] else datetime.now().date(),
                'data_prevista': row['data_prevista'],
                'data_inicio': row['data_inicio'],
                'data_conclusao': row['data_conclusao'],
                'tecnico_responsavel': row['tecnico_responsavel'],
                'equipamento': row['equipamento'],
                'marca_modelo': row['marca_modelo'],
                'numero_serie': row['numero_serie'],
                'diagnostico': row['diagnostico'],
                'diagnostico_tecnico': row['diagnostico_tecnico'],
                'solucao': row['solucao'],
                'observacoes': row['observacoes'],
                'valor_servico': row['valor_servico'] or 0,
                'valor_pecas': row['valor_pecas'] or 0,
                'valor_desconto': row['valor_desconto'] or 0,
                'valor_total': row['valor_total'] or 0,
                'condicao_pagamento': row['condicao_pagamento'] or 'a_vista',
                'status_pagamento': row['status_pagamento'] or 'pendente',
                'numero_parcelas': row['numero_parcelas'] or 1,
                'valor_entrada': row['valor_entrada'],
                'data_primeira_parcela': row['data_primeira_parcela'],
                'data_vencimento_pagamento': row['data_vencimento_pagamento'],
                'descricao_pagamento': row['descricao_pagamento'],
                'prazo_garantia': row['prazo_garantia'] or 0,
                'solicitante': row['solicitante'],
                'descricao_problema': row['descricao_problema'],
                'tipo_servico': row['tipo_servico'] if 'tipo_servico' in row.keys() else 'manutencao',
                'km_inicial': row['km_inicial'] if 'km_inicial' in row.keys() else None,
                'km_final': row['km_final'] if 'km_final' in row.keys() else None,
                'total_km': row['total_km'] if 'total_km' in row.keys() else None,
                'hora_inicial': row['hora_inicial'] if 'hora_inicial' in row.keys() else None,
                'hora_final': row['hora_final'] if 'hora_final' in row.keys() else None,
                'total_horas': row['total_horas'] if 'total_horas' in row.keys() else None,
                'ativo': True,
                'criado_em': row['criado_em'] if row['criado_em'] else datetime.now(),
                'atualizado_em': row['atualizado_em'] if row['atualizado_em'] else datetime.now()
            })
            
            # Pega o ID da OS inserida
            result = session.execute(text("SELECT id FROM ordem_servico WHERE numero = :numero"), {'numero': row['numero']})
            os_id_render = result.scalar()
            
            # Importa itens/serviços
            try:
                itens = cursor.execute(
                    "SELECT * FROM ordem_servico_itens WHERE ordem_servico_id = ?",
                    (row['id'],)
                ).fetchall()
                
                for item in itens:
                    session.execute(text("""
                        INSERT INTO ordem_servico_itens (
                            ordem_servico_id, descricao, quantidade, valor_unitario,
                            tipo_servico, observacoes
                        ) VALUES (
                            :ordem_servico_id, :descricao, :quantidade, :valor_unitario,
                            :tipo_servico, :observacoes
                        )
                    """), {
                        'ordem_servico_id': os_id_render,
                        'descricao': item['descricao'],
                        'quantidade': item['quantidade'] or 1,
                        'valor_unitario': item['valor_unitario'] or 0,
                        'tipo_servico': item['tipo_servico'] if 'tipo_servico' in item.keys() else 'hora',
                        'observacoes': item['observacoes'] if 'observacoes' in item.keys() else None
                    })
            except:
                pass
            
            # Importa produtos
            try:
                produtos = cursor.execute(
                    "SELECT * FROM ordem_servico_produtos WHERE ordem_servico_id = ?",
                    (row['id'],)
                ).fetchall()
                
                for prod in produtos:
                    session.execute(text("""
                        INSERT INTO ordem_servico_produtos (
                            ordem_servico_id, descricao, quantidade, valor_unitario
                        ) VALUES (
                            :ordem_servico_id, :descricao, :quantidade, :valor_unitario
                        )
                    """), {
                        'ordem_servico_id': os_id_render,
                        'descricao': prod['descricao'],
                        'quantidade': prod['quantidade'] or 1,
                        'valor_unitario': prod['valor_unitario'] or 0
                    })
            except:
                pass
            
            # Importa parcelas
            try:
                parcelas = cursor.execute(
                    "SELECT * FROM ordem_servico_parcelas WHERE ordem_servico_id = ?",
                    (row['id'],)
                ).fetchall()
                
                for parc in parcelas:
                    session.execute(text("""
                        INSERT INTO ordem_servico_parcelas (
                            ordem_servico_id, numero_parcela, data_vencimento,
                            valor, pago, data_pagamento
                        ) VALUES (
                            :ordem_servico_id, :numero_parcela, :data_vencimento,
                            :valor, :pago, :data_pagamento
                        )
                    """), {
                        'ordem_servico_id': os_id_render,
                        'numero_parcela': parc['numero_parcela'],
                        'data_vencimento': parc['data_vencimento'],
                        'valor': parc['valor'] or 0,
                        'pago': bool(parc['pago']) if parc['pago'] else False,
                        'data_pagamento': parc['data_pagamento'] if 'data_pagamento' in parc.keys() else None
                    })
            except:
                pass
            
            session.commit()
            stats['importadas'] += 1
            print(f"   ✅ OS {row['numero']}: {row['titulo']} (Cliente: Local ID {cliente_id_local} → Render ID {cliente_id_render})")
        
        except Exception as e:
            session.rollback()
            stats['erros'] += 1
            print(f"   ❌ Erro ao importar OS {row['numero']}: {e}")
    
    # ====================================================================
    # RESUMO FINAL
    # ====================================================================
    print("\n" + "=" * 80)
    print("🎉 IMPORTAÇÃO CONCLUÍDA!")
    print("=" * 80)
    print(f"""
📊 RESUMO:
   ✅ Importadas: {stats['importadas']}
   ⚠️ Puladas: {stats['puladas']}
   ❌ Erros: {stats['erros']}
    """)
    
    # Verifica totais no Render
    result = session.execute(text("SELECT COUNT(*) FROM ordem_servico"))
    total_os = result.scalar()
    
    result = session.execute(text("SELECT COUNT(*) FROM ordem_servico WHERE ativo = TRUE"))
    total_os_ativas = result.scalar()
    
    print("🐘 TOTAIS NO RENDER:")
    print(f"   🔧 Total de OS: {total_os}")
    print(f"   ✅ OS Ativas: {total_os_ativas}")
    print("\n" + "=" * 80)

except Exception as e:
    print(f"\n❌ ERRO GERAL: {e}")
    import traceback
    traceback.print_exc()
    session.rollback()

finally:
    session.close()
    engine.dispose()
    conn_local.close()
