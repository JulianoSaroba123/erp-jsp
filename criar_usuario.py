#!/usr/bin/env python3
"""
Script para criar usuário padrão
"""
from aplicacao import create_app
from aplicacao.autenticacao.models import Usuario
from aplicacao.extensoes import db
from werkzeug.security import generate_password_hash

def criar_usuario():
    app = create_app()
    
    with app.app_context():
        # Verificar se já existe um usuário julia
        usuario_existente = Usuario.query.filter_by(username='julia').first()
        
        if usuario_existente:
            print("Usuário 'julia' já existe!")
            return
        
        # Criar usuário
        novo_usuario = Usuario(
            username='julia',
            senha_hash=generate_password_hash('1234'),
            nome='Julia',
            email='julia@example.com'
        )
        
        db.session.add(novo_usuario)
        db.session.commit()
        
        print("Usuário 'julia' criado com sucesso!")
        print("Username: julia")
        print("Senha: 1234")

if __name__ == "__main__":
    criar_usuario()