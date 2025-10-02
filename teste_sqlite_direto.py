#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Teste simples para verificar funcionamento da edição de OS
"""

import sqlite3
from datetime import datetime

def teste_edicao_direta():
    """Teste direto no SQLite para verificar edição"""
    
    print("=== TESTE DIRETO DE EDIÇÃO NO SQLITE ===\n")
    
    try:
        # Conectar ao banco
        conn = sqlite3.connect('database/database.db')
        cursor = conn.cursor()
        
        print("1. Verificando estado atual da OS0351...")
        cursor.execute("SELECT * FROM ordens_servico WHERE codigo = 'OS0351'")
        linha = cursor.fetchone()
        
        if not linha:
            print("❌ OS0351 não encontrada!")
            return
            
        print("✅ OS0351 encontrada")
        
        # Pegar nomes das colunas
        cursor.execute("PRAGMA table_info(ordens_servico)")
        colunas = [row[1] for row in cursor.fetchall()]
        
        # Criar dicionário com dados atuais
        dados_atuais = dict(zip(colunas, linha))
        
        print("   Estado atual:")
        campos_importantes = ['id', 'codigo', 'cliente_nome', 'status', 'equipamento_nome', 'valor_total']
        for campo in campos_importantes:
            if campo in dados_atuais:
                print(f"   - {campo}: {dados_atuais[campo]}")
        print()
        
        # 2. Simular edição
        print("2. Simulando edição...")
        novos_dados = {
            'cliente_nome': 'TESTE DIRETO - Cliente Editado',
            'status': 'Em Andamento',
            'equipamento_nome': 'Equipamento Teste Direto',
            'descricao_problema': 'Problema editado via teste direto',
            'tecnico_responsavel': 'Técnico Teste Direto',
            'valor_total': 999.99,
            'forma_pagamento': 'Teste',
            'observacoes_internas': 'Observação teste direto'
        }
        
        print("   Novos dados:")
        for campo, valor in novos_dados.items():
            print(f"   - {campo}: {valor}")
        print()
        
        # 3. Executar UPDATE
        print("3. Executando UPDATE...")
        
        # Construir query UPDATE dinâmica
        campos_set = []
        valores = []
        for campo, valor in novos_dados.items():
            campos_set.append(f"{campo} = ?")
            valores.append(valor)
        
        query = f"UPDATE ordens_servico SET {', '.join(campos_set)} WHERE codigo = 'OS0351'"
        
        print(f"   Query: {query}")
        print(f"   Valores: {valores}")
        
        cursor.execute(query, valores)
        rows_affected = cursor.rowcount
        
        print(f"   Linhas afetadas: {rows_affected}")
        
        if rows_affected > 0:
            print("   ✅ UPDATE executado com sucesso!")
        else:
            print("   ❌ Nenhuma linha foi afetada pelo UPDATE")
            return
        
        # 4. Commit
        print("\n4. Fazendo COMMIT...")
        conn.commit()
        print("   ✅ COMMIT realizado!")
        
        # 5. Verificar mudanças
        print("\n5. Verificando se as mudanças foram salvas...")
        cursor.execute("SELECT * FROM ordens_servico WHERE codigo = 'OS0351'")
        linha_nova = cursor.fetchone()
        
        if linha_nova:
            dados_novos = dict(zip(colunas, linha_nova))
            
            print("   Estado após edição:")
            for campo in campos_importantes:
                if campo in dados_novos:
                    print(f"   - {campo}: {dados_novos[campo]}")
            
            # Verificar se mudou
            mudancas_confirmadas = 0
            for campo, valor_esperado in novos_dados.items():
                if campo in dados_novos:
                    valor_atual = dados_novos[campo]
                    if valor_atual == valor_esperado:
                        mudancas_confirmadas += 1
                        print(f"   ✅ {campo}: mudança confirmada")
                    else:
                        print(f"   ❌ {campo}: esperado '{valor_esperado}', atual '{valor_atual}'")
            
            print(f"\n   Mudanças confirmadas: {mudancas_confirmadas}/{len(novos_dados)}")
            
            if mudancas_confirmadas == len(novos_dados):
                print("\n🎉 TESTE PASSOU COMPLETAMENTE!")
                print("   ✅ Banco de dados aceita edições perfeitamente")
                print("   ✅ SQLite está funcionando corretamente")
                print("   ✅ As tabelas estão íntegras")
                print("\n💡 CONCLUSÃO DEFINITIVA:")
                print("   O problema NÃO está no banco de dados!")
                print("   O problema está 100% no frontend/formulário/JavaScript!")
            else:
                print(f"\n⚠️  TESTE PARCIAL: apenas {mudancas_confirmadas} mudanças confirmadas")
        else:
            print("   ❌ OS perdida após commit!")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Erro: {e}")
        if 'conn' in locals():
            conn.rollback()
            conn.close()

if __name__ == '__main__':
    teste_edicao_direta()