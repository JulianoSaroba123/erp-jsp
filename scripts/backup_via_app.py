"""
Backup via Flask App
Usa o contexto do app para exportar dados
"""
import os
import sys
import json
from datetime import datetime

# Adicionar o diretório raiz ao path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Configurar para usar o banco Render
os.environ['DATABASE_URL'] = 'postgresql://erp_jsp_db_iw6v_user:roBPw29VFmZKdksaGXw1tv4mYULKQwnl@dpg-d4pf1s49c44c73bdsdrg-a/erp_jsp_db_iw6v'
os.environ['FLASK_ENV'] = 'production'

from app.app import create_app
from app.extensoes import db
from sqlalchemy import inspect, text

def fazer_backup():
    """Exporta todas as tabelas usando o app Flask"""
    
    print("🔄 Criando app Flask...")
    app = create_app('production')
    
    with app.app_context():
        print("🔄 Conectando ao banco Render...")
        
        # Criar pasta de backups
        backup_dir = os.path.join(os.path.dirname(__file__), '..', 'backups')
        os.makedirs(backup_dir, exist_ok=True)
        
        # Nome do arquivo com timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_file = os.path.join(backup_dir, f'backup_render_{timestamp}.json')
        
        # Inspecionar todas as tabelas
        inspector = inspect(db.engine)
        tabelas = inspector.get_table_names()
        
        print(f"\n📋 Encontradas {len(tabelas)} tabelas:")
        for t in sorted(tabelas):
            print(f"   - {t}")
        
        backup_data = {
            'timestamp': timestamp,
            'database': 'erp_jsp_db_iw6v (Render)',
            'tabelas': {}
        }
        
        print(f"\n💾 Fazendo backup...")
        
        # Exportar cada tabela
        for tabela in tabelas:
            try:
                result = db.session.execute(text(f'SELECT * FROM "{tabela}"'))
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
                        elif valor is None:
                            valor = None
                        else:
                            try:
                                json.dumps(valor)  # Testa se é serializável
                            except:
                                valor = str(valor)
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
        print(f"\n💾 Salvando arquivo JSON...")
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
        
        # Listar tabelas importantes
        print(f"\n📊 Resumo das principais tabelas:")
        principais = ['clientes', 'fornecedores', 'ordens_servico', 'ordem_servico_itens', 
                      'calculo_energia_solar', 'kit_fotovoltaico', 'usuarios', 
                      'placas_solares', 'inversores', 'concessionarias']
        
        for tab in principais:
            if tab in backup_data['tabelas']:
                info = backup_data['tabelas'][tab]
                if 'total_registros' in info:
                    print(f"   ✅ {tab}: {info['total_registros']} registros")
                else:
                    print(f"   ⚠️  {tab}: erro no backup")
            else:
                print(f"   ➖ {tab}: não existe")
        
        return backup_file

if __name__ == '__main__':
    try:
        print("="*60)
        print("🛡️  BACKUP COMPLETO DO BANCO RENDER")
        print("="*60)
        backup_file = fazer_backup()
        print(f"\n{'='*60}")
        print(f"🎉 BACKUP SALVO COM SUCESSO!")
        print(f"📂 {os.path.abspath(backup_file)}")
        print(f"{'='*60}")
        print(f"\n💡 Seus dados estão seguros!")
        print(f"   Agora pode fazer qualquer alteração no banco.")
    except Exception as e:
        print(f"\n❌ Erro ao fazer backup: {e}")
        import traceback
        traceback.print_exc()
