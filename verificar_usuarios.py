#!/usr/bin/env python3
"""
Script para verificar usuários no banco
"""
from aplicacao import create_app
from aplicacao.autenticacao.models import Usuario

def verificar_usuarios():
    app = create_app()
    
    with app.app_context():
        usuarios = Usuario.query.all()
        print(f"Total de usuários encontrados: {len(usuarios)}")
        
        for usuario in usuarios:
            print(f"ID: {usuario.id}, Username: {usuario.username}, Nome: {usuario.nome}")

if __name__ == "__main__":
    verificar_usuarios()