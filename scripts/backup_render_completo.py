"""
Backup Completo do Banco Render
Exporta todas as tabelas para JSON antes de qualquer alteração
"""
import os
import sys
import json
from datetime import datetime

# Adicionar o diretório raiz ao path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker

# URL do banco Render (usar a mesma do .env ou direto)
RENDER_DB_URL = os.environ.get('DATABASE_URL') or input("Cole a URL do banco Render: ")

# Se for render.com, pode vir como postgres:// e precisa ser postgresql://
if RENDER_DB_URL.startswith('postgres://'):
    RENDER_DB_URL = RENDER_DB_URL.replace('postgres://', 'postgresql://', 1)

def fazer_backup():
    """Exporta todas as tabelas do Render para JSON"""
    
    print("🔄 Conectando ao banco Render...")
    engine = create_engine(RENDER_DB_URL)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    # Criar pasta de backups
    backup_dir = os.path.join(os.path.dirname(__file__), '..', 'backups')
    os.makedirs(backup_dir, exist_ok=True)
    
    # Nome do arquivo com timestamp
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_file = os.path.join(backup_dir, f'backup_render_{timestamp}.json')
    
    # Inspecionar todas as tabelas
    inspector = inspect(engine)
    tabelas = inspector.get_table_names()
    
    print(f"\n📋 Encontradas {len(tabelas)} tabelas:")
    for t in tabelas:
        print(f"   - {t}")
    
    backup_data = {
        'timestamp': timestamp,
        'database_url': RENDER_DB_URL.split('@')[1] if '@' in RENDER_DB_URL else 'render',
        'tabelas': {}
    }
    
    print(f"\n💾 Fazendo backup...")
    
    # Exportar cada tabela
    for tabela in tabelas:
        try:
            result = session.execute(text(f'SELECT * FROM "{tabela}"'))
            colunas = result.keys()
            rows = result.fetchall()
            
            # Converter para lista de dicionários
            dados = []
            for row in rows:
                row_dict = {}
                for i, col in enumerate(colunas):
                    valor = row[i]
                    # Converter tipos não serializáveis
                    if hasattr(valor, 'isoformat'):  # datetime/date
                        valor = valor.isoformat()
                    elif isinstance(valor, bytes):
                        valor = valor.decode('utf-8', errors='ignore')
                    row_dict[col] = valor
                dados.append(row_dict)
            
            backup_data['tabelas'][tabela] = {
                'total_registros': len(dados),
                'colunas': list(colunas),
                'dados': dados
            }
            
            print(f"   ✅ {tabela}: {len(dados)} registros")
            
        except Exception as e:
            print(f"   ⚠️  {tabela}: Erro - {e}")
            backup_data['tabelas'][tabela] = {
                'erro': str(e)
            }
    
    # Salvar JSON
    with open(backup_file, 'w', encoding='utf-8') as f:
        json.dump(backup_data, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ Backup concluído!")
    print(f"📁 Arquivo: {backup_file}")
    print(f"📊 Total: {len(tabelas)} tabelas")
    
    # Resumo
    total_registros = sum(
        t.get('total_registros', 0) 
        for t in backup_data['tabelas'].values() 
        if 'total_registros' in t
    )
    print(f"📈 Total de registros: {total_registros}")
    
    session.close()
    return backup_file

if __name__ == '__main__':
    try:
        backup_file = fazer_backup()
        print(f"\n✅ Backup salvo com sucesso em:\n{backup_file}")
    except Exception as e:
        print(f"\n❌ Erro ao fazer backup: {e}")
        import traceback
        traceback.print_exc()
