"""
Script de inicialização - Popula banco com dados padrão se estiver vazio
DEVE SER EXECUTADO NA INICIALIZAÇÃO DO APP
"""
import os
import sys

def popular_banco_inicial():
    """Popula o banco com dados iniciais se estiver vazio"""
    from app.extensoes import db
    from app.ordem_servico.ordem_servico_model import OrdemServico
    from app.cliente.cliente_model import Cliente
    
    try:
        # Verifica se já tem dados
        total_os = OrdemServico.query.count()
        
        if total_os > 0:
            print(f"✅ Banco já populado ({total_os} OS encontradas)")
            return
        
        print("📊 Banco vazio - verificando se precisa importar dados...")
        
        # Verifica se tem clientes
        total_clientes = Cliente.query.count()
        print(f"   Clientes no banco: {total_clientes}")
        
        if total_clientes == 0:
            print("⚠️ Nenhum dado encontrado - banco limpo")
            return
        
        # Se tem clientes mas não tem OS, tenta importar do SQLite local
        if os.path.exists('erp.db'):
            print("🔄 Importando dados do erp.db local...")
            import sqlite3
            from sqlalchemy import text
            from datetime import datetime
            
            conn = sqlite3.connect('erp.db')
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Cria mapeamento de clientes
            clientes_local = cursor.execute("SELECT id, nome, cpf_cnpj FROM clientes").fetchall()
            clientes_render = Cliente.query.all()
            
            mapa_clientes = {}
            for cli_local in clientes_local:
                for cli_render in clientes_render:
                    if cli_render.cpf_cnpj and cli_render.cpf_cnpj == cli_local['cpf_cnpj']:
                        mapa_clientes[cli_local['id']] = cli_render.id
                        break
            
            # Importa OS
            ordens = cursor.execute("SELECT * FROM ordem_servico ORDER BY id").fetchall()
            importadas = 0
            
            for row in ordens:
                cliente_id_render = mapa_clientes.get(row['cliente_id'])
                if not cliente_id_render:
                    continue
                
                nova_os = OrdemServico(
                    numero=row['numero'],
                    cliente_id=cliente_id_render,
                    titulo=row['titulo'] or 'OS sem título',
                    descricao=row['descricao'],
                    status=row['status'] or 'aberta',
                    prioridade=row['prioridade'] or 'normal',
                    data_abertura=row['data_abertura'] if row['data_abertura'] else datetime.now().date(),
                    valor_total=row['valor_total'] or 0,
                    ativo=True
                )
                
                db.session.add(nova_os)
                importadas += 1
            
            db.session.commit()
            conn.close()
            
            print(f"✅ {importadas} OS importadas com sucesso!")
        
    except Exception as e:
        print(f"❌ Erro ao popular banco: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    from app.app import create_app
    app = create_app()
    
    with app.app_context():
        popular_banco_inicial()
