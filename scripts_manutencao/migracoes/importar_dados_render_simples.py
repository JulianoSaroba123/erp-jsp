"""
Script simplificado para importar dados do SQLite para PostgreSQL Render
Importa apenas os campos essenciais para evitar erros de tamanho
"""
import sqlite3
from sqlalchemy import create_engine, text
from datetime import datetime

# URL do PostgreSQL do Render
DATABASE_URL = "postgresql://erp_jsp_db_iw6v_user:roBPw29VFmZKdksaGXw1tv4mYULKQwnl@dpg-d4pf1s49c44c73bdsdrg-a.oregon-postgres.render.com/erp_jsp_db_iw6v"

print("🔄 Conectando aos bancos de dados...")
# SQLite local
sqlite_conn = sqlite3.connect('c:/ERP_JSP/erp.db')
sqlite_conn.row_factory = sqlite3.Row

# PostgreSQL Render
pg_engine = create_engine(DATABASE_URL, isolation_level="AUTOCOMMIT")

print("\n📥 Importando CLIENTES...")
cursor = sqlite_conn.execute("""
    SELECT id, nome, tipo, cpf_cnpj, rg_ie, email, telefone, celular, cep, 
           endereco, numero, complemento, bairro, cidade, estado,
           criado_em, atualizado_em, ativo
    FROM clientes 
    WHERE ativo = 1
""")

clientes_importados = 0
with pg_engine.connect() as conn:
    for row in cursor:
        try:
            # Limitar tamanhos dos campos
            nome = (row['nome'] or '')[:200]
            email = (row['email'] or '')[:150]
            telefone = (row['telefone'] or '')[:20]
            celular = (row['celular'] or '')[:20]
            endereco = (row['endereco'] or '')[:200]
            complemento = (row['complemento'] or '')[:100]
            bairro = (row['bairro'] or '')[:100]
            cidade = (row['cidade'] or '')[:100]
            
            conn.execute(text("""
                INSERT INTO clientes (
                    nome, tipo, cpf_cnpj, rg_ie, email, telefone, celular, cep,
                    endereco, numero, complemento, bairro, cidade, estado,
                    criado_em, atualizado_em, ativo
                ) VALUES (
                    :nome, :tipo, :cpf_cnpj, :rg_ie, :email, :telefone, :celular, :cep,
                    :endereco, :numero, :complemento, :bairro, :cidade, :estado,
                    :criado_em, :atualizado_em, :ativo
                )
            """), {
                "nome": nome,
                "tipo": row['tipo'],
                "cpf_cnpj": row['cpf_cnpj'],
                "rg_ie": row['rg_ie'],
                "email": email,
                "telefone": telefone,
                "celular": celular,
                "cep": row['cep'],
                "endereco": endereco,
                "numero": row['numero'],
                "complemento": complemento,
                "bairro": bairro,
                "cidade": cidade,
                "estado": row['estado'],
                "criado_em": row['criado_em'],
                "atualizado_em": row['atualizado_em'],
                "ativo": bool(row['ativo'])  # Converter 0/1 para False/True
            })
            clientes_importados += 1
            print(f"  ✓ {nome}")
        except Exception as e:
            print(f"  ✗ Erro ao importar {row['nome']}: {str(e)[:100]}")

print(f"\n✅ {clientes_importados} clientes importados!")

print("\n📥 Importando FORNECEDORES...")
cursor = sqlite_conn.execute("""
    SELECT id, nome, telefone, email, endereco, cidade, estado, ativo
    FROM fornecedores 
    WHERE ativo = 1
""")

fornecedores_importados = 0
with pg_engine.connect() as conn:
    for row in cursor:
        try:
            nome = (row['nome'] or '')[:150]
            email = (row['email'] or '')[:150]
            telefone = (row['telefone'] or '')[:20]
            endereco = (row['endereco'] or '')[:200]
            cidade = (row['cidade'] or '')[:100]
            
            now = datetime.now()
            conn.execute(text("""
                INSERT INTO fornecedores (
                    nome, tipo, telefone, email, endereco, cidade, estado, ativo,
                    criado_em, atualizado_em
                ) VALUES (
                    :nome, :tipo, :telefone, :email, :endereco, :cidade, :estado, :ativo,
                    :criado_em, :atualizado_em
                )
            """), {
                "nome": nome,
                "tipo": "PJ",  # Define como Pessoa Jurídica por padrão
                "telefone": telefone,
                "email": email,
                "endereco": endereco,
                "cidade": cidade,
                "estado": row['estado'],
                "ativo": bool(row['ativo']),
                "criado_em": now,
                "atualizado_em": now
            })
            fornecedores_importados += 1
            print(f"  ✓ {nome}")
        except Exception as e:
            print(f"  ✗ Erro ao importar {row['nome']}: {str(e)[:100]}")

print(f"\n✅ {fornecedores_importados} fornecedores importados!")

print("\n📥 Importando PRODUTOS...")
cursor = sqlite_conn.execute("""
    SELECT id, nome, descricao, codigo_barras, unidade_medida, 
           preco_custo, markup, preco_venda, estoque_minimo, estoque_atual, ativo
    FROM produtos 
    WHERE ativo = 1
""")

produtos_importados = 0
with pg_engine.connect() as conn:
    for row in cursor:
        try:
            nome = (row['nome'] or '')[:200]
            descricao = (row['descricao'] or '')[:500]
            codigo_barras = (row['codigo_barras'] or '')[:50]
            now = datetime.now()
            
            conn.execute(text("""
                INSERT INTO produtos (
                    nome, descricao, codigo_barras, unidade_medida,
                    preco_custo, markup, preco_venda, estoque_minimo, estoque_atual, 
                    ativo, criado_em, atualizado_em
                ) VALUES (
                    :nome, :descricao, :codigo_barras, :unidade_medida,
                    :preco_custo, :markup, :preco_venda, :estoque_minimo, :estoque_atual, 
                    :ativo, :criado_em, :atualizado_em
                )
            """), {
                "nome": nome,
                "descricao": descricao,
                "codigo_barras": codigo_barras,
                "unidade_medida": row['unidade_medida'],
                "preco_custo": row['preco_custo'],
                "markup": row['markup'],
                "preco_venda": row['preco_venda'],
                "estoque_minimo": row['estoque_minimo'],
                "estoque_atual": row['estoque_atual'],
                "ativo": bool(row['ativo']),
                "criado_em": now,
                "atualizado_em": now
            })
            produtos_importados += 1
            print(f"  ✓ {nome}")
        except Exception as e:
            print(f"  ✗ Erro ao importar {row['nome']}: {str(e)[:100]}")

print(f"\n✅ {produtos_importados} produtos importados!")

# Verificar usuário admin (já existe, criado anteriormente)
print("\n👤 Verificando usuário admin...")
with pg_engine.connect() as conn:
    result = conn.execute(text("SELECT COUNT(*) FROM usuarios WHERE usuario = 'admin'"))
    if result.scalar() == 0:
        print("⚠️  Usuário admin não encontrado (deve ser criado manualmente)")
    else:
        print("✓ Usuário admin já existe")

sqlite_conn.close()

print("\n🎉 Importação concluída!")
print(f"📊 Resumo:")
print(f"   • {clientes_importados} clientes")
print(f"   • {fornecedores_importados} fornecedores")
print(f"   • {produtos_importados} produtos")
print("\n🌐 Acesse: https://erp-jsp-th5o.onrender.com")
print("🔑 Login: admin / admin123")
