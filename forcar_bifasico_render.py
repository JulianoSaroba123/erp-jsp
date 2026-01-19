"""
Script para atualizar projeto 4 diretamente no Render via API
"""
import psycopg2
import os

# String de conexão do Render (pegar do .env ou Render Dashboard)
DATABASE_URL = "postgresql://erp_jsp_user:d5yZQ37KLmGw1CYpCXzb64IaUnNzQJze@dpg-cu6qrn08fa8c73a3lhag-a.oregon-postgres.render.com/erp_jsp"

print("🔧 Atualizando projeto 4 no Render...")
print("=" * 60)

try:
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    
    # Verificar valor atual
    cur.execute("SELECT id, tipo_instalacao, qtd_fases, circuito FROM projeto_solar WHERE id = 4")
    projeto = cur.fetchone()
    
    if projeto:
        print(f"\n📋 ANTES da atualização:")
        print(f"   ID: {projeto[0]}")
        print(f"   tipo_instalacao: {projeto[1]}")
        print(f"   qtd_fases: {projeto[2]}")
        print(f"   circuito: {projeto[3]}")
        
        # Atualizar para bifásico
        cur.execute("""
            UPDATE projeto_solar 
            SET tipo_instalacao = 'bifasica',
                qtd_fases = 2,
                circuito = 'Bifásico'
            WHERE id = 4
        """)
        conn.commit()
        
        # Verificar após atualização
        cur.execute("SELECT id, tipo_instalacao, qtd_fases, circuito FROM projeto_solar WHERE id = 4")
        projeto = cur.fetchone()
        
        print(f"\n✅ DEPOIS da atualização:")
        print(f"   ID: {projeto[0]}")
        print(f"   tipo_instalacao: {projeto[1]}")
        print(f"   qtd_fases: {projeto[2]}")
        print(f"   circuito: {projeto[3]}")
        
        print("\n🎯 Projeto atualizado! Recarregue a página no navegador.")
        
    else:
        print("❌ Projeto 4 não encontrado!")
    
    cur.close()
    conn.close()
    
except Exception as e:
    print(f"❌ Erro: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)
