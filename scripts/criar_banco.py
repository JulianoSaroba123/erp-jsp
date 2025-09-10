"""Script de criação do banco de dados SQLite para o ERP JSP
Uso: python scripts/criar_banco.py
"""

import sys
import os

# Adiciona a raiz do projeto ao sys.path para permitir imports locais
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from flask import Flask
from aplicacao.extensoes import db

# Caminhos absolutos
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
DB_DIR = os.path.join(BASE_DIR, 'database')
DB_PATH = os.path.join(DB_DIR, 'database.db')

from pathlib import Path
db_posix = Path(DB_PATH).as_posix()

# Garante que a pasta exista e cria arquivo vazio se necessário
os.makedirs(DB_DIR, exist_ok=True)
open(DB_PATH, 'a').close()

# Cria um app temporário para garantir que o DB URI correto seja usado
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{db_posix}"
app.config.setdefault('SQLALCHEMY_TRACK_MODIFICATIONS', False)

with app.app_context():
    # Inicializa a extensão com o app que tem a config correta
    db.init_app(app)
    print('Criando tabelas no banco:', DB_PATH)
    try:
        # Importar modelos para que sejam registrados no metadata do SQLAlchemy
        try:
            from aplicacao.cliente import cliente_model  # noqa: F401
        except Exception:
            # Se não houver módulo cliente, continue; outros módulos podem existir
            pass
        db.create_all()
        print('✅ Banco de dados criado com sucesso:', DB_PATH)
    except Exception as e:
        print('Erro ao criar tabelas:', type(e).__name__, e)
        raise

# Mostra tamanho do arquivo criado (se existir)
if os.path.exists(DB_PATH):
    print('Arquivo do DB criado em:', DB_PATH)
    print('Tamanho (bytes):', os.path.getsize(DB_PATH))
else:
    print('Arquivo do DB não foi criado automaticamente; verifique permissões e configurações.')
