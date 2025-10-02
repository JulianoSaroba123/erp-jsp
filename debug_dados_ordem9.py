import sqlite3
import json

print("=== ANALISE DADOS ORDEM 9 ===")

# Conectar ao banco
conn = sqlite3.connect('database/database.db')
cursor = conn.cursor()

# Buscar ordem 9
cursor.execute('''
    SELECT servicos_dados, produtos_dados, parcelas_json, anexos_dados
    FROM ordens_servico 
    WHERE id = 9
''')

resultado = cursor.fetchone()

if resultado:
    servicos_dados, produtos_dados, parcelas_json, anexos_dados = resultado
    
    print(f"[INFO] Dados da ordem 9:")
    print(f"  Servicos_dados: {servicos_dados}")
    print(f"  Produtos_dados: {produtos_dados}")
    print(f"  Parcelas_json: {parcelas_json}")
    print(f"  Anexos_dados: {anexos_dados}")
    
    print(f"\n[VALIDACAO JSON]")
    
    # Testar cada campo
    if servicos_dados:
        try:
            s = json.loads(servicos_dados)
            print(f"  Servicos: OK - {len(s)} itens")
        except Exception as e:
            print(f"  Servicos: ERRO - {e}")
    else:
        print(f"  Servicos: VAZIO")
    
    if produtos_dados:
        try:
            p = json.loads(produtos_dados)
            print(f"  Produtos: OK - {len(p)} itens")
        except Exception as e:
            print(f"  Produtos: ERRO - {e}")
    else:
        print(f"  Produtos: VAZIO")
    
    if parcelas_json:
        try:
            par = json.loads(parcelas_json)
            print(f"  Parcelas: OK - {len(par)} itens")
        except Exception as e:
            print(f"  Parcelas: ERRO - {e}")
    else:
        print(f"  Parcelas: VAZIO")
    
    if anexos_dados:
        try:
            a = json.loads(anexos_dados)
            print(f"  Anexos: OK - {len(a)} itens")
        except Exception as e:
            print(f"  Anexos: ERRO - {e}")
    else:
        print(f"  Anexos: VAZIO")
else:
    print("[ERRO] Ordem 9 não encontrada")

conn.close()
print("\n=== FIM ANALISE ===")