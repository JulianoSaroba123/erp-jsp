#!/usr/bin/env python3
"""
Verificar estrutura atual da base e criar tabelas necessárias
"""

import os
import sys
import sqlite3

sys.path.append('.')

def verificar_tabelas_existentes():
    """Verificar que tabelas existem na base"""
    
    db_path = "database/database.db"
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Listar todas as tabelas
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tabelas = cursor.fetchall()
        
        print("📋 TABELAS EXISTENTES NA BASE:")
        print("=" * 40)
        
        if tabelas:
            for tabela in tabelas:
                nome_tabela = tabela[0]
                print(f"✅ {nome_tabela}")
                
                # Contar registros
                try:
                    cursor.execute(f"SELECT COUNT(*) FROM {nome_tabela};")
                    count = cursor.fetchone()[0]
                    print(f"   └── {count} registro(s)")
                except:
                    print(f"   └── (erro ao contar registros)")
        else:
            print("❌ Nenhuma tabela encontrada!")
        
        conn.close()
        return tabelas
        
    except Exception as e:
        print(f"❌ Erro ao verificar tabelas: {e}")
        return []

def criar_estrutura_base():
    """Criar estrutura completa da base usando Flask-Migrate"""
    
    print("\n🔧 CRIANDO ESTRUTURA DA BASE...")
    
    try:
        # Importar a aplicação Flask e modelos
        from aplicacao import criar_app, db
        from aplicacao.ordem_servico.ordem_servico_model import OrdemServico
        from aplicacao.cliente.cliente_model import Cliente
        
        app = criar_app()
        
        with app.app_context():
            print("1. Criando todas as tabelas...")
            db.create_all()
            print("✅ Tabelas criadas com sucesso!")
            
            # Verificar se as tabelas foram criadas
            print("\n2. Verificando tabelas criadas...")
            inspector = db.inspect(db.engine)
            tabelas = inspector.get_table_names()
            
            for tabela in tabelas:
                print(f"✅ {tabela}")
            
            return True
            
    except Exception as e:
        print(f"❌ Erro ao criar estrutura: {e}")
        return False

def popular_dados_teste():
    """Popular base com dados de teste se necessário"""
    
    print("\n📝 VERIFICANDO DADOS DE TESTE...")
    
    try:
        from aplicacao import criar_app, db
        from aplicacao.ordem_servico.ordem_servico_model import OrdemServico
        from aplicacao.cliente.cliente_model import Cliente
        
        app = criar_app()
        
        with app.app_context():
            # Verificar se já existe a OS0351
            os_existente = OrdemServico.query.filter_by(codigo='OS0351').first()
            
            if not os_existente:
                print("Criando OS0351 de teste...")
                
                # Verificar se existe cliente
                cliente = Cliente.query.get(7)
                if not cliente:
                    print("Cliente ID 7 não encontrado, usando ID 1 ou criando cliente teste...")
                    cliente = Cliente.query.first()
                    if not cliente:
                        # Criar cliente teste
                        cliente = Cliente(
                            nome="MR JACKY CONFECCAO E REPRESENTACAO LTDA",
                            email="teste@teste.com",
                            telefone="(11) 99999-9999"
                        )
                        db.session.add(cliente)
                        db.session.commit()
                
                # Criar OS0351
                nova_os = OrdemServico(
                    codigo='OS0351',
                    cliente_id=cliente.id,
                    solicitante='João Silva',
                    contato='(11) 99999-1234',
                    status='Em Andamento',
                    prioridade='Media',
                    tipo_servico='Manutenção',
                    equipamento_nome='Ar Condicionado Split',
                    descricao_problema='Equipamento não refrigera adequadamente',
                    valor_total=500.00
                )
                
                db.session.add(nova_os)
                db.session.commit()
                
                print(f"✅ OS0351 criada com ID: {nova_os.id}")
            else:
                print(f"✅ OS0351 já existe com ID: {os_existente.id}")
            
            return True
            
    except Exception as e:
        print(f"❌ Erro ao popular dados: {e}")
        return False

if __name__ == "__main__":
    print("🔍 VERIFICANDO E CORRIGINDO ESTRUTURA DA BASE\n")
    
    # 1. Verificar tabelas existentes
    tabelas_existentes = verificar_tabelas_existentes()
    
    # 2. Criar estrutura se necessário
    if not any('ordem_servico' in str(t) for t in tabelas_existentes):
        print("\n❌ Tabela ordem_servico não encontrada!")
        criar_estrutura_base()
        
        # 3. Popular com dados de teste
        popular_dados_teste()
    else:
        print("\n✅ Estrutura da base parece estar OK!")
    
    print("\n" + "=" * 60)
    print("🎯 VERIFICAÇÃO CONCLUÍDA")
    print("=" * 60)