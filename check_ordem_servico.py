from aplicacao import create_app
from aplicacao.extensoes import db
from sqlalchemy import text

app = create_app()
app.app_context().push()

# Verificar tabelas que contém "ordem"
result = db.session.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE '%ordem%'"))
print("Tabelas relacionadas a ordem:")
for row in result:
    print(f"  {row[0]}")

# Verificar se conseguimos importar o modelo
try:
    from aplicacao.ordem_servico.ordem_servico_model import OrdemServico
    print(f"\nModelo OrdemServico carregado com sucesso!")
    print(f"Tabela: {OrdemServico.__tablename__}")
    
    # Tentar contar registros
    count = OrdemServico.query.count()
    print(f"Número de ordens de serviço: {count}")
    
except Exception as e:
    print(f"\nErro ao carregar modelo OrdemServico: {e}")