#!/usr/bin/env python3
"""
Script para corrigir dados das ordens de serviço para gerar PDFs completos
"""
import sqlite3
import json

def corrigir_dados_ordens():
    conn = sqlite3.connect('database/database.db')
    cursor = conn.cursor()
    
    print("=== CORRIGINDO DADOS DAS ORDENS ===\n")
    
    # Buscar todas as ordens
    cursor.execute("SELECT id, codigo, servicos_dados, produtos_dados, parcelas_json FROM ordens_servico")
    orders = cursor.fetchall()
    
    ordens_corrigidas = 0
    
    for order in orders:
        id_, codigo, servicos, produtos, parcelas = order
        print(f"Processando {codigo}...")
        
        dados_corrigidos = False
        
        # Corrigir serviços
        if servicos and len(servicos) > 2:
            try:
                servicos_data = json.loads(servicos)
                servicos_corrigidos = []
                
                for servico in servicos_data:
                    if servico and isinstance(servico, dict):
                        # Normalizar campos
                        servico_corrigido = {
                            'id': servico.get('id', ''),
                            'descricao': servico.get('nome') or servico.get('descricao', ''),
                            'quantidade': servico.get('quantidade', 1),
                            'valor_unitario': servico.get('valor_unitario', 0),
                            'valor_total': servico.get('valor_total', 0)
                        }
                        
                        # Só adicionar se tem dados válidos
                        if servico_corrigido['descricao'] and servico_corrigido['valor_unitario'] > 0:
                            servicos_corrigidos.append(servico_corrigido)
                
                if servicos_corrigidos:
                    servicos_json = json.dumps(servicos_corrigidos, ensure_ascii=False)
                    cursor.execute("UPDATE ordens_servico SET servicos_dados = ? WHERE id = ?", 
                                 (servicos_json, id_))
                    dados_corrigidos = True
                    print(f"  - Corrigidos {len(servicos_corrigidos)} serviços")
                    
            except Exception as e:
                print(f"  - Erro ao corrigir serviços: {e}")
        
        # Corrigir produtos se existirem
        if produtos and len(produtos) > 2:
            try:
                produtos_data = json.loads(produtos)
                produtos_corrigidos = []
                
                for produto in produtos_data:
                    if produto and isinstance(produto, dict):
                        # Normalizar campos
                        produto_corrigido = {
                            'id': produto.get('id', ''),
                            'descricao': produto.get('nome') or produto.get('descricao', ''),
                            'quantidade': produto.get('quantidade', 1),
                            'valor_unitario': produto.get('valor_unitario') or produto.get('valor_hora', 0),
                            'valor_total': produto.get('valor_total', 0)
                        }
                        
                        # Só adicionar se tem dados válidos
                        if produto_corrigido['descricao'] and produto_corrigido['valor_unitario'] > 0:
                            produtos_corrigidos.append(produto_corrigido)
                
                if produtos_corrigidos:
                    produtos_json = json.dumps(produtos_corrigidos, ensure_ascii=False)
                    cursor.execute("UPDATE ordens_servico SET produtos_dados = ? WHERE id = ?", 
                                 (produtos_json, id_))
                    dados_corrigidos = True
                    print(f"  - Corrigidos {len(produtos_corrigidos)} produtos")
                    
            except Exception as e:
                print(f"  - Erro ao corrigir produtos: {e}")
        
        # Se não tem dados de serviços/produtos, criar dados padrão básicos
        if not dados_corrigidos:
            # Criar serviço padrão baseado no valor total da ordem
            cursor.execute("SELECT valor_total, descricao_servico_realizado FROM ordens_servico WHERE id = ?", (id_,))
            result = cursor.fetchone()
            if result:
                valor_total, descricao = result
                if valor_total and valor_total > 0:
                    servico_padrao = [{
                        'id': '1',
                        'descricao': descricao or 'Serviço realizado',
                        'quantidade': 1,
                        'valor_unitario': float(valor_total),
                        'valor_total': float(valor_total)
                    }]
                    servicos_json = json.dumps(servico_padrao, ensure_ascii=False)
                    cursor.execute("UPDATE ordens_servico SET servicos_dados = ? WHERE id = ?", 
                                 (servicos_json, id_))
                    dados_corrigidos = True
                    print(f"  - Criado serviço padrão: R$ {valor_total}")
        
        if dados_corrigidos:
            ordens_corrigidas += 1
        
        print()
    
    conn.commit()
    conn.close()
    
    print(f"=== CONCLUIDO ===")
    print(f"Ordens corrigidas: {ordens_corrigidas}/{len(orders)}")
    print(f"\nAgora teste gerar o PDF de qualquer ordem!")

if __name__ == "__main__":
    corrigir_dados_ordens()