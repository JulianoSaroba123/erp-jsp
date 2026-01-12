"""
Diagnóstico do erro 500 na rota /projetos no Render
"""
import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))

def diagnosticar():
    """Diagnostica o problema na rota de projetos"""
    print("🔍 Diagnóstico - Erro 500 em /projetos\n")
    
    try:
        from app.app import create_app
        from app.extensoes import db
        
        app = create_app()
        
        with app.app_context():
            print("✅ App criado com sucesso\n")
            
            # 1. Verificar se tabela projeto_solar existe
            print("📋 Verificando tabela 'projeto_solar'...")
            result = db.session.execute(db.text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'projeto_solar'
                )
            """))
            existe = result.scalar()
            
            if existe:
                print("✅ Tabela 'projeto_solar' existe!")
                
                # Contar registros
                result = db.session.execute(db.text("SELECT COUNT(*) FROM projeto_solar"))
                count = result.scalar()
                print(f"📊 Total de projetos: {count}")
                
                # Ver estrutura
                print("\n📋 Estrutura da tabela:")
                result = db.session.execute(db.text("""
                    SELECT column_name, data_type, is_nullable
                    FROM information_schema.columns
                    WHERE table_name = 'projeto_solar'
                    ORDER BY ordinal_position
                    LIMIT 10
                """))
                for row in result:
                    print(f"  - {row[0]}: {row[1]} (nullable: {row[2]})")
                    
            else:
                print("❌ Tabela 'projeto_solar' NÃO EXISTE!")
                print("\n🔧 É necessário criar a tabela!")
                print("Execute: python scripts/migrar_energia_solar_v3.py")
            
            # 2. Testar import do modelo
            print("\n📦 Testando import do modelo ProjetoSolar...")
            try:
                from app.energia_solar.catalogo_model import ProjetoSolar
                print("✅ Modelo ProjetoSolar importado com sucesso!")
                print(f"   Tabela: {ProjetoSolar.__tablename__}")
            except Exception as e:
                print(f"❌ Erro ao importar ProjetoSolar: {e}")
            
            # 3. Testar query
            print("\n🔍 Testando query...")
            try:
                from app.energia_solar.catalogo_model import ProjetoSolar
                projetos = ProjetoSolar.query.all()
                print(f"✅ Query executada! Encontrados {len(projetos)} projetos")
                
                if projetos:
                    p = projetos[0]
                    print(f"\n   Exemplo: ID={p.id}, Cliente={p.nome_cliente}")
                    
            except Exception as e:
                print(f"❌ Erro na query: {e}")
                import traceback
                traceback.print_exc()
            
            # 4. Verificar template
            print("\n📄 Verificando template...")
            template_path = os.path.join('app', 'energia_solar', 'templates', 'energia_solar', 'projetos_lista.html')
            if os.path.exists(template_path):
                print(f"✅ Template existe: {template_path}")
            else:
                print(f"❌ Template NÃO encontrado: {template_path}")
                
                # Listar templates existentes
                templates_dir = os.path.join('app', 'energia_solar', 'templates', 'energia_solar')
                if os.path.exists(templates_dir):
                    print(f"\n📂 Templates disponíveis em {templates_dir}:")
                    for f in os.listdir(templates_dir):
                        print(f"  - {f}")
            
            # 5. Verificar outras tabelas relacionadas
            print("\n📊 Verificando tabelas relacionadas...")
            tabelas = [
                'concessionarias',
                'orcamento_itens', 
                'projeto_financiamento',
                'marco_legal_taxacao',
                'custos_fixos_template'
            ]
            
            for tabela in tabelas:
                result = db.session.execute(db.text(f"""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_name = '{tabela}'
                    )
                """))
                existe = result.scalar()
                status = "✅" if existe else "❌"
                print(f"{status} {tabela}: {'existe' if existe else 'NÃO existe'}")
            
    except Exception as e:
        print(f"\n❌ ERRO GERAL: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    diagnosticar()
