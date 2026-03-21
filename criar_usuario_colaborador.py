"""
Script para criar usuário do tipo colaborador para testes.
"""
import os
import sys

# Adicionar diretório ao path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app.app import app
from app.extensoes import db
from app.auth.usuario_model import Usuario
from werkzeug.security import generate_password_hash

def criar_colaborador():
    with app.app_context():
        try:
            # Verificar se já existe
            colaborador = Usuario.query.filter_by(usuario='colaborador').first()
            
            if colaborador:
                print('⚠️  Usuário colaborador já existe!')
                print(f'   Nome: {colaborador.nome}')
                print(f'   Tipo: {colaborador.tipo_usuario}')
                
                # Atualizar tipo se necessário
                if colaborador.tipo_usuario != 'colaborador':
                    colaborador.tipo_usuario = 'colaborador'
                    db.session.commit()
                    print('✅ Tipo atualizado para "colaborador"')
            else:
                # Criar novo usuário colaborador
                novo_colaborador = Usuario(
                    usuario='colaborador',
                    senha_hash=generate_password_hash('123456'),
                    nome='João Silva',
                    email='colaborador@jsp.com',
                    tipo_usuario='colaborador',
                    cargo='Técnico de Campo',
                    departamento='Operacional',
                    ativo=True,
                    email_confirmado=True,
                    primeiro_login=False
                )
                
                db.session.add(novo_colaborador)
                db.session.commit()
                
                print('✅ Usuário colaborador criado com sucesso!')
            
            print('\n' + '='*50)
            print('📋 CREDENCIAIS PARA LOGIN:')
            print('='*50)
            print('👤 Usuário: colaborador')
            print('🔑 Senha: 123456')
            print('🔧 Tipo: Colaborador (apenas OS operacionais)')
            print('='*50)
            
        except Exception as e:
            print(f'❌ Erro ao criar colaborador: {e}')
            import traceback
            traceback.print_exc()

if __name__ == '__main__':
    criar_colaborador()
