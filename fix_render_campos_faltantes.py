"""
🚨 CORREÇÃO URGENTE - RENDER 🚨
Adiciona campos faltantes que causam erro 500 em /energia-solar/projetos

Execute no Render Shell:
python fix_render_campos_faltantes.py
"""
import os
os.environ['SKIP_MIGRATIONS'] = '1'

from app.app import create_app
from app.extensoes import db

app = create_app()

with app.app_context():
    print("🔧 Adicionando campos faltantes em projeto_solar...\n")
    
    # Campos que o template usa mas não existem no modelo
    campos_faltantes = [
        # Campos do template projetos_lista.html
        ("circuito", "VARCHAR(20)"),  # Monofásico, Bifásico, Trifásico
        ("status_orcamento", "VARCHAR(20) DEFAULT 'pendente'"),  # pendente, em_analise, aprovado, revisao
        
        # Outros campos que podem estar faltando
        ("numero", "VARCHAR(20)"),
        ("tipo_instalacao", "VARCHAR(20) DEFAULT 'monofasica'"),
        ("taxa_disponibilidade", "DOUBLE PRECISION"),
        ("economia_mensal", "DOUBLE PRECISION"),
        ("tempo_retorno", "DOUBLE PRECISION"),
        ("economia_25_anos", "DOUBLE PRECISION"),
        ("economia_anual", "DOUBLE PRECISION"),
        ("payback_anos", "DOUBLE PRECISION"),
        ("modalidade_gd", "VARCHAR(50)"),
        ("aliquota_fio_b", "DOUBLE PRECISION"),
        ("usuario_criador", "VARCHAR(100)"),
        ("data_criacao", "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"),
        ("data_atualizacao", "TIMESTAMP"),
    ]
    
    adicionados = []
    ja_existem = []
    erros = []
    
    for campo, tipo in campos_faltantes:
        try:
            # Tentar adicionar (PostgreSQL ignora se já existe com IF NOT EXISTS)
            db.session.execute(db.text(f"""
                ALTER TABLE projeto_solar 
                ADD COLUMN IF NOT EXISTS {campo} {tipo}
            """))
            adicionados.append(campo)
            print(f"✅ {campo}")
        except Exception as e:
            erro_str = str(e).lower()
            if "already exists" in erro_str or "duplicate column" in erro_str:
                ja_existem.append(campo)
                print(f"⏭️ {campo} (já existe)")
            else:
                erros.append((campo, str(e)))
                print(f"❌ {campo}: {e}")
    
    try:
        db.session.commit()
        print(f"\n{'='*50}")
        print("✅ CORREÇÃO CONCLUÍDA!")
        print(f"{'='*50}")
        print(f"  Campos adicionados: {len(adicionados)}")
        print(f"  Campos existentes: {len(ja_existem)}")
        print(f"  Erros: {len(erros)}")
        
        if erros:
            print("\n⚠️ Erros encontrados:")
            for campo, erro in erros:
                print(f"  - {campo}: {erro}")
                
    except Exception as e:
        print(f"\n❌ ERRO AO COMMITAR: {e}")
        db.session.rollback()
        
    # Atualizar circuito baseado em tipo_instalacao para dados existentes
    print("\n🔄 Sincronizando circuito com tipo_instalacao...")
    try:
        db.session.execute(db.text("""
            UPDATE projeto_solar 
            SET circuito = CASE 
                WHEN tipo_instalacao = 'monofasica' THEN 'Monofásico'
                WHEN tipo_instalacao = 'bifasica' THEN 'Bifásico'
                WHEN tipo_instalacao = 'trifasica' THEN 'Trifásico'
                ELSE circuito
            END
            WHERE circuito IS NULL AND tipo_instalacao IS NOT NULL
        """))
        db.session.commit()
        print("✅ Sincronização concluída!")
    except Exception as e:
        print(f"⚠️ Erro na sincronização: {e}")
