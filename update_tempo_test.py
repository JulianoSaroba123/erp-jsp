import sqlite3

conn = sqlite3.connect('C:/ERP_JSP/instance/erp.db')
cursor = conn.cursor()

# Atualizar a proposta ID=2 para testar se o campo carrega na visualização
cursor.execute('UPDATE propostas SET tempo_estimado = ? WHERE id = ?', ('3 horas', 2))
conn.commit()

print("Proposta ID=2 atualizada com tempo_estimado = '3 horas'")

# Verificar se foi salvo
cursor.execute('SELECT id, codigo, tempo_estimado, km_estimado, prioridade FROM propostas WHERE id = 2')
proposta = cursor.fetchone()
if proposta:
    print(f'Verificação: ID: {proposta[0]}, Código: {proposta[1]}, Tempo: "{proposta[2]}", KM: {proposta[3]}, Prioridade: "{proposta[4]}"')

conn.close()