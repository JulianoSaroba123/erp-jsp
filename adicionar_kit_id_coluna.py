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

def verificar_projeto_6():
    """Verifica especificamente o projeto 6 USANDO SQL DIRETO"""
    app = create_app()
    
    with app.app_context():
        try:
            print('\n🔍 Verificando Projeto #6...')
            
            # Usar SQL direto
            with db.engine.connect() as conn:
                # Buscar projeto 6
                result = conn.execute(text(
                    'SELECT id, nome_cliente, kit_id, placa_id, inversor_id '
                    'FROM calculo_energia_solar '
                    'WHERE id = :projeto_id'
                ), {'projeto_id': 6})
                
                projeto = result.fetchone()
                
                if not projeto:
                    print('❌ Projeto 6 não encontrado!')
                    return
                
                projeto_id, nome_cliente, kit_id, placa_id, inversor_id = projeto
                
                print(f'\n📊 Dados do Projeto 6:')
                print(f'  ID: {projeto_id}')
                print(f'  Nome Cliente: {nome_cliente}')
                print(f'  kit_id: {kit_id}')
                print(f'  placa_id: {placa_id}')
                print(f'  inversor_id: {inversor_id}')
                
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
                        print(f'  nome_exibicao: {fabricante} - {descricao}')
                        print(f'  valor_orcamento: {preco}')
                else:
                    print('\n⚠️ Projeto 6 não tem kit_id definido')
                    
                    # Verificar se existem kits compatíveis
                    if placa_id and inversor_id:
                        result_kits = conn.execute(text(
                            'SELECT id, fabricante, descricao, preco '
                            'FROM kit_solar '
                            'WHERE placa_id = :placa_id AND inversor_id = :inversor_id'
                        ), {'placa_id': placa_id, 'inversor_id': inversor_id})
                        
                        kits = result_kits.fetchall()
                        
                        if kits:
                            print(f'\n💡 Kits compatíveis encontrados: {len(kits)}')
                            for kit in kits:
                                kit_id, fabricante, descricao, preco = kit
                                print(f'  - Kit {kit_id}: {fabricante} - {descricao} (R$ {preco:,.2f})')
                        else:
                            print('\n❌ Nenhum kit compatível encontrado')
                        
        except Exception as e:
            print(f'❌ Erro ao verificar projeto 6: {e}')

if __name__ == '__main__':
    print('🚀 MIGRAÇÃO: Adicionar coluna kit_id e inferir kits\n')
    
    # Passo 1: Adicionar coluna
    if adicionar_coluna_kit_id():
        # Passo 2: Tentar inferir kits
        tentar_inferir_kit()
        
        # Passo 3: Verificar projeto 6
        verificar_projeto_6()
    else:
        print('❌ Falha ao adicionar coluna kit_id')
