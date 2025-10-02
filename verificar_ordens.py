import sqlite3
import json

print("=== VERIFICAÇÃO DE ORDENS NO BANCO ===")

# Conectar ao banco
conn = sqlite3.connect('database/database.db')
cursor = conn.cursor()

# Verificar se a tabela existe
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='ordens_servico'")
tabela_existe = cursor.fetchone()

if not tabela_existe:
    print("❌ ERRO: Tabela 'ordens_servico' não existe!")
    conn.close()
    exit()

print("✅ Tabela 'ordens_servico' existe")

# Contar total de ordens
cursor.execute('SELECT COUNT(*) FROM ordens_servico')
total_ordens = cursor.fetchone()[0]
print(f"📊 Total de ordens no banco: {total_ordens}")

# Contar ordens ativas
cursor.execute('SELECT COUNT(*) FROM ordens_servico WHERE ativo = 1')
total_ativas = cursor.fetchone()[0]
print(f"📊 Ordens ativas: {total_ativas}")

# Contar ordens inativas
cursor.execute('SELECT COUNT(*) FROM ordens_servico WHERE ativo = 0 OR ativo IS NULL')
total_inativas = cursor.fetchone()[0]
print(f"📊 Ordens inativas/nulas: {total_inativas}")

# Listar todas as ordens (limitado a 20)
print(f"\n=== LISTAGEM DAS ORDENS ===")
cursor.execute('''
    SELECT id, codigo, cliente_id, data_emissao, valor_total, ativo, anexos_dados
    FROM ordens_servico 
    ORDER BY id DESC 
    LIMIT 20
''')

ordens = cursor.fetchall()

if not ordens:
    print("❌ Nenhuma ordem encontrada no banco!")
else:
    print(f"📋 Últimas {len(ordens)} ordens:")
    for ordem in ordens:
        id_ordem, codigo, cliente_id, data_emissao, valor_total, ativo, anexos_dados = ordem
        status = "✅ Ativa" if ativo == 1 else "❌ Inativa"
        
        # Verificar anexos
        anexos_count = 0
        if anexos_dados:
            try:
                anexos = json.loads(anexos_dados)
                anexos_count = len(anexos)
            except:
                pass
        
        print(f"  [{id_ordem}] {codigo} - Cliente: {cliente_id} - {status}")
        print(f"      Data: {data_emissao} - Valor: R$ {valor_total or 0:.2f}")
        print(f"      Anexos: {anexos_count}")

# Verificar estrutura da tabela
print(f"\n=== ESTRUTURA DA TABELA ===")
cursor.execute("PRAGMA table_info(ordens_servico)")
colunas = cursor.fetchall()
for coluna in colunas:
    print(f"  {coluna[1]} ({coluna[2]}) - Null: {coluna[3] == 0}")

conn.close()
print("\n=== FIM DA VERIFICAÇÃO ===")