"""
Importa TODOS OS DADOS do SQLite local para PostgreSQL Render
NA ORDEM CORRETA (Clientes primeiro, depois OS)
"""
import sqlite3
import os
import sys
from datetime import datetime
from decimal import Decimal

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

print("=" * 80)
print("🚀 IMPORTAÇÃO COMPLETA - SQLite → PostgreSQL Render")
print("   (NA ORDEM CORRETA)")
print("=" * 80)

# 1. CONECTA AO SQLITE LOCAL
print("\n📂 1. Conectando ao SQLite local...")
conn_sqlite = sqlite3.connect('database/database.db')
conn_sqlite.row_factory = sqlite3.Row
cursor = conn_sqlite.cursor()

# 2. CONECTA AO RENDER
print("🐘 2. Conectando ao PostgreSQL Render...")
from app.app import create_app

RENDER_DB_URL = 'postgresql://erp_jsp_db_iw6v_user:roBPw29VFmZKdksaGXw1tv4mYULKQwnl@dpg-d4pf1s49c44c73bdsdrg-a.oregon-postgres.render.com/erp_jsp_db_iw6v'

app = create_app()
app.config['SQLALCHEMY_DATABASE_URI'] = RENDER_DB_URL

with app.app_context():
    from app.extensoes import db
    from app.cliente.cliente_model import Cliente
    from app.fornecedor.fornecedor_model import Fornecedor
    from app.produto.produto_model import Produto
    from app.ordem_servico.ordem_servico_model import (
        OrdemServico, OrdemServicoItem, OrdemServicoProduto, OrdemServicoParcela
    )
    
    stats = {
        'clientes': 0,
        'fornecedores': 0,
        'produtos': 0,
        'ordens': 0,
        'itens': 0,
        'produtos_os': 0,
        'parcelas': 0
    }
    
    # ====================================================================
    # PASSO 1: IMPORTAR CLIENTES
    # ====================================================================
    print("\n" + "=" * 80)
    print("👥 PASSO 1: IMPORTANDO CLIENTES")
    print("=" * 80)
    
    try:
        clientes_local = cursor.execute("SELECT * FROM cliente").fetchall()
        print(f"\n📊 Encontrados {len(clientes_local)} clientes no SQLite local")
        
        for row in clientes_local:
            cliente_id = row['id']
            
            # Verifica se já existe
            existe = Cliente.query.filter_by(id=cliente_id).first()
            if existe:
                print(f"   ⚠️ Cliente ID {cliente_id} ({row['nome']}) já existe - pulando")
                continue
            
            # Cria novo cliente
            novo_cliente = Cliente(
                id=cliente_id,
                nome=row['nome'],
                cpf_cnpj=row['cpf_cnpj'],
                email=row['email'],
                telefone=row['telefone'],
                celular=row['celular'],
                endereco=row['endereco'],
                numero=row['numero'],
                complemento=row['complemento'],
                bairro=row['bairro'],
                cidade=row['cidade'],
                estado=row['estado'],
                cep=row['cep'],
                observacoes=row['observacoes'],
                ativo=bool(row['ativo']) if row['ativo'] is not None else True,
                criado_em=datetime.fromisoformat(row['criado_em']) if row['criado_em'] else datetime.now(),
                atualizado_em=datetime.fromisoformat(row['atualizado_em']) if row['atualizado_em'] else datetime.now()
            )
            
            db.session.add(novo_cliente)
            stats['clientes'] += 1
            print(f"   ✅ Cliente ID {cliente_id}: {row['nome']}")
        
        db.session.commit()
        print(f"\n✅ {stats['clientes']} clientes importados com sucesso!")
        
    except Exception as e:
        print(f"❌ Erro ao importar clientes: {e}")
        db.session.rollback()
    
    # ====================================================================
    # PASSO 2: IMPORTAR FORNECEDORES
    # ====================================================================
    print("\n" + "=" * 80)
    print("🏭 PASSO 2: IMPORTANDO FORNECEDORES")
    print("=" * 80)
    
    try:
        fornecedores_local = cursor.execute("SELECT * FROM fornecedores").fetchall()
        print(f"\n📊 Encontrados {len(fornecedores_local)} fornecedores no SQLite local")
        
        for row in fornecedores_local:
            fornecedor_id = row['id']
            
            existe = Fornecedor.query.filter_by(id=fornecedor_id).first()
            if existe:
                print(f"   ⚠️ Fornecedor ID {fornecedor_id} já existe - pulando")
                continue
            
            novo_fornecedor = Fornecedor(
                id=fornecedor_id,
                nome=row['nome'],
                razao_social=row['razao_social'],
                cnpj=row['cnpj'],
                email=row['email'],
                telefone=row['telefone'],
                celular=row['celular'],
                endereco=row['endereco'],
                numero=row['numero'],
                complemento=row['complemento'],
                bairro=row['bairro'],
                cidade=row['cidade'],
                estado=row['estado'],
                cep=row['cep'],
                observacoes=row['observacoes'],
                ativo=bool(row['ativo']) if row['ativo'] is not None else True
            )
            
            db.session.add(novo_fornecedor)
            stats['fornecedores'] += 1
            print(f"   ✅ Fornecedor ID {fornecedor_id}: {row['nome']}")
        
        db.session.commit()
        print(f"\n✅ {stats['fornecedores']} fornecedores importados!")
        
    except Exception as e:
        print(f"❌ Erro ao importar fornecedores: {e}")
        db.session.rollback()
    
    # ====================================================================
    # PASSO 3: IMPORTAR PRODUTOS
    # ====================================================================
    print("\n" + "=" * 80)
    print("📦 PASSO 3: IMPORTANDO PRODUTOS")
    print("=" * 80)
    
    try:
        # Tenta diferentes nomes de tabela
        for table_name in ['produto', 'produtos']:
            try:
                produtos_local = cursor.execute(f"SELECT * FROM {table_name}").fetchall()
                print(f"\n📊 Encontrados {len(produtos_local)} produtos no SQLite local (tabela: {table_name})")
                
                for row in produtos_local:
                    produto_id = row['id']
                    
                    existe = Produto.query.filter_by(id=produto_id).first()
                    if existe:
                        print(f"   ⚠️ Produto ID {produto_id} já existe - pulando")
                        continue
                    
                    novo_produto = Produto(
                        id=produto_id,
                        descricao=row['descricao'],
                        codigo=row['codigo'] if 'codigo' in row.keys() else None,
                        unidade=row['unidade'] if 'unidade' in row.keys() else 'UN',
                        preco_custo=Decimal(str(row['preco_custo'])) if row['preco_custo'] else Decimal('0'),
                        preco_venda=Decimal(str(row['preco_venda'])) if row['preco_venda'] else Decimal('0'),
                        estoque=int(row['estoque']) if 'estoque' in row.keys() and row['estoque'] else 0,
                        estoque_minimo=int(row['estoque_minimo']) if 'estoque_minimo' in row.keys() and row['estoque_minimo'] else 0,
                        ativo=bool(row['ativo']) if row['ativo'] is not None else True
                    )
                    
                    db.session.add(novo_produto)
                    stats['produtos'] += 1
                    print(f"   ✅ Produto ID {produto_id}: {row['descricao']}")
                
                db.session.commit()
                print(f"\n✅ {stats['produtos']} produtos importados!")
                break
                
            except sqlite3.OperationalError:
                continue
        
    except Exception as e:
        print(f"❌ Erro ao importar produtos: {e}")
        db.session.rollback()
    
    # ====================================================================
    # PASSO 4: IMPORTAR ORDENS DE SERVIÇO
    # ====================================================================
    print("\n" + "=" * 80)
    print("🔧 PASSO 4: IMPORTANDO ORDENS DE SERVIÇO")
    print("=" * 80)
    
    try:
        os_local = cursor.execute("SELECT * FROM ordem_servico").fetchall()
        print(f"\n📊 Encontradas {len(os_local)} ordens de serviço no SQLite local")
        
        for row in os_local:
            os_id = row['id']
            
            # Verifica se já existe
            existe = OrdemServico.query.filter_by(id=os_id).first()
            if existe:
                print(f"   ⚠️ OS ID {os_id} ({row['numero']}) já existe - pulando")
                continue
            
            # Verifica se o cliente existe
            cliente_existe = Cliente.query.filter_by(id=row['cliente_id']).first()
            if not cliente_existe:
                print(f"   ⚠️ OS {row['numero']}: Cliente ID {row['cliente_id']} não existe - pulando")
                continue
            
            # Cria OS
            nova_os = OrdemServico(
                id=os_id,
                numero=row['numero'],
                cliente_id=row['cliente_id'],
                titulo=row['titulo'] or 'OS sem título',
                descricao=row['descricao'],
                status=row['status'] or 'aberta',
                prioridade=row['prioridade'] or 'normal',
                data_abertura=datetime.fromisoformat(row['data_abertura']).date() if row['data_abertura'] else datetime.now().date(),
                data_prevista=datetime.fromisoformat(row['data_prevista']).date() if row['data_prevista'] else None,
                data_inicio=datetime.fromisoformat(row['data_inicio']) if row['data_inicio'] else None,
                data_conclusao=datetime.fromisoformat(row['data_conclusao']) if row['data_conclusao'] else None,
                tecnico_responsavel=row['tecnico_responsavel'],
                equipamento=row['equipamento'],
                marca_modelo=row['marca_modelo'],
                numero_serie=row['numero_serie'],
                diagnostico=row['diagnostico'],
                diagnostico_tecnico=row['diagnostico_tecnico'],
                solucao=row['solucao'],
                observacoes=row['observacoes'],
                valor_servico=Decimal(str(row['valor_servico'])) if row['valor_servico'] else Decimal('0'),
                valor_pecas=Decimal(str(row['valor_pecas'])) if row['valor_pecas'] else Decimal('0'),
                valor_desconto=Decimal(str(row['valor_desconto'])) if row['valor_desconto'] else Decimal('0'),
                valor_total=Decimal(str(row['valor_total'])) if row['valor_total'] else Decimal('0'),
                condicao_pagamento=row['condicao_pagamento'] or 'a_vista',
                status_pagamento=row['status_pagamento'] or 'pendente',
                numero_parcelas=row['numero_parcelas'] or 1,
                valor_entrada=Decimal(str(row['valor_entrada'])) if row['valor_entrada'] else None,
                data_primeira_parcela=datetime.fromisoformat(row['data_primeira_parcela']).date() if row['data_primeira_parcela'] else None,
                data_vencimento_pagamento=datetime.fromisoformat(row['data_vencimento_pagamento']).date() if row['data_vencimento_pagamento'] else None,
                descricao_pagamento=row['descricao_pagamento'],
                prazo_garantia=row['prazo_garantia'] or 0,
                solicitante=row['solicitante'],
                descricao_problema=row['descricao_problema'],
                tipo_servico=row['tipo_servico'] if 'tipo_servico' in row.keys() else 'manutencao',
                km_inicial=row['km_inicial'] if 'km_inicial' in row.keys() else None,
                km_final=row['km_final'] if 'km_final' in row.keys() else None,
                total_km=row['total_km'] if 'total_km' in row.keys() else None,
                hora_inicial=datetime.strptime(row['hora_inicial'], '%H:%M:%S').time() if row.get('hora_inicial') else None,
                hora_final=datetime.strptime(row['hora_final'], '%H:%M:%S').time() if row.get('hora_final') else None,
                total_horas=row['total_horas'] if 'total_horas' in row.keys() else None,
                ativo=bool(row['ativo']) if row['ativo'] is not None else True,
                criado_em=datetime.fromisoformat(row['criado_em']) if row['criado_em'] else datetime.now(),
                atualizado_em=datetime.fromisoformat(row['atualizado_em']) if row['atualizado_em'] else datetime.now()
            )
            
            db.session.add(nova_os)
            db.session.flush()  # Para obter o ID
            
            # Importa itens/serviços
            try:
                itens = cursor.execute(
                    "SELECT * FROM ordem_servico_itens WHERE ordem_servico_id = ?",
                    (os_id,)
                ).fetchall()
                
                for item in itens:
                    novo_item = OrdemServicoItem(
                        ordem_servico_id=nova_os.id,
                        descricao=item['descricao'],
                        quantidade=Decimal(str(item['quantidade'])) if item['quantidade'] else Decimal('1'),
                        valor_unitario=Decimal(str(item['valor_unitario'])) if item['valor_unitario'] else Decimal('0'),
                        tipo_servico=item['tipo_servico'] if 'tipo_servico' in item.keys() else 'hora',
                        observacoes=item['observacoes'] if 'observacoes' in item.keys() else None
                    )
                    db.session.add(novo_item)
                    stats['itens'] += 1
            except:
                pass
            
            # Importa produtos
            try:
                produtos = cursor.execute(
                    "SELECT * FROM ordem_servico_produtos WHERE ordem_servico_id = ?",
                    (os_id,)
                ).fetchall()
                
                for prod in produtos:
                    novo_prod = OrdemServicoProduto(
                        ordem_servico_id=nova_os.id,
                        descricao=prod['descricao'],
                        quantidade=Decimal(str(prod['quantidade'])) if prod['quantidade'] else Decimal('1'),
                        valor_unitario=Decimal(str(prod['valor_unitario'])) if prod['valor_unitario'] else Decimal('0')
                    )
                    db.session.add(novo_prod)
                    stats['produtos_os'] += 1
            except:
                pass
            
            # Importa parcelas
            try:
                parcelas = cursor.execute(
                    "SELECT * FROM ordem_servico_parcelas WHERE ordem_servico_id = ?",
                    (os_id,)
                ).fetchall()
                
                for parc in parcelas:
                    nova_parc = OrdemServicoParcela(
                        ordem_servico_id=nova_os.id,
                        numero_parcela=parc['numero_parcela'],
                        data_vencimento=datetime.fromisoformat(parc['data_vencimento']).date() if parc['data_vencimento'] else None,
                        valor=Decimal(str(parc['valor'])) if parc['valor'] else Decimal('0'),
                        pago=bool(parc['pago']) if parc['pago'] else False,
                        data_pagamento=datetime.fromisoformat(parc['data_pagamento']).date() if parc.get('data_pagamento') else None
                    )
                    db.session.add(nova_parc)
                    stats['parcelas'] += 1
            except:
                pass
            
            stats['ordens'] += 1
            print(f"   ✅ OS {row['numero']}: {row['titulo']}")
        
        db.session.commit()
        print(f"\n✅ {stats['ordens']} ordens de serviço importadas!")
        
    except Exception as e:
        print(f"❌ Erro ao importar ordens de serviço: {e}")
        import traceback
        traceback.print_exc()
        db.session.rollback()
    
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
   📦 Produtos: {stats['produtos']}
   🔧 Ordens de Serviço: {stats['ordens']}
   📝 Itens/Serviços: {stats['itens']}
   📦 Produtos OS: {stats['produtos_os']}
   💰 Parcelas: {stats['parcelas']}
    """)
    
    # Mostra totais no Render
    print("🐘 TOTAIS NO RENDER AGORA:")
    print(f"   👥 Clientes: {Cliente.query.count()}")
    print(f"   🏭 Fornecedores: {Fornecedor.query.count()}")
    print(f"   📦 Produtos: {Produto.query.count()}")
    print(f"   🔧 Ordens de Serviço: {OrdemServico.query.count()}")
    
    print("\n" + "=" * 80)

conn_sqlite.close()
