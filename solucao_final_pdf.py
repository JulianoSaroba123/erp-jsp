#!/usr/bin/env python3
"""
SOLUÇÃO FINAL - Script para corrigir TODAS as ordens para gerar PDFs completos
Execução: python solucao_final_pdf.py
"""
import sqlite3
import json

def corrigir_todas_ordens():
    print("=== SOLUÇÃO FINAL PARA PDFs COMPLETOS ===\n")
    
    conn = sqlite3.connect('database/database.db')
    cursor = conn.cursor()
    
    # Buscar todas as ordens
    cursor.execute("""
        SELECT id, codigo, servicos_dados, produtos_dados, valor_total, 
               descricao_servico_realizado, equipamento_problema, status
        FROM ordens_servico 
        ORDER BY id
    """)
    orders = cursor.fetchall()
    
    ordens_corrigidas = 0
    
    for order in orders:
        id_, codigo, servicos, produtos, valor_total, descricao, problema, status = order
        print(f"Processando {codigo}...")
        
        dados_corretos = False
        
        # Verificar se já tem serviços válidos
        try:
            if servicos and len(servicos) > 2:
                servicos_data = json.loads(servicos)
                valid_servicos = [s for s in servicos_data if s and s.get('descricao') and s.get('valor_unitario')]
                if valid_servicos:
                    dados_corretos = True
                    print(f"  ✓ Já tem {len(valid_servicos)} serviços válidos")
        except:
            pass
        
        # Se não tem dados válidos, criar dados padrão
        if not dados_corretos:
            # Usar valor_total da ordem para criar serviço
            if valor_total and valor_total > 0:
                servico_descricao = descricao or problema or "Serviço técnico realizado"
                
                servico_padrao = [{
                    'id': '1',
                    'descricao': servico_descricao[:100],  # Limitar tamanho
                    'quantidade': 1,
                    'valor_unitario': float(valor_total),
                    'valor_total': float(valor_total)
                }]
                
                servicos_json = json.dumps(servico_padrao, ensure_ascii=False)
                cursor.execute("UPDATE ordens_servico SET servicos_dados = ? WHERE id = ?", 
                             (servicos_json, id_))
                
                # Se tem parcelas vazias, criar parcela única
                cursor.execute("SELECT parcelas_json FROM ordens_servico WHERE id = ?", (id_,))
                parcelas_result = cursor.fetchone()
                if parcelas_result and (not parcelas_result[0] or parcelas_result[0] == '[]'):
                    parcela_padrao = [{
                        'numero': 1,
                        'valor': float(valor_total),
                        'data_vencimento': '2025-10-30',
                        'status': 'Pendente' if status != 'Concluída' else 'Pago'
                    }]
                    parcelas_json = json.dumps(parcela_padrao, ensure_ascii=False)
                    cursor.execute("UPDATE ordens_servico SET parcelas_json = ? WHERE id = ?", 
                                 (parcelas_json, id_))
                
                ordens_corrigidas += 1
                print(f"  ✓ Corrigida com serviço padrão: R$ {valor_total}")
            else:
                print(f"  ⚠ Sem valor_total para corrigir")
        
        print()
    
    conn.commit()
    conn.close()
    
    print(f"=== RESULTADO FINAL ===")
    print(f"✓ Ordens corrigidas: {ordens_corrigidas}/{len(orders)}")
    print(f"\n📋 COMO GERAR PDFs COMPLETOS:")
    print(f"   1. Acesse: http://localhost:5000/ordens")
    print(f"   2. Na lista de ordens, clique no botão PDF de qualquer ordem")
    print(f"   3. URL do PDF: http://localhost:5000/ordens/<ID>/pdf")
    print(f"   4. Exemplo: http://localhost:5000/ordens/2/pdf")
    print(f"\n🎯 ORDENS PRONTAS PARA PDF:")
    
    # Listar ordens que devem funcionar
    cursor = conn.cursor()
    cursor.execute("SELECT id, codigo FROM ordens_servico WHERE servicos_dados IS NOT NULL AND LENGTH(servicos_dados) > 10")
    ordens_prontas = cursor.fetchall()
    for id_, codigo in ordens_prontas:
        print(f"   - {codigo} (ID {id_}): http://localhost:5000/ordens/{id_}/pdf")
    
    conn.close()

if __name__ == "__main__":
    corrigir_todas_ordens()