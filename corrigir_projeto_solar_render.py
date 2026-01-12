"""
Correção do erro 500 - Adiciona campo 'numero' na tabela projeto_solar
Executa diretamente no Render
"""
import os
import sys

# Detectar ambiente
if os.getenv('DATABASE_URL'):
    print("🌐 AMBIENTE: Render (Produção)")
else:
    print("💻 AMBIENTE: Local")

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))

from app.app import create_app
from app.extensoes import db

def corrigir_campo_numero():
    """Adiciona o campo 'numero' se não existir"""
    
    print("\n🔧 Corrigindo campo 'numero' em projeto_solar...\n")
    
    app = create_app()
    
    with app.app_context():
        try:
            # Verificar se o campo já existe
            print("1️⃣ Verificando se campo 'numero' existe...")
            result = db.session.execute(db.text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'projeto_solar' 
                AND column_name = 'numero'
            """))
            
            existe = result.fetchone() is not None
            
            if existe:
                print("✅ Campo 'numero' já existe!")
            else:
                print("⚠️ Campo 'numero' NÃO existe. Adicionando...")
                
                # Adicionar o campo
                db.session.execute(db.text("""
                    ALTER TABLE projeto_solar 
                    ADD COLUMN numero VARCHAR(20)
                """))
                db.session.commit()
                
                print("✅ Campo 'numero' adicionado com sucesso!")
            
            # Verificar outros campos que podem estar faltando
            print("\n2️⃣ Verificando outros campos importantes...")
            
            campos_necessarios = {
                'metodo_calculo': "VARCHAR(50)",
                'consumo_kwh_mes': "DOUBLE PRECISION",
                'historico_consumo': "JSON",
                'valor_conta_luz': "DOUBLE PRECISION",
                'tarifa_kwh': "DOUBLE PRECISION",
                'tipo_instalacao': "VARCHAR(20) DEFAULT 'monofasica'",
                'potencia_kwp': "DOUBLE PRECISION",
                'geracao_estimada_mes': "DOUBLE PRECISION",
                'simultaneidade': "DOUBLE PRECISION DEFAULT 0.80",
                'perdas_sistema': "DOUBLE PRECISION DEFAULT 0.20",
                'modo_equipamento': "VARCHAR(20)",
                'kit_id': "INTEGER",
                'placa_id': "INTEGER",
                'inversor_id': "INTEGER",
                'qtd_placas': "INTEGER",
                'qtd_inversores': "INTEGER",
                'orientacao': "VARCHAR(20)",
                'inclinacao': "DOUBLE PRECISION",
                'direcao': "VARCHAR(20)",
                'linhas_placas': "INTEGER",
                'colunas_placas': "INTEGER",
                'area_necessaria': "DOUBLE PRECISION",
                'string_box': "BOOLEAN DEFAULT FALSE",
                'disjuntor_cc': "VARCHAR(50)",
                'disjuntor_ca': "VARCHAR(50)",
                'cabo_cc': "VARCHAR(50)",
                'cabo_ca': "VARCHAR(50)",
                'estrutura_fixacao': "VARCHAR(100)",
                'componentes_extras': "JSON",
                'custo_equipamentos': "DOUBLE PRECISION",
                'custo_instalacao': "DOUBLE PRECISION",
                'custo_projeto': "DOUBLE PRECISION",
                'custo_total': "DOUBLE PRECISION",
                'margem_lucro': "DOUBLE PRECISION",
                'valor_venda': "DOUBLE PRECISION",
                'lei_14300_ano': "INTEGER",
                'taxa_disponibilidade': "DOUBLE PRECISION",
                'economia_mensal': "DOUBLE PRECISION",
                'economia_anual': "DOUBLE PRECISION",
                'tempo_retorno': "DOUBLE PRECISION",
                'economia_25_anos': "DOUBLE PRECISION",
                'status': "VARCHAR(20) DEFAULT 'rascunho'",
                'data_criacao': "TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
                'data_atualizacao': "TIMESTAMP",
                'observacoes': "TEXT"
            }
            
            # Verificar campos existentes
            result = db.session.execute(db.text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'projeto_solar'
            """))
            
            campos_existentes = {row[0] for row in result}
            
            # Adicionar campos faltantes
            campos_adicionados = []
            for campo, tipo in campos_necessarios.items():
                if campo not in campos_existentes:
                    try:
                        print(f"   Adicionando campo '{campo}'...")
                        db.session.execute(db.text(f"""
                            ALTER TABLE projeto_solar 
                            ADD COLUMN {campo} {tipo}
                        """))
                        campos_adicionados.append(campo)
                    except Exception as e:
                        print(f"   ⚠️ Erro ao adicionar '{campo}': {e}")
            
            if campos_adicionados:
                db.session.commit()
                print(f"\n✅ {len(campos_adicionados)} campos adicionados:")
                for campo in campos_adicionados:
                    print(f"   - {campo}")
            else:
                print("✅ Todos os campos já existem!")
            
            # Verificar estrutura final
            print("\n3️⃣ Estrutura final da tabela projeto_solar:")
            result = db.session.execute(db.text("""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = 'projeto_solar'
                ORDER BY ordinal_position
            """))
            
            total = 0
            for row in result:
                total += 1
                print(f"   {total}. {row[0]}: {row[1]}")
            
            print(f"\n✅ Total: {total} campos")
            
        except Exception as e:
            print(f"\n❌ ERRO: {e}")
            import traceback
            traceback.print_exc()
            db.session.rollback()

if __name__ == '__main__':
    corrigir_campo_numero()
