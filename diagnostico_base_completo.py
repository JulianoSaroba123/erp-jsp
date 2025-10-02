#!/usr/bin/env python3
"""
Diagnóstico completo da base de dados
"""

import os
import sys
import sqlite3
from datetime import datetime

sys.path.append('.')

def verificar_base_dados():
    """Diagnóstico completo da base de dados"""
    
    print("=" * 60)
    print("🔍 DIAGNÓSTICO COMPLETO DA BASE DE DADOS")
    print("=" * 60)
    
    # 1. Verificar se o arquivo existe
    db_path = "database/database.db"
    print(f"\n1. Verificando arquivo da base: {db_path}")
    
    if not os.path.exists(db_path):
        print(f"❌ Arquivo da base não encontrado: {db_path}")
        return False
    
    file_size = os.path.getsize(db_path)
    print(f"✅ Arquivo encontrado - Tamanho: {file_size} bytes")
    
    # 2. Verificar se o arquivo está bloqueado
    print(f"\n2. Verificando se a base está bloqueada...")
    try:
        conn = sqlite3.connect(db_path, timeout=5.0)
        conn.execute("BEGIN IMMEDIATE;")
        conn.rollback()
        conn.close()
        print("✅ Base não está bloqueada")
    except sqlite3.OperationalError as e:
        print(f"❌ Base está bloqueada: {e}")
        return False
    
    # 3. Verificar integridade da base
    print(f"\n3. Verificando integridade da base...")
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("PRAGMA integrity_check;")
        resultado = cursor.fetchone()
        if resultado[0] == "ok":
            print("✅ Integridade da base OK")
        else:
            print(f"❌ Problema de integridade: {resultado[0]}")
            conn.close()
            return False
        conn.close()
    except Exception as e:
        print(f"❌ Erro ao verificar integridade: {e}")
        return False
    
    # 4. Verificar tabela ordem_servico
    print(f"\n4. Verificando tabela ordem_servico...")
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Verificar se a tabela existe
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='ordem_servico';")
        if not cursor.fetchone():
            print("❌ Tabela ordem_servico não encontrada")
            conn.close()
            return False
        print("✅ Tabela ordem_servico existe")
        
        # Verificar estrutura da tabela
        cursor.execute("PRAGMA table_info(ordem_servico);")
        colunas = cursor.fetchall()
        print(f"✅ Tabela tem {len(colunas)} colunas")
        
        # Verificar registros
        cursor.execute("SELECT COUNT(*) FROM ordem_servico;")
        total_registros = cursor.fetchone()[0]
        print(f"✅ Total de registros: {total_registros}")
        
        # Verificar se OS0351 (ID 2) existe
        cursor.execute("SELECT id, codigo, solicitante, status, data_atualizacao FROM ordem_servico WHERE id = 2;")
        os_351 = cursor.fetchone()
        if os_351:
            print(f"✅ OS0351 encontrada:")
            print(f"   ID: {os_351[0]}")
            print(f"   Código: {os_351[1]}")
            print(f"   Solicitante: {os_351[2]}")
            print(f"   Status: {os_351[3]}")
            print(f"   Última atualização: {os_351[4]}")
        else:
            print("❌ OS0351 (ID 2) não encontrada")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Erro ao verificar tabela: {e}")
        return False
    
    # 5. Teste de escrita
    print(f"\n5. Testando operação de escrita...")
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Tentar atualizar a OS0351
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute("""
            UPDATE ordem_servico 
            SET solicitante = ?, data_atualizacao = ? 
            WHERE id = 2
        """, (f"TESTE DIAGNÓSTICO {timestamp}", timestamp))
        
        linhas_afetadas = cursor.rowcount
        conn.commit()
        
        if linhas_afetadas > 0:
            print(f"✅ Teste de escrita OK - {linhas_afetadas} linha(s) atualizada(s)")
            
            # Verificar se a atualização foi persistida
            cursor.execute("SELECT solicitante, data_atualizacao FROM ordem_servico WHERE id = 2;")
            resultado = cursor.fetchone()
            print(f"✅ Dados atualizados: {resultado[0]} - {resultado[1]}")
        else:
            print("❌ Teste de escrita falhou - Nenhuma linha afetada")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Erro no teste de escrita: {e}")
        return False
    
    # 6. Verificar permissões do arquivo
    print(f"\n6. Verificando permissões do arquivo...")
    try:
        # Verificar se podemos ler
        if os.access(db_path, os.R_OK):
            print("✅ Permissão de leitura OK")
        else:
            print("❌ Sem permissão de leitura")
            
        # Verificar se podemos escrever
        if os.access(db_path, os.W_OK):
            print("✅ Permissão de escrita OK")
        else:
            print("❌ Sem permissão de escrita")
            return False
            
    except Exception as e:
        print(f"❌ Erro ao verificar permissões: {e}")
        return False
    
    # 7. Verificar processos que podem estar usando a base
    print(f"\n7. Verificando processos Python em execução...")
    try:
        import psutil
        processos_python = []
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                if proc.info['name'] and 'python' in proc.info['name'].lower():
                    processos_python.append(f"PID {proc.info['pid']}: {' '.join(proc.info['cmdline'])}")
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        
        if processos_python:
            print(f"⚠️  {len(processos_python)} processo(s) Python encontrado(s):")
            for proc in processos_python[:5]:  # Mostrar apenas os primeiros 5
                print(f"   {proc}")
        else:
            print("✅ Nenhum processo Python conflitante encontrado")
            
    except ImportError:
        print("⚠️  psutil não disponível - não foi possível verificar processos")
    except Exception as e:
        print(f"⚠️  Erro ao verificar processos: {e}")
    
    print(f"\n" + "=" * 60)
    print("✅ DIAGNÓSTICO CONCLUÍDO - BASE PARECE ESTAR OK")
    print("=" * 60)
    
    return True

def corrigir_problemas_base():
    """Tentar corrigir problemas comuns da base"""
    
    print("\n🔧 TENTANDO CORRIGIR PROBLEMAS...")
    
    db_path = "database/database.db"
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 1. Executar VACUUM para otimizar
        print("1. Executando VACUUM...")
        cursor.execute("VACUUM;")
        print("✅ VACUUM concluído")
        
        # 2. Reindexar
        print("2. Reindexando base...")
        cursor.execute("REINDEX;")
        print("✅ Reindexação concluída")
        
        # 3. Atualizar estatísticas
        print("3. Atualizando estatísticas...")
        cursor.execute("ANALYZE;")
        print("✅ Estatísticas atualizadas")
        
        conn.close()
        
        print("✅ Correções aplicadas com sucesso!")
        return True
        
    except Exception as e:
        print(f"❌ Erro ao corrigir problemas: {e}")
        return False

if __name__ == "__main__":
    print("Iniciando diagnóstico da base de dados...")
    
    if verificar_base_dados():
        print("\n🎯 BASE ESTÁ FUNCIONANDO CORRETAMENTE")
        print("O problema pode ser na aplicação Flask, não na base.")
    else:
        print("\n⚠️  PROBLEMAS DETECTADOS NA BASE")
        resposta = input("\nDeseja tentar corrigir os problemas? (s/n): ")
        if resposta.lower() == 's':
            corrigir_problemas_base()