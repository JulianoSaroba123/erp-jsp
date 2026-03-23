"""
Script para adicionar 6 campos de horário detalhado no banco de dados
Substitui o sistema antigo de 2 campos (hora_inicial, hora_final) 
pelo novo sistema de 6 campos detalhados
"""
import os
import sys
from sqlalchemy import create_engine, text

def adicionar_campos_horarios():
    """Adiciona os 6 novos campos de horário detalhado"""
    
    # Pega a URL do banco do .env ou usa SQLite local
    DATABASE_URL = os.getenv('DATABASE_URL')
    
    if not DATABASE_URL:
        # Banco local
        DATABASE_URL = 'sqlite:///database/database.db'
        print("📊 Usando banco SQLite local")
    else:
        print("📊 Usando banco PostgreSQL (Render)")
        # Fix para Render: postgres:// -> postgresql://
        if DATABASE_URL.startswith('postgres://'):
            DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)
    
    print(f"🔗 Conectando ao banco...")
    engine = create_engine(DATABASE_URL)
    
    try:
        with engine.connect() as conn:
            print("🔧 Conectando ao banco de dados...")
            
            # Lista de comandos SQL para adicionar as colunas
            comandos = [
                "ALTER TABLE ordem_servico ADD COLUMN IF NOT EXISTS hora_entrada_manha TIME",
                "ALTER TABLE ordem_servico ADD COLUMN IF NOT EXISTS hora_saida_almoco TIME",
                "ALTER TABLE ordem_servico ADD COLUMN IF NOT EXISTS hora_retorno_almoco TIME",
                "ALTER TABLE ordem_servico ADD COLUMN IF NOT EXISTS hora_saida TIME",
                "ALTER TABLE ordem_servico ADD COLUMN IF NOT EXISTS hora_entrada_extra TIME",
                "ALTER TABLE ordem_servico ADD COLUMN IF NOT EXISTS hora_saida_extra TIME",
                "ALTER TABLE ordem_servico ADD COLUMN IF NOT EXISTS horas_normais VARCHAR(20)",
                "ALTER TABLE ordem_servico ADD COLUMN IF NOT EXISTS horas_extras VARCHAR(20)"
            ]
            
            # Para SQLite, precisa verificar se as colunas existem antes
            if 'sqlite' in DATABASE_URL:
                result = conn.execute(text("PRAGMA table_info(ordem_servico)"))
                colunas_existentes = [row[1] for row in result.fetchall()]
                
                comandos_ajustados = []
                for cmd in comandos:
                    coluna = cmd.split('ADD COLUMN IF NOT EXISTS ')[1].split(' ')[0]
                    if coluna not in colunas_existentes:
                        # SQLite não suporta IF NOT EXISTS, então removemos
                        cmd_sqlite = cmd.replace('IF NOT EXISTS ', '')
                        comandos_ajustados.append(cmd_sqlite)
                        print(f"📝 Adicionando coluna: {coluna}")
                    else:
                        print(f"✅ Coluna '{coluna}' já existe")
                comandos = comandos_ajustados
            
            # Executar comandos
            for cmd in comandos:
                print(f"📝 Executando: {cmd}")
                conn.execute(text(cmd))
                conn.commit()
            
            print("✅ Migração concluída com sucesso!")
            print("\n📊 Novos campos adicionados:")
            print("   - hora_entrada_manha (TIME)")
            print("   - hora_saida_almoco (TIME)")
            print("   - hora_retorno_almoco (TIME)")
            print("   - hora_saida (TIME)")
            print("   - hora_entrada_extra (TIME)")
            print("   - hora_saida_extra (TIME)")
            print("   - horas_normais (VARCHAR 20)")
            print("   - horas_extras (VARCHAR 20)")
            print("\n💡 Os campos antigos hora_inicial e hora_final foram mantidos para compatibilidade")
            
    except Exception as e:
        print(f"❌ Erro durante migração: {str(e)}")
        raise

if __name__ == "__main__":
    adicionar_campos_horarios()
