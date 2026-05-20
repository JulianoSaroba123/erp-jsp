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
from app.energia_solar.energia_solar_model import CalculoEnergiaSolar
from app.energia_solar.catalogo_model import KitSolar
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
    """
    app = create_app()
    
    with app.app_context():
        try:
            print('\n🔍 Tentando inferir kit_id dos projetos...')
            
            # Buscar todos os projetos
            projetos = CalculoEnergiaSolar.query.all()
            print(f'📊 Total de projetos: {len(projetos)}')
            
            for projeto in projetos:
                if projeto.kit_id:
                    print(f'  ⏭️ Projeto {projeto.id} já tem kit_id: {projeto.kit_id}')
                    continue
                
                # Tentar encontrar kit que combine com placa_id e inversor_id
                if projeto.placa_id and projeto.inversor_id:
                    kit = KitSolar.query.filter_by(
                        placa_id=projeto.placa_id,
                        inversor_id=projeto.inversor_id
                    ).first()
                    
                    if kit:
                        projeto.kit_id = kit.id
                        print(f'  ✅ Projeto {projeto.id}: kit_id definido como {kit.id} ({kit.fabricante} - {kit.descricao})')
                    else:
                        print(f'  ⚠️ Projeto {projeto.id}: nenhum kit encontrado para placa_id={projeto.placa_id} e inversor_id={projeto.inversor_id}')
                else:
                    print(f'  ⚠️ Projeto {projeto.id}: sem placa_id ou inversor_id')
            
            db.session.commit()
            print('\n✅ Inferência concluída!')
            return True
            
        except Exception as e:
            db.session.rollback()
            print(f'❌ Erro ao inferir kit: {e}')
            return False

def verificar_projeto_6():
    """Verifica especificamente o projeto 6"""
    app = create_app()
    
    with app.app_context():
        try:
            print('\n🔍 Verificando Projeto #6...')
            projeto = CalculoEnergiaSolar.query.get(6)
            
            if not projeto:
                print('❌ Projeto 6 não encontrado!')
                return
            
            print(f'\n📊 Dados do Projeto 6:')
            print(f'  ID: {projeto.id}')
            print(f'  Nome Cliente: {projeto.nome_cliente}')
            print(f'  kit_id: {projeto.kit_id}')
            print(f'  placa_id: {projeto.placa_id}')
            print(f'  inversor_id: {projeto.inversor_id}')
            
            if projeto.kit_id:
                kit = KitSolar.query.get(projeto.kit_id)
                if kit:
                    print(f'\n✅ KIT ENCONTRADO:')
                    print(f'  ID: {kit.id}')
                    print(f'  Fabricante: {kit.fabricante}')
                    print(f'  Descrição: {kit.descricao}')
                    print(f'  Preço: R$ {kit.preco:,.2f}')
                    print(f'  nome_exibicao: {kit.nome_exibicao}')
                    print(f'  valor_orcamento: {kit.valor_orcamento}')
            else:
                print('\n⚠️ Projeto 6 não tem kit_id definido')
                
                # Verificar se existem kits compatíveis
                if projeto.placa_id and projeto.inversor_id:
                    kits = KitSolar.query.filter_by(
                        placa_id=projeto.placa_id,
                        inversor_id=projeto.inversor_id
                    ).all()
                    
                    if kits:
                        print(f'\n💡 Kits compatíveis encontrados: {len(kits)}')
                        for kit in kits:
                            print(f'  - Kit {kit.id}: {kit.fabricante} - {kit.descricao} (R$ {kit.preco:,.2f})')
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
