#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script para exportar dados do SQLite local e importar no PostgreSQL do Render
Execute DEPOIS de rodar setup_render.py no Render
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def exportar_clientes_local():
    """Exporta clientes do banco local SQLite."""
    print("\n📦 Exportando dados do SQLite local...\n")
    
    # Conectar ao SQLite local
    import sqlite3
    conn = sqlite3.connect('c:/ERP_JSP/erp.db')
    cursor = conn.cursor()
    
    # Buscar todos os clientes
    cursor.execute('SELECT * FROM clientes WHERE ativo = 1')
    clientes = cursor.fetchall()
    
    # Pegar nomes das colunas
    cursor.execute('PRAGMA table_info(clientes)')
    colunas = [col[1] for col in cursor.fetchall()]
    
    conn.close()
    
    print(f"✅ {len(clientes)} clientes encontrados no banco local")
    print(f"📋 Colunas: {', '.join(colunas[:5])}...\n")
    
    return colunas, clientes

def importar_clientes_render(colunas, dados):
    """Importa clientes para o PostgreSQL do Render."""
    from app.app import create_app
    from app.extensoes import db
    from app.cliente.cliente_model import Cliente
    
    app = create_app()
    
    with app.app_context():
        print("🚀 Importando para PostgreSQL do Render...\n")
        
        importados = 0
        erros = 0
        
        for registro in dados:
            try:
                # Criar dicionário com dados
                dados_cliente = dict(zip(colunas, registro))
                
                # Remover campos que não devem ser inseridos diretamente
                dados_cliente.pop('id', None)
                dados_cliente.pop('criado_em', None)
                dados_cliente.pop('atualizado_em', None)
                
                # Verificar se já existe
                cpf_cnpj = dados_cliente.get('cpf_cnpj')
                if cpf_cnpj:
                    existente = Cliente.query.filter_by(cpf_cnpj=cpf_cnpj).first()
                    if existente:
                        print(f"⏭️  Pulando: {dados_cliente.get('nome')} (CPF/CNPJ já existe)")
                        continue
                
                # Criar cliente
                cliente = Cliente(**dados_cliente)
                db.session.add(cliente)
                db.session.flush()
                
                importados += 1
                print(f"✅ Importado: {cliente.nome}")
                
            except Exception as e:
                erros += 1
                print(f"❌ Erro ao importar {dados_cliente.get('nome', '???')}: {e}")
                db.session.rollback()
        
        # Commit final
        try:
            db.session.commit()
            print(f"\n{'='*60}")
            print(f"✅ IMPORTAÇÃO CONCLUÍDA")
            print(f"{'='*60}")
            print(f"✓ Importados com sucesso: {importados}")
            print(f"✗ Erros: {erros}")
            print(f"{'='*60}\n")
        except Exception as e:
            db.session.rollback()
            print(f"\n❌ ERRO no commit final: {e}\n")

if __name__ == '__main__':
    try:
        print("\n" + "="*60)
        print("📤 IMPORTAÇÃO SQLite → PostgreSQL Render")
        print("="*60)
        
        # Verificar se está rodando localmente
        if not os.path.exists('c:/ERP_JSP/erp.db'):
            print("\n❌ Arquivo erp.db não encontrado!")
            print("Este script deve ser executado LOCALMENTE com acesso ao erp.db\n")
            sys.exit(1)
        
        # Exportar do local
        colunas, clientes = exportar_clientes_local()
        
        if not clientes:
            print("⚠️  Nenhum cliente para importar\n")
            sys.exit(0)
        
        # Importar para o Render (precisa ter DATABASE_URL configurada)
        database_url = os.getenv('DATABASE_URL')
        if not database_url:
            print("\n⚠️  DATABASE_URL não configurada!")
            print("Para importar para o Render, você precisa:")
            print("1. Copiar a URL do PostgreSQL do Render")
            print("2. Criar um arquivo .env com: DATABASE_URL=postgresql+psycopg://...")
            print("3. Rodar este script novamente\n")
            sys.exit(1)
        
        importar_clientes_render(colunas, clientes)
        
    except Exception as e:
        print(f"\n❌ ERRO FATAL: {e}\n")
        import traceback
        traceback.print_exc()
        sys.exit(1)
