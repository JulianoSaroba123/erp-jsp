import sqlite3
import json

print("=== TESTE COMPLETO DE ANEXOS ===")

# Conectar ao banco
conn = sqlite3.connect('database/database.db')
cursor = conn.cursor()

# Listar todas as ordens com anexos
cursor.execute('SELECT id, anexos_dados FROM ordens_servico WHERE anexos_dados IS NOT NULL AND anexos_dados != "[]"')
ordens = cursor.fetchall()

print(f"\nEncontradas {len(ordens)} ordens com anexos:")

for ordem_id, anexos_dados in ordens:
    try:
        anexos = json.loads(anexos_dados)
        print(f"\n[*] Ordem {ordem_id}:")
        print(f"   {len(anexos)} anexo(s)")
        for i, anexo in enumerate(anexos):
            print(f"   [{i+1}] {anexo.get('nome_original', 'sem nome')}")
            print(f"       - Tamanho: {anexo.get('tamanho_formatado', 'N/A')}")
            print(f"       - Tipo (antigo): {anexo.get('tipo', 'N/A')}")
            print(f"       - Tipo (novo): {anexo.get('tipo_arquivo', 'N/A')}")
            print(f"       - Upload: {anexo.get('data_upload', 'N/A')}")
    except json.JSONDecodeError:
        print(f"   [ERRO] dados inválidos na ordem {ordem_id}")

# Verificar especificamente a ordem 9
print(f"\n=== ORDEM 9 DETALHADA ===")
cursor.execute('SELECT anexos_dados FROM ordens_servico WHERE id = 9')
resultado = cursor.fetchone()

if resultado and resultado[0]:
    try:
        anexos = json.loads(resultado[0])
        print(f"[OK] Ordem 9 tem {len(anexos)} anexo(s)")
        for anexo in anexos:
            print("[*] Anexo encontrado:")
            for campo, valor in anexo.items():
                print(f"   {campo}: {valor}")
    except json.JSONDecodeError:
        print("[ERRO] dados JSON inválidos na ordem 9")
else:
    print("[ERRO] Ordem 9 não tem anexos ou não existe")

conn.close()
print("\n=== FIM DO TESTE ===")