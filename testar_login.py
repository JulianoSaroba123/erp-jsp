from app import create_app
from app.auth.auth_model import Usuario

app = create_app()

with app.app_context():
    # Teste o usuário admin
    admin = Usuario.query.filter_by(username='admin').first()
    
    if admin:
        print(f"✅ Usuário encontrado: {admin.username}")
        print(f"   ID: {admin.id}")
        print(f"   Email: {admin.email}")
        print(f"   Ativo: {admin.ativo}")
        print(f"   Bloqueado: {admin.esta_bloqueado if hasattr(admin, 'esta_bloqueado') else 'N/A'}")
        print(f"   Pode fazer login: {admin.pode_fazer_login if hasattr(admin, 'pode_fazer_login') else 'N/A'}")
        
        # Testar senha
        senha_correta = admin.verificar_senha('admin')
        print(f"   Senha 'admin' correta: {senha_correta}")
        
        # Verificar métodos necessários para Flask-Login
        print(f"\n   Métodos Flask-Login:")
        print(f"   - is_authenticated: {admin.is_authenticated if hasattr(admin, 'is_authenticated') else 'MISSING'}")
        print(f"   - is_active: {admin.is_active if hasattr(admin, 'is_active') else 'MISSING'}")
        print(f"   - is_anonymous: {admin.is_anonymous if hasattr(admin, 'is_anonymous') else 'MISSING'}")
        print(f"   - get_id(): {admin.get_id() if hasattr(admin, 'get_id') else 'MISSING'}")
    else:
        print("❌ Usuário admin não encontrado!")
