"""
🚀 MIGRAÇÃO DE ORDENS DE SERVIÇO: SQLite → PostgreSQL (Render)
================================================================

Este script migra ordens de serviço do banco local (SQLite) para o 
PostgreSQL da Render de forma segura e idempotente.

Features:
- ✅ Verifica duplicatas pelo campo 'numero'
- ✅ Ajusta sequences automáticas
- ✅ Transação com rollback em caso de erro
- ✅ Logs detalhados para auditoria
- ✅ Lê credenciais de variáveis de ambiente

Autor: JSP Soluções
Data: 2025-12-09
"""

import os
import sys
from datetime import datetime
from decimal import Decimal
import psycopg
from dotenv import load_dotenv

# Carrega variáveis de ambiente
load_dotenv()

# =============================
# CONFIGURAÇÕES
# =============================

# Banco LOCAL (SQLite)
SQLITE_PATH = os.getenv('SQLITE_PATH', 'erp.db')

# Banco REMOTO (PostgreSQL Render)
PG_HOST = os.getenv('DB_HOST', 'dpg-d4pf1s49c44c73bdsdrg-a.oregon-postgres.render.com')
PG_USER = os.getenv('DB_USER', 'erp_jsp_db_iw6v_user')
PG_PASS = os.getenv('DB_PASS', 'roBPw29VFmZKdksaGXw1tv4mYLKQwnl')
PG_NAME = os.getenv('DB_NAME', 'erp_jsp_db_iw6v')
PG_PORT = int(os.getenv('DB_PORT', '5432'))

# Connection string completa
DATABASE_URL = f"postgresql://{PG_USER}:{PG_PASS}@{PG_HOST}:{PG_PORT}/{PG_NAME}"


def conectar_sqlite():
    """Conecta ao banco SQLite local"""
    import sqlite3
    
    if not os.path.exists(SQLITE_PATH):
        raise FileNotFoundError(f"❌ Banco SQLite não encontrado: {SQLITE_PATH}")
    
    conn = sqlite3.connect(SQLITE_PATH)
    conn.row_factory = sqlite3.Row  # Permite acessar colunas por nome
    print(f"✅ Conectado ao SQLite: {SQLITE_PATH}")
    return conn


def conectar_postgres():
    """Conecta ao banco PostgreSQL da Render"""
    try:
        conn = psycopg.connect(DATABASE_URL)
        print(f"✅ Conectado ao PostgreSQL: {PG_HOST}/{PG_NAME}")
        return conn
    except Exception as e:
        raise ConnectionError(f"❌ Falha ao conectar no Render: {e}")


def buscar_ordens_sqlite(conn_sqlite):
    """Busca todas as ordens de serviço ativas do SQLite"""
    cursor = conn_sqlite.cursor()
    
    query = """
        SELECT 
            numero, cliente_id, solicitante, descricao_problema, titulo, descricao,
            observacoes, status, prioridade, data_abertura, data_previsao, 
            data_inicio, data_conclusao, tecnico_responsavel, equipamento, marca_modelo,
            numero_serie, defeito_relatado, diagnostico, diagnostico_tecnico, solucao,
            km_inicial, km_final, total_km, hora_inicial, hora_final, total_horas,
            condicao_pagamento, numero_parcelas, valor_servico, valor_pecas, valor_desconto,
            valor_total, prazo_garantia, ativo, incluir_imagens_relatorio, forma_pagamento,
            num_parcelas, valor_entrada, valor_mao_obra, valor_produtos
        FROM ordem_servico
        WHERE ativo = 1
        ORDER BY id
    """
    
    cursor.execute(query)
    ordens = cursor.fetchall()
    print(f"📊 Encontradas {len(ordens)} ordens ativas no SQLite")
    return ordens


def ordem_existe_postgres(cursor_pg, numero):
    """Verifica se uma ordem já existe no Postgres pelo número"""
    cursor_pg.execute("SELECT id FROM ordem_servico WHERE numero = %s", (numero,))
    return cursor_pg.fetchone() is not None


def converter_valor(valor):
    """Converte valores para Decimal ou retorna 0"""
    if valor is None or valor == '':
        return Decimal('0')
    try:
        return Decimal(str(valor))
    except:
        return Decimal('0')


def inserir_ordem_postgres(cursor_pg, ordem):
    """Insere uma nova ordem no PostgreSQL"""
    
    query = """
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
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
        )
    """
    
    valores = (
        ordem['numero'],
        ordem['cliente_id'],
        ordem['solicitante'],
        ordem['descricao_problema'],
        ordem['titulo'] or 'Serviço',
        ordem['descricao'],
        ordem['observacoes'],
        ordem['status'] or 'aberta',
        ordem['prioridade'] or 'normal',
        ordem['data_abertura'] or datetime.now().date(),
        ordem['data_previsao'],
        ordem['data_inicio'],
        ordem['data_conclusao'],
        ordem['tecnico_responsavel'],
        ordem['equipamento'],
        ordem['marca_modelo'],
        ordem['numero_serie'],
        ordem['defeito_relatado'],
        ordem['diagnostico'],
        ordem['diagnostico_tecnico'],
        ordem['solucao'],
        ordem['km_inicial'],
        ordem['km_final'],
        ordem['total_km'],
        ordem['hora_inicial'],
        ordem['hora_final'],
        ordem['total_horas'],
        ordem['condicao_pagamento'],
        ordem['numero_parcelas'] or 1,
        converter_valor(ordem['valor_servico']),
        converter_valor(ordem['valor_pecas']),
        converter_valor(ordem['valor_desconto']),
        converter_valor(ordem['valor_total']),
        ordem['prazo_garantia'],
        True,  # ativo
        ordem['incluir_imagens_relatorio'] or False,
        ordem['forma_pagamento'] or 'a_vista',
        ordem['num_parcelas'] or 1,
        converter_valor(ordem['valor_entrada']),
        converter_valor(ordem['valor_mao_obra']),
        converter_valor(ordem['valor_produtos'])
    )
    
    cursor_pg.execute(query, valores)


def ajustar_sequence_postgres(cursor_pg):
    """Ajusta a sequence do ID para evitar conflitos futuros"""
    cursor_pg.execute("""
        SELECT setval(
            pg_get_serial_sequence('ordem_servico', 'id'), 
            COALESCE((SELECT MAX(id) FROM ordem_servico), 1)
        )
    """)
    novo_valor = cursor_pg.fetchone()[0]
    print(f"✅ Sequence ajustada para: {novo_valor}")


def main():
    """Pipeline principal de migração"""
    
    print("=" * 70)
    print("🚀 MIGRAÇÃO: SQLite → PostgreSQL (Render)")
    print("=" * 70)
    print()
    
    # Estatísticas
    total_processadas = 0
    total_inseridas = 0
    total_existentes = 0
    total_erros = 0
    
    conn_sqlite = None
    conn_pg = None
    
    try:
        # 1. Conectar aos bancos
        print("📡 Estabelecendo conexões...")
        conn_sqlite = conectar_sqlite()
        conn_pg = conectar_postgres()
        cursor_pg = conn_pg.cursor()
        print()
        
        # 2. Buscar ordens do SQLite
        print("🔍 Buscando ordens no SQLite...")
        ordens_sqlite = buscar_ordens_sqlite(conn_sqlite)
        print()
        
        # 3. Processar cada ordem
        print("⚙️  Processando ordens...")
        print("-" * 70)
        
        for ordem in ordens_sqlite:
            total_processadas += 1
            numero = ordem['numero']
            
            try:
                # Verifica se já existe
                if ordem_existe_postgres(cursor_pg, numero):
                    total_existentes += 1
                    print(f"  ✓ {numero:15} (já existe no Postgres)")
                else:
                    # Insere nova ordem
                    inserir_ordem_postgres(cursor_pg, ordem)
                    total_inseridas += 1
                    cliente_nome = ordem['solicitante'] or f"Cliente {ordem['cliente_id']}"
                    print(f"  + {numero:15} → {cliente_nome[:40]:40}")
                    
            except Exception as e:
                total_erros += 1
                print(f"  ❌ {numero:15} (erro: {str(e)[:50]})")
        
        print("-" * 70)
        print()
        
        # 4. Ajustar sequence
        print("🔧 Ajustando sequences...")
        ajustar_sequence_postgres(cursor_pg)
        print()
        
        # 5. Commit da transação
        print("💾 Persistindo alterações...")
        conn_pg.commit()
        print("✅ Commit realizado com sucesso!")
        print()
        
        # 6. Relatório final
        print("=" * 70)
        print("📊 RELATÓRIO FINAL")
        print("=" * 70)
        print(f"  Total processadas:  {total_processadas}")
        print(f"  ✅ Inseridas:        {total_inseridas}")
        print(f"  ⏭️  Já existentes:    {total_existentes}")
        print(f"  ❌ Erros:            {total_erros}")
        print("=" * 70)
        print()
        
        if total_erros > 0:
            print("⚠️  Migração concluída com erros. Revise os logs acima.")
        else:
            print("🎉 Migração concluída com sucesso!")
        
    except Exception as e:
        print()
        print("=" * 70)
        print(f"❌ ERRO CRÍTICO: {e}")
        print("=" * 70)
        
        if conn_pg:
            print("🔄 Fazendo rollback...")
            conn_pg.rollback()
            print("✅ Rollback concluído")
        
        sys.exit(1)
        
    finally:
        # Fechar conexões
        if conn_sqlite:
            conn_sqlite.close()
            print("🔌 Conexão SQLite fechada")
        
        if conn_pg:
            conn_pg.close()
            print("🔌 Conexão PostgreSQL fechada")


if __name__ == "__main__":
    main()
