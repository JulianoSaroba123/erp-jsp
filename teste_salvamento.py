#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Teste de salvamento de proposta
"""

import requests

def testar_salvamento_proposta():
    """Testa o salvamento de uma proposta com produtos e serviços."""
    
    # URL da proposta para editar
    url = 'http://192.168.0.109:5001/propostas/2/editar'
    
    # Dados do formulário
    dados = {
        'titulo': 'PROPOSTA TESTE - DADOS PRESERVADOS',
        'cliente_id': '1',
        'descricao': 'Teste de preservação de dados',
        'status': 'pendente',
        'vendedor': 'Teste Vendedor',
        'forma_pagamento': 'a_vista',
        'prazo_execucao': '30 dias',
        'garantia': '12 meses',
        'validade': '30',
        'observacoes': 'Teste de preservação',
        'condicoes_pagamento': 'À vista',
        'desconto': '5',
        'data_emissao': '2025-10-15',
        
        # Produtos
        'produto_descricao[]': [
            'Produto 1 - Preservado',
            'Produto 2 - Preservado',
            'Produto 3 - Novo'
        ],
        'produto_quantidade[]': [
            '2,000',
            '1,000', 
            '5,000'
        ],
        'produto_valor[]': [
            '100,00',
            '250,00',
            '50,00'
        ],
        
        # Serviços
        'servico_descricao[]': [
            'Serviço 1 - Preservado',
            'Serviço 2 - Novo'
        ],
        'servico_quantidade[]': [
            '1,000',
            '2,000'
        ],
        'servico_valor[]': [
            '500,00',
            '300,00'
        ]
    }
    
    print("🔄 Enviando dados para salvamento...")
    print(f"📦 Produtos: {len(dados['produto_descricao[]'])}")
    print(f"🔧 Serviços: {len(dados['servico_descricao[]'])}")
    
    try:
        # Enviar POST
        response = requests.post(url, data=dados, timeout=15, allow_redirects=False)
        
        print(f"📤 Status da resposta: {response.status_code}")
        
        if response.status_code in [200, 302]:
            print("✅ Salvamento executado com sucesso!")
            
            # Verificar dados no banco
            print("\n🔍 Verificando dados salvos no banco...")
            
            import sqlite3
            conn = sqlite3.connect('instance/erp.db')
            cursor = conn.cursor()
            
            # Verificar produtos
            cursor.execute('''
                SELECT descricao, quantidade, valor_unitario, valor_total 
                FROM proposta_produto 
                WHERE proposta_id = 2 AND ativo = 1
                ORDER BY id
            ''')
            produtos = cursor.fetchall()
            
            print(f"\n📦 PRODUTOS SALVOS ({len(produtos)}):")
            for i, p in enumerate(produtos, 1):
                print(f"  {i}. {p[0]}")
                print(f"     Qtd: {p[1]} x R$ {p[2]} = R$ {p[3]}")
            
            # Verificar serviços
            cursor.execute('''
                SELECT descricao, quantidade, valor_unitario, valor_total 
                FROM proposta_servico 
                WHERE proposta_id = 2 AND ativo = 1
                ORDER BY id
            ''')
            servicos = cursor.fetchall()
            
            print(f"\n🔧 SERVIÇOS SALVOS ({len(servicos)}):")
            for i, s in enumerate(servicos, 1):
                print(f"  {i}. {s[0]}")
                print(f"     Qtd: {s[1]} x R$ {s[2]} = R$ {s[3]}")
            
            # Verificar totais da proposta
            cursor.execute('''
                SELECT valor_produtos, valor_servicos, valor_total, desconto
                FROM propostas 
                WHERE id = 2
            ''')
            valores = cursor.fetchone()
            
            if valores:
                print(f"\n💰 VALORES DA PROPOSTA:")
                print(f"  Produtos: R$ {valores[0]}")
                print(f"  Serviços: R$ {valores[1]}")
                print(f"  Desconto: {valores[3]}%")
                print(f"  TOTAL: R$ {valores[2]}")
            
            conn.close()
            
            if len(produtos) > 0 and len(servicos) > 0:
                print("\n🎉 SUCESSO! Todos os dados foram preservados.")
                return True
            else:
                print("\n❌ ERRO! Dados não foram salvos corretamente.")
                return False
        else:
            print(f"❌ Erro no salvamento: {response.status_code}")
            print(f"Resposta: {response.text[:200]}")
            return False
            
    except Exception as e:
        print(f"❌ Erro na requisição: {e}")
        return False

if __name__ == "__main__":
    testar_salvamento_proposta()