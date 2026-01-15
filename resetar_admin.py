from app import create_app
from app.extensoes import db
from app.auth.auth_model import Usuario
from werkzeug.security import generate_password_hash

app = create_app()

with app.app_context():
    # Verificar se há usuários
    usuarios = Usuario.query.all()
    print(f"Total de usuários: {len(usuarios)}")
    
    if usuarios:
        for u in usuarios:
            print(f"- {u.username} (ID: {u.id}, Ativo: {u.ativo})")
    
    # Resetar senha do admin
    admin = Usuario.query.filter_by(username='admin').first()
    
    if admin:
        admin.senha_hash = generate_password_hash('admin')
        admin.ativo = True
        db.session.commit()
        print("\n✅ Senha do admin resetada para: admin")
    else:
        # Criar admin
        novo_admin = Usuario(
            username='admin',
            email='admin@jsp.com',
            nome_completo='Administrador',
            senha_hash=generate_password_hash('admin'),
            ativo=True,
            is_admin=True
        )
        db.session.add(novo_admin)
        db.session.commit()
        print("\n✅ Usuário admin criado!")
        print("Login: admin")
        print("Senha: admin")
