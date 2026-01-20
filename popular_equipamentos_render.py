"""
Script SIMPLIFICADO para popular equipamentos no Render
Execute com a DATABASE_URL do Render como variável de ambiente
"""
import psycopg2
from datetime import datetime

# URL do banco do Render
DATABASE_URL = "postgresql://erp_jsp_local_user:qAr5fOLCGZJ6bk7NcblN3tPJqDvmPE9q@dpg-cu76r2pu0jms738vjs00-a.oregon-postgres.render.com/erp_jsp_local"

def main():
    print("=" * 60)
    print("🔧 POPULANDO EQUIPAMENTOS NO RENDER")
    print("=" * 60)
    
    # Conectar ao banco
    print("\n📡 Conectando ao PostgreSQL do Render...")
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    
    # Listar clientes
    print("\n👥 Buscando clientes...")
    cur.execute("SELECT id, nome FROM clientes ORDER BY id LIMIT 5")
    clientes = cur.fetchall()
    
    if not clientes:
        print("❌ Nenhum cliente encontrado!")
        return
    
    print(f"✅ Encontrados {len(clientes)} clientes:")
    for cliente_id, nome in clientes:
        print(f"   - ID {cliente_id}: {nome}")
    
    # Equipamentos de exemplo
    equipamentos = [
        ('Calandra Termográfica M1', 'Calandra', 'Mirandópolis', 'TF 601', '2024', 'MR JACKY'),
        ('Calandra Termográfica M5', 'Calandra', 'Mirandópolis', 'TF-610', '0525', 'MR JACKY'),
        ('Prensa Térmica 8x1', 'Prensa', 'Compacta Print', 'Premium 8x1', 'PR2024001', None),
        ('Impressora Sublimática', 'Impressora', 'Epson', 'L3250', 'IMP2024001', None),
        ('Computador Desktop', 'Computador', 'Dell', 'Optiplex 3080', 'PC2024001', None),
    ]
    
    criados = 0
    print(f"\n🔧 Criando equipamentos...")
    
    for i, (cliente_id, cliente_nome) in enumerate(clientes):
        # Criar 1-2 equipamentos por cliente
        for j in range(min(2, len(equipamentos) - i * 2)):
            idx = i * 2 + j
            if idx >= len(equipamentos):
                break
            
            nome, tipo, marca, modelo, num_serie, localizacao = equipamentos[idx]
            
            # Verificar se já existe
            cur.execute("""
                SELECT id FROM equipamentos 
                WHERE cliente_id = %s AND numero_serie = %s
            """, (cliente_id, num_serie))
            
            if cur.fetchone():
                print(f"  ⚠️  Já existe: {nome} (S/N: {num_serie})")
                continue
            
            # Inserir equipamento
            cur.execute("""
                INSERT INTO equipamentos (
                    cliente_id, nome, tipo, marca, modelo, numero_serie, 
                    localizacao, descricao, ativo, criado_em, atualizado_em
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                )
            """, (
                cliente_id,
                nome,
                tipo,
                marca,
                modelo,
                num_serie,
                localizacao or 'Setor Calandras',
                f'Equipamento criado via migração para {cliente_nome}',
                True,
                datetime.now(),
                datetime.now()
            ))
            
            criados += 1
            print(f"  ✅ Criado: {nome} para {cliente_nome}")
    
    # Commit
    conn.commit()
    print(f"\n✅ Total de {criados} equipamentos criados no RENDER!")
    
    # Verificar resultado
    cur.execute("SELECT COUNT(*) FROM equipamentos WHERE ativo = true")
    total = cur.fetchone()[0]
    print(f"📊 Total de equipamentos ativos no Render: {total}")
    
    # Mostrar por cliente
    print("\n📋 EQUIPAMENTOS POR CLIENTE:")
    for cliente_id, cliente_nome in clientes:
        cur.execute("""
            SELECT COUNT(*) FROM equipamentos 
            WHERE cliente_id = %s AND ativo = true
        """, (cliente_id,))
        count = cur.fetchone()[0]
        print(f"   {cliente_nome}: {count} equipamentos")
    
    cur.close()
    conn.close()
    
    print("\n" + "=" * 60)
    print("✅ Concluído!")
    print("🌐 Teste em: https://erp-jsp-th5o.onrender.com/os/nova")
    print("=" * 60)

if __name__ == '__main__':
    main()
