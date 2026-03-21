# 🔧 MIGRAÇÃO: Adicionar intervalo_almoco no Render

## ✅ Método 1: Python Interativo (RECOMENDADO)

No Render Shell, execute linha por linha:

```python
# Entrar no Python
python

# Executar migração
from sqlalchemy import create_engine, text
import os

DATABASE_URL = os.getenv('DATABASE_URL')
if DATABASE_URL.startswith('postgres://'):
    DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)

engine = create_engine(DATABASE_URL)

with engine.connect() as conn:
    # Verificar se já existe
    result = conn.execute(text("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name='ordem_servico' AND column_name='intervalo_almoco'
    """))
    
    if result.fetchone():
        print("✅ Coluna intervalo_almoco já existe!")
    else:
        # Adicionar coluna
        conn.execute(text("""
            ALTER TABLE ordem_servico 
            ADD COLUMN intervalo_almoco INTEGER DEFAULT 60
        """))
        conn.commit()
        print("✅ Coluna intervalo_almoco adicionada com sucesso!")

exit()
```

---

## ⚡ Método 2: Script direto (se conseguir copiar arquivo)

Se conseguir fazer upload do arquivo, executar:

```bash
cd /opt/render/project/src
python adicionar_intervalo_almoco.py
```

---

## 🔍 Verificar se funcionou

```python
python

from app.app import app, db
from app.ordem_servico.ordem_servico_model import OrdemServico

with app.app_context():
    # Verificar estrutura da tabela
    from sqlalchemy import inspect
    inspector = inspect(db.engine)
    colunas = [c['name'] for c in inspector.get_columns('ordem_servico')]
    print("Colunas:", colunas)
    print("intervalo_almoco presente:", 'intervalo_almoco' in colunas)

exit()
```

---

## ✅ Após migração bem-sucedida

No Render Dashboard:
1. **Deploy Manual** para aplicar o código novo
2. Verificar se o campo aparece no formulário
3. Testar criação de OS com intervalo de almoço
4. Gerar PDF para ver colaboradores detalhados
