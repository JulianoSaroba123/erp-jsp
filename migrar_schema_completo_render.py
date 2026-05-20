"""
🚨 MIGRAÇÃO COMPLETA - 94 COLUNAS PARA RENDER
================================================
Script IDEMPOTENTE para adicionar TODAS as colunas faltantes
na tabela calculo_energia_solar no PostgreSQL do Render.

SEGURANÇA:
- Verifica quais colunas existem ANTES de adicionar
- Adiciona APENAS as colunas ausentes
- NÃO drop/recreate (preserva dados de produção)
- Pode ser executado múltiplas vezes sem problemas

USO:
  python migrar_schema_completo_render.py
"""

from app import create_app
from app.extensoes import db
from sqlalchemy import text, inspect
import sys


# 🗂️ DEFINIÇÃO COMPLETA DAS 94 COLUNAS
# Baseado no model CalculoEnergiaSolar + banco local SQLite
SCHEMA_COMPLETO = {
    # ===== IDENTIFICAÇÃO E DADOS BÁSICOS =====
    'id': 'SERIAL PRIMARY KEY',
    'numero_projeto': 'TEXT',
    'cliente_id': 'INTEGER',
    'nome_cliente': 'TEXT',
    'local_instalacao': 'TEXT',
    'titulo_projeto': 'TEXT',
    'endereco_instalacao': 'TEXT',
    
    # ===== DADOS DE CONSUMO =====
    'consumo_mensal': 'NUMERIC(12,2)',
    'consumo_anual': 'NUMERIC(12,2)',
    'tarifa_energia': 'NUMERIC(12,4)',
    'historico_consumo_json': 'TEXT',
    'iluminacao_publica': 'NUMERIC(12,2)',
    'demais_custos': 'NUMERIC(12,2)',
    'fatura_minima': 'NUMERIC(12,2)',
    'taxa_disponibilidade': 'NUMERIC(12,2)',
    
    # ===== PARÂMETROS DE SIMULAÇÃO =====
    'simultaneidade': 'NUMERIC(5,2)',
    'reajuste_anual_energia': 'NUMERIC(5,2)',
    'perda_eficiencia_anual': 'NUMERIC(5,4)',
    'vida_util_sistema': 'INTEGER',
    
    # ===== DADOS DE LOCALIZAÇÃO =====
    'cidade': 'TEXT',
    'estado': 'TEXT',
    'latitude': 'NUMERIC(10,6)',
    'longitude': 'NUMERIC(10,6)',
    'irradiacao_media': 'NUMERIC(10,4)',
    'irradiacao_mensal_json': 'TEXT',
    'cliente_grupo': 'TEXT',
    
    # ===== EQUIPAMENTOS - PLACA SOLAR =====
    'placa_id': 'INTEGER',
    'placa_modelo': 'TEXT',
    'placa_fabricante': 'TEXT',
    'placa_potencia': 'NUMERIC(10,2)',
    'placa_comprimento': 'NUMERIC(10,2)',
    'placa_largura': 'NUMERIC(10,2)',
    'placa_num_celulas': 'INTEGER',
    
    # ===== EQUIPAMENTOS - INVERSOR =====
    'inversor_id': 'INTEGER',
    'inversor_modelo': 'TEXT',
    'inversor_fabricante': 'TEXT',
    'inversor_potencia': 'NUMERIC(10,2)',
    'inversor_tipo': 'TEXT',
    
    # ===== DIMENSIONAMENTO DO SISTEMA =====
    'potencia_sistema': 'NUMERIC(12,2)',
    'numero_paineis': 'INTEGER',
    'numero_inversores': 'INTEGER',
    'area_necessaria': 'NUMERIC(12,2)',
    'producao_especifica': 'NUMERIC(12,2)',
    
    # ===== INSTALAÇÃO ELÉTRICA =====
    'circuito': 'TEXT',
    'tensao_instalacao': 'TEXT',
    'qtd_placas_instalacao': 'INTEGER',
    'qtd_inversores_instalacao': 'INTEGER',
    'disjuntor': 'TEXT',
    'cabo_fase': 'TEXT',
    'cabo_neutro': 'TEXT',
    'cabo_aterramento': 'TEXT',
    'conexao_tipo': 'TEXT',
    
    # ===== CARACTERÍSTICAS DA INSTALAÇÃO =====
    'posicao_placas': 'TEXT',
    'disposicao': 'TEXT',
    'area_instalacao': 'NUMERIC(12,2)',
    'tipo_instalacao': 'TEXT',
    'orientacao': 'TEXT',
    'inclinacao': 'NUMERIC(5,2)',
    
    # ===== GERAÇÃO E ECONOMIA =====
    'geracao_mensal': 'NUMERIC(12,2)',
    'geracao_anual': 'NUMERIC(12,2)',
    'geracao_mensal_json': 'TEXT',
    'economia_mensal': 'NUMERIC(12,2)',
    'economia_anual': 'NUMERIC(12,2)',
    'economia_25anos': 'NUMERIC(12,2)',
    'economia_antes_lei': 'NUMERIC(12,2)',
    'economia_depois_lei': 'NUMERIC(12,2)',
    'economia_anual_prevista': 'NUMERIC(12,2)',
    
    # ===== CUSTOS E VALORES =====
    'custo_total': 'NUMERIC(12,2)',
    'valor_nota_fiscal': 'NUMERIC(12,2)',
    'valor_faturado_empresa': 'NUMERIC(12,2)',
    'valor_faturado_cliente': 'NUMERIC(12,2)',
    'impostos': 'NUMERIC(12,2)',
    'impostos_percentual': 'NUMERIC(5,2)',
    'lucro': 'NUMERIC(12,2)',
    'percentual_lucro': 'NUMERIC(5,2)',
    'valor_orcamento_total': 'NUMERIC(12,2)',
    
    # ===== ANÁLISE FINANCEIRA =====
    'payback_anos': 'NUMERIC(10,2)',
    'payback_meses': 'INTEGER',
    'roi': 'NUMERIC(12,2)',
    'roi_percentual': 'NUMERIC(5,2)',
    
    # ===== FINANCIAMENTO =====
    'valor_financiado': 'NUMERIC(12,2)',
    'periodo_financiamento': 'INTEGER',
    'juros_mensal': 'NUMERIC(5,4)',
    'parcela_mensal': 'NUMERIC(12,2)',
    
    # ===== INFORMAÇÕES ADICIONAIS =====
    'observacoes': 'TEXT',
    'data_calculo': 'TIMESTAMP',
    'data_prevista_entrega': 'TIMESTAMP',
    'previsao_entrega': 'TIMESTAMP',
    'usuario_id': 'INTEGER',
    'concessionaria_id': 'INTEGER',
    
    # ===== STATUS E CONTROLE =====
    'status': 'TEXT',
    'etapa_projeto': 'TEXT',
    'status_orcamento': 'TEXT',
    
    # ===== RELACIONAMENTO KIT =====
    'kit_id': 'INTEGER'
}


def listar_colunas_existentes(engine):
    """Lista todas as colunas existentes na tabela calculo_energia_solar"""
    inspector = inspect(engine)
    colunas = [col['name'] for col in inspector.get_columns('calculo_energia_solar')]
    return set(colunas)


def adicionar_colunas_faltantes(app):
    """Adiciona todas as colunas faltantes na tabela"""
    print("\n🔍 AUDITORIA DO SCHEMA")
    print("=" * 60)
    
    with app.app_context():
        # Lista colunas existentes
        colunas_existentes = listar_colunas_existentes(db.engine)
        print(f"📋 Colunas existentes no banco: {len(colunas_existentes)}")
        
        # Identifica colunas faltantes
        colunas_faltantes = set(SCHEMA_COMPLETO.keys()) - colunas_existentes
        print(f"❌ Colunas faltantes: {len(colunas_faltantes)}")
        
        if not colunas_faltantes:
            print("\n✅ BANCO JÁ ESTÁ COMPLETO!")
            print("   Todas as 94 colunas já existem.")
            return True
        
        print("\n🔧 INICIANDO MIGRAÇÃO")
        print("=" * 60)
        
        # Adiciona cada coluna faltante
        sucessos = 0
        erros = 0
        
        for coluna in sorted(colunas_faltantes):
            tipo_sql = SCHEMA_COMPLETO[coluna]
            
            # Pula a coluna 'id' se estiver faltando (já deve existir como PK)
            if coluna == 'id':
                continue
            
            try:
                # Monta comando ALTER TABLE
                sql_add = f'ALTER TABLE calculo_energia_solar ADD COLUMN IF NOT EXISTS {coluna} {tipo_sql};'
                
                with db.engine.connect() as conn:
                    conn.execute(text(sql_add))
                    conn.commit()
                
                print(f"  ✅ {coluna:30} ({tipo_sql})")
                sucessos += 1
                
            except Exception as e:
                print(f"  ❌ {coluna:30} ERRO: {str(e)[:50]}")
                erros += 1
        
        print("\n📊 RESULTADO DA MIGRAÇÃO")
        print("=" * 60)
        print(f"✅ Colunas adicionadas: {sucessos}")
        print(f"❌ Erros: {erros}")
        
        # Verifica resultado final
        colunas_finais = listar_colunas_existentes(db.engine)
        print(f"📋 Total de colunas após migração: {len(colunas_finais)}")
        
        if len(colunas_finais) == 94:
            print("\n🎉 MIGRAÇÃO COMPLETA!")
            print("   Banco agora possui todas as 94 colunas.")
            return True
        else:
            print(f"\n⚠️ MIGRAÇÃO PARCIAL")
            print(f"   Esperado: 94 colunas")
            print(f"   Atual: {len(colunas_finais)} colunas")
            print(f"   Faltam: {94 - len(colunas_finais)} colunas")
            return False


def adicionar_foreign_keys():
    """Adiciona foreign keys para kit_id, placa_id, inversor_id, concessionaria_id"""
    print("\n🔗 ADICIONANDO FOREIGN KEYS")
    print("=" * 60)
    
    app = create_app()
    with app.app_context():
        fks = [
            ('fk_calculo_energia_kit', 'kit_id', 'kit_solar', 'id'),
            ('fk_calculo_energia_placa', 'placa_id', 'placa_solar', 'id'),
            ('fk_calculo_energia_inversor', 'inversor_id', 'inversor_solar', 'id'),
            ('fk_calculo_energia_concessionaria', 'concessionaria_id', 'concessionaria', 'id'),
        ]
        
        for fk_name, coluna_origem, tabela_destino, coluna_destino in fks:
            try:
                # Verifica se FK já existe (PostgreSQL)
                check_sql = f"""
                SELECT 1 FROM information_schema.table_constraints 
                WHERE constraint_name = '{fk_name}' 
                AND table_name = 'calculo_energia_solar';
                """
                
                with db.engine.connect() as conn:
                    result = conn.execute(text(check_sql))
                    if result.fetchone():
                        print(f"  ⏭️  FK {fk_name} já existe")
                        continue
                    
                    # Adiciona FK
                    add_fk_sql = f"""
                    ALTER TABLE calculo_energia_solar 
                    ADD CONSTRAINT {fk_name} 
                    FOREIGN KEY ({coluna_origem}) 
                    REFERENCES {tabela_destino}({coluna_destino});
                    """
                    
                    conn.execute(text(add_fk_sql))
                    conn.commit()
                    print(f"  ✅ FK {fk_name} adicionada")
                    
            except Exception as e:
                print(f"  ⚠️  FK {fk_name} - {str(e)[:60]}")


def main():
    """Função principal"""
    print("\n" + "=" * 60)
    print("🚨 MIGRAÇÃO COMPLETA - SCHEMA CALCULO_ENERGIA_SOLAR")
    print("=" * 60)
    
    try:
        app = create_app()
        
        # 1. Adiciona colunas faltantes
        sucesso = adicionar_colunas_faltantes(app)
        
        if not sucesso:
            print("\n⚠️ Migração incompleta. Verifique os erros acima.")
            return 1
        
        # 2. Adiciona foreign keys
        adicionar_foreign_keys()
        
        print("\n✅ MIGRAÇÃO FINALIZADA COM SUCESSO!")
        print("=" * 60)
        
        return 0
        
    except Exception as e:
        print(f"\n❌ ERRO CRÍTICO: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
