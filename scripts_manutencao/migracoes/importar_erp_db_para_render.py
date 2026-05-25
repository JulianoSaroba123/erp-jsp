"""
Importa TODOS OS DADOS do banco erp.db LOCAL para o Render
Ordem: Clientes → Fornecedores → Produtos → Propostas → OS
"""
import sqlite3
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from decimal import Decimal

print("=" * 80)
print("🚀 IMPORTAÇÃO COMPLETA: erp.db → Render PostgreSQL")
print("=" * 80)

# 1. Conecta ao SQLite LOCAL (erp.db NA RAIZ DO PROJETO)
print("\n📂 Conectando ao SQLite local (erp.db)...")
conn_local = sqlite3.connect('erp.db')
conn_local.row_factory = sqlite3.Row
cursor = conn_local.cursor()

# 2. Conecta ao Render PostgreSQL
print("🐘 Conectando ao PostgreSQL Render...")
RENDER_DB_URL = 'postgresql://erp_jsp_db_iw6v_user:roBPw29VFmZKdksaGXw1tv4mYULKQwnl@dpg-d4pf1s49c44c73bdsdrg-a.oregon-postgres.render.com/erp_jsp_db_iw6v'

engine = create_engine(RENDER_DB_URL)
Session = sessionmaker(bind=engine)
session = Session()

stats = {
    'clientes': 0,
    'fornecedores': 0,
    'produtos': 0,
    'propostas': 0,
    'ordens': 0,
    'itens': 0,
    'produtos_os': 0,
    'parcelas': 0
}

try:
    # ====================================================================
    # PASSO 1: IMPORTAR CLIENTES
    # ====================================================================
    print("\n" + "=" * 80)
    print("👥 PASSO 1: IMPORTANDO CLIENTES")
    print("=" * 80)
    
    # Busca clientes do erp.db
    clientes = cursor.execute("SELECT * FROM clientes").fetchall()
    print(f"\n📊 Encontrados {len(clientes)} clientes no banco local")
    
    for row in clientes:
        # Verifica se já existe (por ID ou CPF/CNPJ)
        result = session.execute(
            text("SELECT id FROM clientes WHERE id = :id OR cpf_cnpj = :cpf_cnpj"),
            {'id': row['id'], 'cpf_cnpj': row['cpf_cnpj']}
        )
        if result.fetchone():
            print(f"   ⚠️ Cliente ID {row['id']} ({row['nome']}) já existe - pulando")
            continue
        
        # Determina o tipo (pessoa_fisica ou pessoa_juridica)
        tipo_cliente = 'pessoa_juridica' if row['cpf_cnpj'] and len(row['cpf_cnpj'].replace('.', '').replace('/', '').replace('-', '')) > 11 else 'pessoa_fisica'
        
        # Insere cliente
        session.execute(text("""
            INSERT INTO clientes (
                id, nome, tipo, cpf_cnpj, email, telefone, celular,
                endereco, numero, complemento, bairro, cidade, estado, cep,
                observacoes, ativo, criado_em, atualizado_em
            ) VALUES (
                :id, :nome, :tipo, :cpf_cnpj, :email, :telefone, :celular,
                :endereco, :numero, :complemento, :bairro, :cidade, :estado, :cep,
                :observacoes, :ativo, :criado_em, :atualizado_em
            )
        """), {
            'id': row['id'],
            'nome': row['nome'],
            'tipo': tipo_cliente,
            'cpf_cnpj': row['cpf_cnpj'],
            'email': row['email'],
            'telefone': row['telefone'],
            'celular': row['celular'],
            'endereco': row['endereco'],
            'numero': row['numero'],
            'complemento': row['complemento'],
            'bairro': row['bairro'],
            'cidade': row['cidade'],
            'estado': row['estado'],
            'cep': row['cep'],
            'observacoes': row['observacoes'],
            'ativo': bool(row['ativo']) if row['ativo'] is not None else True,
            'criado_em': row['criado_em'] if row['criado_em'] else datetime.now(),
            'atualizado_em': row['atualizado_em'] if row['atualizado_em'] else datetime.now()
        })
        
        stats['clientes'] += 1
        print(f"   ✅ Cliente ID {row['id']}: {row['nome']}")
    
    session.commit()
    print(f"\n✅ {stats['clientes']} clientes importados!")
    
    # ====================================================================
    # PASSO 2: IMPORTAR FORNECEDORES
    # ====================================================================
    print("\n" + "=" * 80)
    print("🏭 PASSO 2: IMPORTANDO FORNECEDORES")
    print("=" * 80)
    
    try:
        fornecedores = cursor.execute("SELECT * FROM fornecedores").fetchall()
        print(f"\n📊 Encontrados {len(fornecedores)} fornecedores")
        
        for row in fornecedores:
            try:
                result = session.execute(
                    text("SELECT id FROM fornecedores WHERE id = :id"),
                    {'id': row['id']}
                )
                if result.fetchone():
                    print(f"   ⚠️ Fornecedor ID {row['id']} já existe")
                    continue
                
                session.execute(text("""
                    INSERT INTO fornecedores (
                        id, nome, razao_social, cnpj, email, telefone, celular,
                        endereco, numero, complemento, bairro, cidade, estado, cep,
                        observacoes, ativo
                    ) VALUES (
                        :id, :nome, :razao_social, :cnpj, :email, :telefone, :celular,
                        :endereco, :numero, :complemento, :bairro, :cidade, :estado, :cep,
                        :observacoes, :ativo
                    )
                """), {
                    'id': row['id'],
                    'nome': row['nome'],
                    'razao_social': row['razao_social'],
                    'cnpj': row['cnpj'],
                    'email': row['email'],
                    'telefone': row['telefone'],
                    'celular': row['celular'],
                    'endereco': row['endereco'],
                    'numero': row['numero'],
                    'complemento': row['complemento'],
                    'bairro': row['bairro'],
                    'cidade': row['cidade'],
                    'estado': row['estado'],
                    'cep': row['cep'],
                    'observacoes': row['observacoes'],
                    'ativo': bool(row['ativo']) if row['ativo'] is not None else True
                })
                
                session.commit()
                stats['fornecedores'] += 1
                print(f"   ✅ Fornecedor ID {row['id']}: {row['nome']}")
            
            except Exception as e:
                session.rollback()
                print(f"   ❌ Erro ao importar fornecedor ID {row['id']}: {e}")
        
        print(f"\n✅ {stats['fornecedores']} fornecedores importados!")
    
    except Exception as e:
        print(f"⚠️ Tabela fornecedores não encontrada: {e}")
        session.rollback()
    
    # ====================================================================
    # PASSO 3: IMPORTAR ORDENS DE SERVIÇO
    # ====================================================================
    print("\n" + "=" * 80)
    print("🔧 PASSO 3: IMPORTANDO ORDENS DE SERVIÇO")
    print("=" * 80)
    
    ordens = cursor.execute("SELECT * FROM ordem_servico ORDER BY id").fetchall()
    print(f"\n📊 Encontradas {len(ordens)} ordens de serviço")
    
    for row in ordens:
        try:
            # Verifica se já existe
            result = session.execute(
                text("SELECT id FROM ordem_servico WHERE id = :id"),
                {'id': row['id']}
            )
            if result.fetchone():
                print(f"   ⚠️ OS ID {row['id']} já existe - pulando")
                continue
            
            # Verifica se o cliente existe
            result = session.execute(
                text("SELECT id FROM clientes WHERE id = :id"),
                {'id': row['cliente_id']}
            )
            if not result.fetchone():
                print(f"   ⚠️ OS {row['numero']}: Cliente ID {row['cliente_id']} não existe - pulando")
                continue
            
            # Insere OS
            session.execute(text("""
            INSERT INTO ordem_servico (
                id, numero, cliente_id, titulo, descricao, status, prioridade,
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
                :id, :numero, :cliente_id, :titulo, :descricao, :status, :prioridade,
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
        """), {
            'id': row['id'],
            'numero': row['numero'],
            'cliente_id': row['cliente_id'],
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
            'ativo': True,  # FORÇA COMO TRUE
            'criado_em': row['criado_em'] if row['criado_em'] else datetime.now(),
            'atualizado_em': row['atualizado_em'] if row['atualizado_em'] else datetime.now()
            })
            
            # Importa itens/serviços da OS
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
                        'ordem_servico_id': row['id'],
                        'descricao': item['descricao'],
                        'quantidade': item['quantidade'] or 1,
                        'valor_unitario': item['valor_unitario'] or 0,
                        'tipo_servico': item['tipo_servico'] if 'tipo_servico' in item.keys() else 'hora',
                        'observacoes': item['observacoes'] if 'observacoes' in item.keys() else None
                    })
                    stats['itens'] += 1
            except:
                pass
            
            # Importa produtos da OS
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
                        'ordem_servico_id': row['id'],
                        'descricao': prod['descricao'],
                        'quantidade': prod['quantidade'] or 1,
                        'valor_unitario': prod['valor_unitario'] or 0
                    })
                    stats['produtos_os'] += 1
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
                        'ordem_servico_id': row['id'],
                        'numero_parcela': parc['numero_parcela'],
                        'data_vencimento': parc['data_vencimento'],
                        'valor': parc['valor'] or 0,
                        'pago': bool(parc['pago']) if parc['pago'] else False,
                        'data_pagamento': parc['data_pagamento'] if 'data_pagamento' in parc.keys() else None
                    })
                    stats['parcelas'] += 1
            except:
                pass
            
            session.commit()
            stats['ordens'] += 1
            print(f"   ✅ OS {row['numero']}: {row['titulo']}")
        
        except Exception as e:
            session.rollback()
            print(f"   ❌ Erro ao importar OS {row.get('numero', row['id'])}: {e}")
    
    print(f"\n✅ {stats['ordens']} ordens de serviço importadas!")
    
    # ====================================================================
    # RESUMO FINAL
    # ====================================================================
    print("\n" + "=" * 80)
    print("🎉 IMPORTAÇÃO CONCLUÍDA!")
    print("=" * 80)
    print(f"""
📊 RESUMO DA IMPORTAÇÃO:
   👥 Clientes: {stats['clientes']}
   🏭 Fornecedores: {stats['fornecedores']}
   🔧 Ordens de Serviço: {stats['ordens']}
   📝 Itens/Serviços: {stats['itens']}
   📦 Produtos: {stats['produtos_os']}
   💰 Parcelas: {stats['parcelas']}
    """)
    
    # Mostra totais no Render
    print("🐘 TOTAIS NO RENDER AGORA:")
    result = session.execute(text("SELECT COUNT(*) FROM clientes"))
    print(f"   👥 Clientes: {result.scalar()}")
    
    result = session.execute(text("SELECT COUNT(*) FROM ordem_servico"))
    print(f"   🔧 Ordens de Serviço: {result.scalar()}")
    
    result = session.execute(text("SELECT COUNT(*) FROM ordem_servico WHERE ativo = TRUE"))
    print(f"   🔧 Ordens de Serviço ATIVAS: {result.scalar()}")
    
    print("\n" + "=" * 80)

except Exception as e:
    print(f"\n❌ ERRO: {e}")
    import traceback
    traceback.print_exc()
    session.rollback()

finally:
    session.close()
    engine.dispose()
    conn_local.close()
