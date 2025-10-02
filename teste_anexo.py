import sqlite3
import json

# Conectar ao banco
conn = sqlite3.connect('database/database.db')
cursor = conn.cursor()

# Anexo de teste
anexo_teste = [{
    "nome_arquivo": "teste.pdf",
    "nome_original": "documento_teste.pdf", 
    "tamanho": 1024,
    "tamanho_formatado": "1.0KB",
    "tipo_arquivo": "application/pdf",
    "data_upload": "2025-09-29 21:00:00"
}]

# Adicionar à ordem 9
cursor.execute('UPDATE ordens_servico SET anexos_dados = ? WHERE id = ?', 
               (json.dumps(anexo_teste), 9))
conn.commit()

print("Anexo de teste adicionado à ordem 9")

# Verificar se foi salvo
cursor.execute('SELECT anexos_dados FROM ordens_servico WHERE id = 9')
resultado = cursor.fetchone()
if resultado and resultado[0]:
    anexos = json.loads(resultado[0])
    print(f"Confirmado: {len(anexos)} anexo(s) na ordem 9")
    for anexo in anexos:
        print(f"  - {anexo['nome_original']}")
else:
    print("ERRO: Anexo não foi salvo")

conn.close()