"""
Script para adicionar coluna kit_id na tabela calculo_energia_solar
e tentar inferir o kit_id baseado nos equipamentos selecionados
"""
import os
import sys

# Adicionar o diretório raiz ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.extensoes import db
from sqlalchemy import text, inspect

def adicionar_coluna_kit_id():
    """Adiciona coluna kit_id se não existir"""
    app = create_app()
    
    with app.app_context():
        try:
            # Verificar se a coluna já existe
            inspector = inspect(db.engine)
            columns = [col['name'] for col in inspector.get_columns('calculo_energia_solar')]
            
            if 'kit_id' in columns:
                print('✅ Coluna kit_id já existe!')
                return True
                
            print('🔧 Adicionando coluna kit_id...')
            
            # Adicionar coluna kit_id
            with db.engine.connect() as conn:
                # Para PostgreSQL ou SQLite
                try:
                    # Passo 1: Adicionar coluna
                    conn.execute(text(
                        'ALTER TABLE calculo_energia_solar '
                        'ADD COLUMN kit_id INTEGER'
                    ))
                    conn.commit()
                    print('✅ Coluna kit_id adicionada com sucesso!')
                    
                    # Passo 2: Adicionar Foreign Key (só funciona no PostgreSQL)
                    try:
                        conn.execute(text(
                            'ALTER TABLE calculo_energia_solar '
                            'ADD CONSTRAINT fk_calculo_energia_solar_kit '
                            'FOREIGN KEY (kit_id) REFERENCES kit_solar(id)'
                        ))
                        conn.commit()
                        print('✅ Foreign Key adicionada com sucesso!')
                    except Exception as fk_error:
                        print(f'⚠️ Não foi possível adicionar FK (normal no SQLite): {fk_error}')
                        
                except Exception as e:
                    print(f'⚠️ Erro ao adicionar coluna: {e}')
                    return False
            
            return True
            
        except Exception as e:
            print(f'❌ Erro: {e}')
            return False

def tentar_inferir_kit():
    """
    Tenta inferir qual kit cada projeto está usando baseado nas placas e inversores selecionados
    USANDO SQL DIRETO para evitar conflito com campos que não existem no banco
    """
    app = create_app()
    
    with app.app_context():
        try:
            print('\n🔍 Tentando inferir kit_id dos projetos...')
            
            # Primeiro, verificar quais colunas existem
            inspector = inspect(db.engine)
            columns = [col['name'] for col in inspector.get_columns('calculo_energia_solar')]
            
            if 'kit_id' not in columns:
                print('⚠️ Coluna kit_id não existe! Execute adicionar_coluna_kit_id() primeiro.')
                return False
            
            # Verificar se placa_id e inversor_id existem
            tem_placa_id = 'placa_id' in columns
            tem_inversor_id = 'inversor_id' in columns
            
            if not tem_placa_id or not tem_inversor_id:
                print(f'⚠️ Colunas necessárias não existem no banco:')
                print(f'  placa_id: {"✅" if tem_placa_id else "❌"}')
                print(f'  inversor_id: {"✅" if tem_inversor_id else "❌"}')
                print('⚠️ Não é possível inferir kit automaticamente.')
                return False
            
            # Usar SQL direto em vez de ORM
            with db.engine.connect() as conn:
                # Buscar projetos sem kit_id
                result = conn.execute(text(
                    'SELECT id, placa_id, inversor_id, kit_id '
                    'FROM calculo_energia_solar'
                ))
                projetos = result.fetchall()
                print(f'📊 Total de projetos: {len(projetos)}')
                
                for row in projetos:
                    projeto_id, placa_id, inversor_id, kit_id = row
                    
                    if kit_id:
                        print(f'  ⏭️ Projeto {projeto_id} já tem kit_id: {kit_id}')
                        continue
                    
                    # Tentar encontrar kit que combine com placa_id e inversor_id
                    if placa_id and inversor_id:
                        result_kit = conn.execute(text(
                            'SELECT id, fabricante, descricao '
                            'FROM kit_solar '
                            'WHERE placa_id = :placa_id AND inversor_id = :inversor_id '
                            'LIMIT 1'
                        ), {'placa_id': placa_id, 'inversor_id': inversor_id})
                        
                        kit_row = result_kit.fetchone()
                        
                        if kit_row:
                            kit_id_encontrado, fabricante, descricao = kit_row
                            # Atualizar projeto com kit_id
                            conn.execute(text(
                                'UPDATE calculo_energia_solar '
                                'SET kit_id = :kit_id '
                                'WHERE id = :projeto_id'
                            ), {'kit_id': kit_id_encontrado, 'projeto_id': projeto_id})
                            conn.commit()
                            print(f'  ✅ Projeto {projeto_id}: kit_id definido como {kit_id_encontrado} ({fabricante} - {descricao})')
                        else:
                            print(f'  ⚠️ Projeto {projeto_id}: nenhum kit encontrado para placa_id={placa_id} e inversor_id={inversor_id}')
                    else:
                        print(f'  ⚠️ Projeto {projeto_id}: sem placa_id ou inversor_id')
            
            print('\n✅ Inferência concluída!')
            return True
            
        except Exception as e:
            print(f'❌ Erro ao inferir kit: {e}')
            return False

def listar_colunas_tabela():
    """Lista as colunas que realmente existem na tabela"""
    app = create_app()
    
    with app.app_context():
        try:
            print('\n🔍 Listando colunas da tabela calculo_energia_solar...')
            
            inspector = inspect(db.engine)
            columns = [col['name'] for col in inspector.get_columns('calculo_energia_solar')]
            
            print(f'📊 Total de colunas: {len(columns)}')
            print(f'📋 Colunas disponíveis: {", ".join(columns[:10])}...')
            
            # Verificar colunas importantes
            colunas_importantes = ['kit_id', 'placa_id', 'inversor_id', 'nome_cliente']
            for col in colunas_importantes:
                status = '✅' if col in columns else '❌'
                print(f'  {status} {col}')
            
            return columns
            
        except Exception as e:
            print(f'❌ Erro ao listar colunas: {e}')
            return []

def verificar_projeto_6():
    """Verifica especificamente o projeto 6 USANDO SQL DIRETO e apenas colunas que existem"""
    app = create_app()
    
    with app.app_context():
        try:
            print('\n🔍 Verificando Projeto #6...')
            
            # Primeiro, descobrir quais colunas existem
            inspector = inspect(db.engine)
            columns = [col['name'] for col in inspector.get_columns('calculo_energia_solar')]
            
            # Montar query com apenas colunas que existem
            select_cols = ['id', 'nome_cliente']
            if 'kit_id' in columns:
                select_cols.append('kit_id')
            if 'placa_id' in columns:
                select_cols.append('placa_id')
            if 'inversor_id' in columns:
                select_cols.append('inversor_id')
            
            query = f"SELECT {', '.join(select_cols)} FROM calculo_energia_solar WHERE id = :projeto_id"
            
            # Usar SQL direto
            with db.engine.connect() as conn:
                result = conn.execute(text(query), {'projeto_id': 6})
                projeto = result.fetchone()
                
                if not projeto:
                    print('❌ Projeto 6 não encontrado!')
                    return
                
                print(f'\n📊 Dados do Projeto 6:')
                for i, col in enumerate(select_cols):
                    print(f'  {col}: {projeto[i]}')
                
                # Verificar kit_id se existir
                if 'kit_id' in columns:
                    kit_id_idx = select_cols.index('kit_id')
                    kit_id = projeto[kit_id_idx]
                    
                    if kit_id:
                        # Buscar dados do kit
                        result_kit = conn.execute(text(
                            'SELECT id, fabricante, descricao, preco '
                            'FROM kit_solar '
                            'WHERE id = :kit_id'
                        ), {'kit_id': kit_id})
                        
                        kit = result_kit.fetchone()
                        
                        if kit:
                            kit_id, fabricante, descricao, preco = kit
                            print(f'\n✅ KIT ENCONTRADO:')
                            print(f'  ID: {kit_id}')
                            print(f'  Fabricante: {fabricante}')
                            print(f'  Descrição: {descricao}')
                            print(f'  Preço: R$ {preco:,.2f}')
                    else:
                        print('\n⚠️ Projeto 6 não tem kit_id definido')
                else:
                    print('\n⚠️ Coluna kit_id não existe na tabela')
                        
        except Exception as e:
            print(f'❌ Erro ao verificar projeto 6: {e}')

if __name__ == '__main__':
    print('🚀 MIGRAÇÃO: Adicionar coluna kit_id e inferir kits\n')
    
    # Passo 0: Listar colunas existentes
    colunas = listar_colunas_tabela()
    
    # Passo 1: Adicionar coluna
    if adicionar_coluna_kit_id():
        # Passo 2: Tentar inferir kits (só se placa_id e inversor_id existirem)
        tentar_inferir_kit()
        
        # Passo 3: Verificar projeto 6
        verificar_projeto_6()
    else:
        print('❌ Falha ao adicionar coluna kit_id')
