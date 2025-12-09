"""
🚀 MIGRAÇÃO DE ORDENS DE SERVIÇO: SQLite → PostgreSQL (Render)
================================================================

Migra ordens de serviço usando SQLAlchemy (compatível com Python 3.13)

Autor: JSP Soluções
Data: 2025-12-09
"""

import os
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from decimal import Decimal

# =============================
# CONFIGURAÇÕES
# =============================
SQLITE_PATH = "erp.db"
DATABASE_URL = os.getenv(
    'DATABASE_URL',
    'postgresql://erp_jsp_db_iw6v_user:roBPw29VFmZKdksaGXw1tv4mYLKQwnl@dpg-d4pf1s49c44c73bdsdrg-a.oregon-postgres.render.com/erp_jsp_db_iw6v'
)

print("="*70)
print("🚀 MIGRAÇÃO DE ORDENS DE SERVIÇO: SQLite → PostgreSQL")
print("="*70)

# Conecta SQLite
sqlite_engine = create_engine(f'sqlite:///{SQLITE_PATH}')
SQLiteSession = sessionmaker(bind=sqlite_engine)
session_sqlite = SQLiteSession()

# Conecta PostgreSQL
pg_engine = create_engine(DATABASE_URL)
PGSession = sessionmaker(bind=pg_engine)
session_pg = PGSession()

print(f"\n✅ Conectado ao SQLite: {SQLITE_PATH}")
print(f"✅ Conectado ao PostgreSQL: Render\n")

# =============================
# BUSCA ORDENS NO SQLITE
# =============================
query_sqlite = text("""
    SELECT * FROM ordem_servico WHERE ativo = 1
""")

ordens_sqlite = session_sqlite.execute(query_sqlite).fetchall()
total_sqlite = len(ordens_sqlite)
print(f"📦 Total de Ordens no SQLite: {total_sqlite}")

# =============================
# BUSCA ORDENS NO POSTGRES
# =============================
query_pg = text("SELECT numero FROM ordem_servico")
ordens_pg = session_pg.execute(query_pg).fetchall()
numeros_existentes = {row[0] for row in ordens_pg}
print(f"📦 Total de Ordens no Render: {len(numeros_existentes)}\n")

# =============================
# MIGRAÇÃO
# =============================
importadas = 0
puladas = 0
erros = 0

print("🔄 Iniciando migração...\n")

for ordem in ordens_sqlite:
    numero = ordem.numero
    
    # Verifica se já existe
    if numero in numeros_existentes:
        puladas += 1
        print(f"⏭️  OS #{numero} já existe no Render (pulada)")
        continue
    
    try:
        # Prepara dados
        dados = {
            'numero': ordem.numero,
            'cliente_id': ordem.cliente_id,
            'solicitante': ordem.solicitante,
            'descricao_problema': ordem.descricao_problema,
            'titulo': ordem.titulo,
            'descricao': ordem.descricao,
            'observacoes': ordem.observacoes,
            'status': ordem.status,
            'prioridade': ordem.prioridade,
            'data_abertura': ordem.data_abertura,
            'data_previsao': ordem.data_previsao,
            'data_inicio': ordem.data_inicio,
            'data_conclusao': ordem.data_conclusao,
            'tecnico_responsavel': ordem.tecnico_responsavel,
            'equipamento': ordem.equipamento,
            'marca_modelo': ordem.marca_modelo,
            'numero_serie': ordem.numero_serie,
            'defeito_relatado': ordem.defeito_relatado,
            'diagnostico': ordem.diagnostico,
            'diagnostico_tecnico': ordem.diagnostico_tecnico,
            'solucao': ordem.solucao,
            'km_inicial': Decimal(str(ordem.km_inicial)) if ordem.km_inicial else None,
            'km_final': Decimal(str(ordem.km_final)) if ordem.km_final else None,
            'total_km': Decimal(str(ordem.total_km)) if ordem.total_km else None,
            'hora_inicial': ordem.hora_inicial,
            'hora_final': ordem.hora_final,
            'total_horas': Decimal(str(ordem.total_horas)) if ordem.total_horas else None,
            'condicao_pagamento': ordem.condicao_pagamento,
            'numero_parcelas': ordem.numero_parcelas,
            'valor_servico': Decimal(str(ordem.valor_servico)) if ordem.valor_servico else Decimal('0'),
            'valor_pecas': Decimal(str(ordem.valor_pecas)) if ordem.valor_pecas else Decimal('0'),
            'valor_desconto': Decimal(str(ordem.valor_desconto)) if ordem.valor_desconto else Decimal('0'),
            'valor_total': Decimal(str(ordem.valor_total)) if ordem.valor_total else Decimal('0'),
            'prazo_garantia': ordem.prazo_garantia,
            'ativo': ordem.ativo,
            'incluir_imagens_relatorio': ordem.incluir_imagens_relatorio,
            'forma_pagamento': ordem.forma_pagamento,
            'num_parcelas': ordem.num_parcelas,
            'valor_entrada': Decimal(str(ordem.valor_entrada)) if ordem.valor_entrada else Decimal('0'),
            'valor_mao_obra': Decimal(str(ordem.valor_mao_obra)) if ordem.valor_mao_obra else Decimal('0'),
            'valor_produtos': Decimal(str(ordem.valor_produtos)) if ordem.valor_produtos else Decimal('0')
        }
        
        # Insere no PostgreSQL
        insert_query = text("""
            INSERT INTO ordem_servico (
                numero, cliente_id, solicitante, descricao_problema, titulo, descricao,
                observacoes, status, prioridade, data_abertura, data_previsao, 
                data_inicio, data_conclusao, tecnico_responsavel, equipamento, marca_modelo,
                numero_serie, defeito_relatado, diagnostico, diagnostico_tecnico, solucao,
                km_inicial, km_final, total_km, hora_inicial, hora_final, total_horas,
                condicao_pagamento, numero_parcelas, valor_servico, valor_pecas, valor_desconto,
                valor_total, prazo_garantia, ativo, incluir_imagens_relatorio, forma_pagamento,
                num_parcelas, valor_entrada, valor_mao_obra, valor_produtos
            ) VALUES (
                :numero, :cliente_id, :solicitante, :descricao_problema, :titulo, :descricao,
                :observacoes, :status, :prioridade, :data_abertura, :data_previsao, 
                :data_inicio, :data_conclusao, :tecnico_responsavel, :equipamento, :marca_modelo,
                :numero_serie, :defeito_relatado, :diagnostico, :diagnostico_tecnico, :solucao,
                :km_inicial, :km_final, :total_km, :hora_inicial, :hora_final, :total_horas,
                :condicao_pagamento, :numero_parcelas, :valor_servico, :valor_pecas, :valor_desconto,
                :valor_total, :prazo_garantia, :ativo, :incluir_imagens_relatorio, :forma_pagamento,
                :num_parcelas, :valor_entrada, :valor_mao_obra, :valor_produtos
            )
        """)
        
        session_pg.execute(insert_query, dados)
        session_pg.commit()
        
        importadas += 1
        print(f"✅ OS #{numero} importada com sucesso")
        
    except Exception as e:
        session_pg.rollback()
        erros += 1
        print(f"❌ Erro ao importar OS #{numero}: {e}")
        continue

# =============================
# AJUSTA SEQUENCE
# =============================
print("\n🔧 Ajustando sequence do PostgreSQL...")
try:
    ajuste_query = text("""
        SELECT setval(
            pg_get_serial_sequence('ordem_servico', 'id'), 
            (SELECT MAX(id) FROM ordem_servico)
        )
    """)
    session_pg.execute(ajuste_query)
    session_pg.commit()
    print("✅ Sequence ajustada com sucesso")
except Exception as e:
    print(f"⚠️  Aviso: Não foi possível ajustar sequence: {e}")

# =============================
# RESUMO FINAL
# =============================
print("\n" + "="*70)
print("📊 RESUMO DA MIGRAÇÃO")
print("="*70)
print(f"📦 Total no SQLite: {total_sqlite}")
print(f"✅ Importadas: {importadas}")
print(f"⏭️  Puladas (já existiam): {puladas}")
print(f"❌ Erros: {erros}")
print("="*70)

# Fecha conexões
session_sqlite.close()
session_pg.close()

print("\n✅ Migração concluída!")
print("\n🌐 Acesse: https://erp-jsp-th5o.onrender.com/ordem_servico/listar")
