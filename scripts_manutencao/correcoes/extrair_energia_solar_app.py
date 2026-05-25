"""
Script para extrair o módulo de Energia Solar em um app Flask independente.

Este script cria uma cópia completa do módulo energia_solar + dependências mínimas
para funcionar como um sistema standalone de gestão de energia solar.

O ERP JSP original NÃO será modificado.
"""
import os
import shutil
from pathlib import Path

# Diretório de destino (paralelo ao ERP JSP)
DESTINO_BASE = Path(__file__).parent.parent / "JSP-Energia-Solar"

print("🚀 EXTRAÇÃO DO MÓDULO ENERGIA SOLAR")
print("=" * 60)
print(f"📁 Destino: {DESTINO_BASE}")
print(f"📂 Fonte: {Path(__file__).parent}")
print()

# Criar estrutura de diretórios
estrutura = {
    "app": ["energia_solar", "cliente", "auth", "templates", "static"],
    "app/energia_solar": ["templates", "services"],
    "app/energia_solar/templates": ["energia_solar"],
    "app/cliente": ["templates"],
    "app/cliente/templates": ["cliente"],
    "app/auth": ["templates"],
    "app/auth/templates": ["auth"],
    "app/templates": [],
    "app/static": ["css", "js", "img", "uploads"],
    "database": [],
    "scripts": [],
}

print("📦 Criando estrutura de diretórios...")
for pasta, subpastas in estrutura.items():
    pasta_completa = DESTINO_BASE / pasta
    pasta_completa.mkdir(parents=True, exist_ok=True)
    print(f"  ✅ {pasta}/")
    
    for sub in subpastas:
        sub_completa = pasta_completa / sub
        sub_completa.mkdir(parents=True, exist_ok=True)
        print(f"     ✅ {pasta}/{sub}/")

print()
print("📄 Copiando arquivos do módulo Energia Solar...")

# Arquivos principais do módulo energia_solar
arquivos_energia_solar = [
    "app/energia_solar/__init__.py",
    "app/energia_solar/energia_solar_model.py",
    "app/energia_solar/energia_solar_routes.py",
    "app/energia_solar/catalogo_model.py",
    "app/energia_solar/custo_fixo_model.py",
    "app/energia_solar/word_utils.py",
    "app/energia_solar/proposta_word_service.py",
]

fonte_base = Path(__file__).parent

for arquivo in arquivos_energia_solar:
    fonte = fonte_base / arquivo
    destino = DESTINO_BASE / arquivo
    if fonte.exists():
        shutil.copy2(fonte, destino)
        print(f"  ✅ {arquivo}")
    else:
        print(f"  ⚠️  {arquivo} (não encontrado)")

print()
print("📄 Copiando templates do módulo Energia Solar...")

# Templates energia_solar
pasta_templates = fonte_base / "app/energia_solar/templates/energia_solar"
if pasta_templates.exists():
    destino_templates = DESTINO_BASE / "app/energia_solar/templates/energia_solar"
    shutil.copytree(pasta_templates, destino_templates, dirs_exist_ok=True)
    total = len(list(destino_templates.glob("*.html")))
    print(f"  ✅ Copiados {total} templates HTML")

print()
print("📄 Copiando módulo Cliente (simplificado)...")

# Módulo cliente (apenas necessário para energia solar)
arquivos_cliente = [
    "app/cliente/__init__.py",
    "app/cliente/cliente_model.py",
    "app/cliente/cliente_routes.py",
]

for arquivo in arquivos_cliente:
    fonte = fonte_base / arquivo
    destino = DESTINO_BASE / arquivo
    if fonte.exists():
        shutil.copy2(fonte, destino)
        print(f"  ✅ {arquivo}")

# Templates cliente
pasta_templates_cliente = fonte_base / "app/cliente/templates/cliente"
if pasta_templates_cliente.exists():
    destino_templates_cliente = DESTINO_BASE / "app/cliente/templates/cliente"
    shutil.copytree(pasta_templates_cliente, destino_templates_cliente, dirs_exist_ok=True)
    total = len(list(destino_templates_cliente.glob("*.html")))
    print(f"  ✅ Copiados {total} templates de cliente")

print()
print("📄 Copiando módulo Auth (login)...")

# Módulo auth
arquivos_auth = [
    "app/auth/__init__.py",
    "app/auth/auth_model.py",
    "app/auth/auth_routes.py",
]

for arquivo in arquivos_auth:
    fonte = fonte_base / arquivo
    destino = DESTINO_BASE / arquivo
    if fonte.exists():
        shutil.copy2(fonte, destino)
        print(f"  ✅ {arquivo}")

# Templates auth
pasta_templates_auth = fonte_base / "app/auth/templates/auth"
if pasta_templates_auth.exists():
    destino_templates_auth = DESTINO_BASE / "app/auth/templates/auth"
    shutil.copytree(pasta_templates_auth, destino_templates_auth, dirs_exist_ok=True)
    total = len(list(destino_templates_auth.glob("*.html")))
    print(f"  ✅ Copiados {total} templates de autenticação")

print()
print("📄 Copiando arquivos base da aplicação...")

# Arquivos principais do app
arquivos_base_app = [
    "app/__init__.py",
    "app/extensoes.py",
    "app/config.py",
]

for arquivo in arquivos_base_app:
    fonte = fonte_base / arquivo
    destino = DESTINO_BASE / arquivo
    if fonte.exists():
        shutil.copy2(fonte, destino)
        print(f"  ✅ {arquivo}")

print()
print("📄 Copiando templates base...")

# Templates base
templates_base = [
    "app/templates/base.html",
    "app/templates/navbar.html",
    "app/templates/index.html",
]

for template in templates_base:
    fonte = fonte_base / template
    destino = DESTINO_BASE / template
    if fonte.exists():
        shutil.copy2(fonte, destino)
        print(f"  ✅ {template}")

print()
print("📄 Copiando arquivos estáticos (CSS, JS, imagens)...")

# Static files
pastas_static = ["css", "js", "img"]
for pasta in pastas_static:
    fonte_static = fonte_base / "app/static" / pasta
    destino_static = DESTINO_BASE / "app/static" / pasta
    if fonte_static.exists():
        shutil.copytree(fonte_static, destino_static, dirs_exist_ok=True)
        total = len(list(destino_static.rglob("*")))
        print(f"  ✅ {pasta}/ ({total} arquivos)")

print()
print("📄 Criando arquivos de configuração do novo app...")

# Criar run.py
run_py = """\"\"\"
JSP Energia Solar - Sistema de Gestão de Energia Solar

Aplicação Flask standalone extraída do ERP JSP.
Foco em gestão de projetos de energia solar fotovoltaica.
\"\"\"
from app import criar_app
from app.extensoes import db
import os

app = criar_app()

if __name__ == '__main__':
    with app.app_context():
        # Criar tabelas do banco de dados
        db.create_all()
        print("✅ Banco de dados inicializado!")
    
    # Rodar aplicação
    port = int(os.environ.get('PORT', 5001))  # Porta 5001 para não conflitar com ERP JSP
    app.run(
        host='0.0.0.0',
        port=port,
        debug=True
    )
"""

(DESTINO_BASE / "run.py").write_text(run_py, encoding='utf-8')
print("  ✅ run.py")

# Criar requirements.txt
requirements = """Flask==3.0.0
Flask-Login==0.6.3
Flask-SQLAlchemy==3.1.1
python-dotenv==1.0.0
WeasyPrint==60.1
python-docx==1.1.0
Werkzeug==3.0.1
psycopg2-binary==2.9.9
gunicorn==21.2.0
"""

(DESTINO_BASE / "requirements.txt").write_text(requirements, encoding='utf-8')
print("  ✅ requirements.txt")

# Criar .env de exemplo
env_exemplo = """# Configurações do JSP Energia Solar
FLASK_APP=run.py
FLASK_ENV=development
SECRET_KEY=sua-chave-secreta-aqui-12345

# Banco de Dados (SQLite local)
DATABASE_URL=sqlite:///database/energia_solar.db

# Para PostgreSQL no Render:
# DATABASE_URL=postgresql://usuario:senha@host:5432/database

# Configurações opcionais
DEBUG=True
"""

(DESTINO_BASE / ".env.example").write_text(env_exemplo, encoding='utf-8')
print("  ✅ .env.example")

# Criar .gitignore
gitignore = """# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
venv/
.venv/
ENV/

# Flask
instance/
.webassets-cache

# Database
*.db
*.sqlite
*.sqlite3
database/*.db

# IDE
.vscode/
.idea/
*.swp
*.swo

# Environment
.env

# Uploads
app/static/uploads/

# Logs
*.log
"""

(DESTINO_BASE / ".gitignore").write_text(gitignore, encoding='utf-8')
print("  ✅ .gitignore")

# Criar README.md
readme = """# 🌞 JSP Energia Solar

Sistema de gestão de projetos de energia solar fotovoltaica.

Aplicação Flask standalone extraída do ERP JSP, focada em dimensionamento,
orçamento e documentação de sistemas de energia solar.

## 🚀 Funcionalidades

- ✅ Cadastro de clientes
- ✅ Catálogo de equipamentos (placas, inversores, kits)
- ✅ Dimensionamento de sistemas fotovoltaicos
- ✅ Cálculo automático de economia e payback
- ✅ Geração de propostas comerciais (PDF e Word)
- ✅ Dashboard de projetos com KPIs
- ✅ Gestão de orçamentos e financiamentos
- ✅ Múltiplos templates de documentos

## 📦 Instalação

### 1. Clonar/Baixar o repositório

### 2. Criar ambiente virtual
```bash
python -m venv .venv
.venv\\Scripts\\activate  # Windows
source .venv/bin/activate  # Linux/Mac
```

### 3. Instalar dependências
```bash
pip install -r requirements.txt
```

### 4. Configurar variáveis de ambiente
```bash
copy .env.example .env
# Editar .env com suas configurações
```

### 5. Rodar a aplicação
```bash
python run.py
```

Acesse: http://localhost:5001

## 🔐 Login Padrão

Na primeira execução, o sistema cria um usuário administrador:
- **Usuário:** admin
- **Senha:** admin123

⚠️ **Altere a senha após o primeiro login!**

## 📊 Estrutura do Projeto

```
JSP-Energia-Solar/
├── app/
│   ├── energia_solar/     # Módulo principal
│   ├── cliente/           # Gestão de clientes
│   ├── auth/              # Autenticação
│   ├── templates/         # Templates HTML
│   └── static/            # CSS, JS, imagens
├── database/              # Banco de dados SQLite
├── run.py                 # Ponto de entrada
└── requirements.txt       # Dependências Python
```

## 🌐 Deploy no Render

1. Criar conta no [Render](https://render.com)
2. Conectar ao repositório Git
3. Configurar Web Service:
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `gunicorn run:app`
4. Adicionar variáveis de ambiente no painel do Render

## 📝 Licença

Desenvolvido por JSP Energia Solar © 2024

---

Para suporte, entre em contato com a equipe JSP.
"""

(DESTINO_BASE / "README.md").write_text(readme, encoding='utf-8')
print("  ✅ README.md")

# Criar script de criação do banco
script_criar_banco = """\"\"\"
Script para criar o banco de dados e usuário admin inicial
\"\"\"
from app import criar_app
from app.extensoes import db
from app.auth.auth_model import User
from werkzeug.security import generate_password_hash

app = criar_app()

with app.app_context():
    print("🔨 Criando tabelas do banco de dados...")
    db.create_all()
    print("✅ Tabelas criadas!")
    
    # Verificar se já existe usuário admin
    admin = User.query.filter_by(username='admin').first()
    
    if not admin:
        print("\\n👤 Criando usuário administrador...")
        admin = User(
            username='admin',
            email='admin@jspsolar.com.br',
            password_hash=generate_password_hash('admin123'),
            tipo='ADMIN',
            ativo=True
        )
        db.session.add(admin)
        db.session.commit()
        print("✅ Usuário 'admin' criado com senha 'admin123'")
        print("⚠️  IMPORTANTE: Altere a senha após o primeiro login!")
    else:
        print("\\n✅ Usuário admin já existe")
    
    print("\\n🎉 Sistema pronto para uso!")
    print("   Execute: python run.py")
"""

(DESTINO_BASE / "scripts" / "criar_banco.py").write_text(script_criar_banco, encoding='utf-8')
print("  ✅ scripts/criar_banco.py")

print()
print("=" * 60)
print("✅ EXTRAÇÃO CONCLUÍDA COM SUCESSO!")
print("=" * 60)
print()
print(f"📁 App criado em: {DESTINO_BASE}")
print()
print("🚀 PRÓXIMOS PASSOS:")
print()
print("1️⃣  Navegar até a pasta do novo app:")
print(f"    cd {DESTINO_BASE}")
print()
print("2️⃣  Criar ambiente virtual:")
print("    python -m venv .venv")
print("    .venv\\Scripts\\activate")
print()
print("3️⃣  Instalar dependências:")
print("    pip install -r requirements.txt")
print()
print("4️⃣  Criar banco de dados:")
print("    python scripts/criar_banco.py")
print()
print("5️⃣  Rodar aplicação:")
print("    python run.py")
print()
print("6️⃣  Acessar no navegador:")
print("    http://localhost:5001")
print()
print("=" * 60)
print("📝 Login inicial: admin / admin123")
print("=" * 60)
print()
print("✅ O ERP JSP original continua funcionando normalmente!")
print("✅ Agora você tem 2 apps independentes:")
print("   - ERP JSP (completo): http://localhost:5000")
print("   - JSP Energia Solar: http://localhost:5001")
