"""
Script para criar colaboradores de exemplo para testes.
"""
import os
import sys

# Adicionar diretório ao path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app.app import app
from app.extensoes import db
from app.colaborador.colaborador_model import Colaborador
from decimal import Decimal

def criar_colaboradores():
    with app.app_context():
        try:
            # Verificar colaboradores existentes
            colaboradores_existentes = Colaborador.query.filter_by(ativo=True).all()
            
            if colaboradores_existentes:
                print(f'⚠️  {len(colaboradores_existentes)} colaborador(es) já cadastrado(s):')
                for c in colaboradores_existentes:
                    print(f'   - {c.nome} ({c.cargo}) - R$ {c.valor_hora}/hora')
                print()
            
            # Lista de colaboradores para criar
            colaboradores_exemplo = [
                {
                    'nome': 'João Silva',
                    'cpf': '111.222.333-44',
                    'cargo': 'Técnico em Manutenção',
                    'celular': '(11) 98765-4321',
                    'especialidade': 'Manutenção Elétrica',
                    'valor_hora': Decimal('50.00')
                },
                {
                    'nome': 'Maria Santos',
                    'cpf': '222.333.444-55',
                    'cargo': 'Engenheira',
                    'celular': '(11) 97654-3210',
                    'especialidade': 'Energia Solar',
                    'valor_hora': Decimal('80.00')
                },
                {
                    'nome': 'Pedro Oliveira',
                    'cpf': '333.444.555-66',
                    'cargo': 'Eletricista',
                    'celular': '(11) 96543-2109',
                    'especialidade': 'Instalações Elétricas',
                    'valor_hora': Decimal('45.00')
                },
                {
                    'nome': 'Ana Costa',
                    'cpf': '444.555.666-77',
                    'cargo': 'Auxiliar Técnico',
                    'celular': '(11) 95432-1098',
                    'especialidade': 'Suporte Técnico',
                    'valor_hora': Decimal('35.00')
                }
            ]
            
            criados = 0
            for dados in colaboradores_exemplo:
                # Verificar se já existe pelo CPF
                existe = Colaborador.query.filter_by(cpf=dados['cpf']).first()
                if not existe:
                    colaborador = Colaborador(
                        nome=dados['nome'],
                        cpf=dados['cpf'],
                        cargo=dados['cargo'],
                        celular=dados['celular'],
                        especialidade=dados['especialidade'],
                        valor_hora=dados['valor_hora'],
                        ativo=True
                    )
                    db.session.add(colaborador)
                    criados += 1
                    print(f'✅ Colaborador criado: {dados["nome"]} - {dados["cargo"]}')
                else:
                    print(f'⏭️  Já existe: {dados["nome"]}')
            
            if criados > 0:
                db.session.commit()
                print(f'\n🎉 {criados} colaborador(es) criado(s) com sucesso!')
            else:
                print('\n✅ Todos os colaboradores de exemplo já existem!')
            
            # Listar todos
            print('\n' + '='*60)
            print('📋 COLABORADORES CADASTRADOS:')
            print('='*60)
            todos = Colaborador.query.filter_by(ativo=True).all()
            for c in todos:
                print(f'ID: {c.id} | {c.nome} ({c.cargo}) | R$ {c.valor_hora}/hora')
            print('='*60)
            
        except Exception as e:
            print(f'❌ Erro ao criar colaboradores: {e}')
            import traceback
            traceback.print_exc()

if __name__ == '__main__':
    criar_colaboradores()
