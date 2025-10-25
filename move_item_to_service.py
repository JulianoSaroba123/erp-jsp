import sqlite3

conn = sqlite3.connect('C:/ERP_JSP/instance/erp.db')
cursor = conn.cursor()

print("=== ANÁLISE DO ITEM 'Manutenção Elétrica Industrial' ===")

# Encontrar o item específico
cursor.execute('''
    SELECT pp.id, pp.proposta_id, pp.descricao, pp.quantidade, pp.valor_unitario, pp.valor_total
    FROM proposta_produto pp
    WHERE pp.descricao = 'Manutenção Elétrica Industrial' AND pp.ativo = 1
''')
produto = cursor.fetchone()

if produto:
    print(f"Encontrado como PRODUTO:")
    print(f"  ID: {produto[0]}")
    print(f"  Proposta ID: {produto[1]}")
    print(f"  Descrição: {produto[2]}")
    print(f"  Quantidade: {produto[3]}")
    print(f"  Valor Unitário: R$ {produto[4]}")
    print(f"  Valor Total: R$ {produto[5]}")
    
    print("\nDESEJA MOVER PARA SERVIÇOS? (y/n)")
    resposta = input().lower()
    
    if resposta == 'y':
        # Inserir como serviço
        cursor.execute('''
            INSERT INTO proposta_servico (proposta_id, descricao, quantidade, valor_unitario, valor_total, criado_em, atualizado_em, ativo)
            VALUES (?, ?, ?, ?, ?, datetime('now'), datetime('now'), 1)
        ''', (produto[1], produto[2], produto[3], produto[4], produto[5]))
        
        # Desativar o produto
        cursor.execute('UPDATE proposta_produto SET ativo = 0 WHERE id = ?', (produto[0],))
        
        conn.commit()
        print("✅ Item movido de PRODUTOS para SERVIÇOS com sucesso!")
    else:
        print("❌ Operação cancelada.")
else:
    print("❌ Item não encontrado como produto.")

conn.close()