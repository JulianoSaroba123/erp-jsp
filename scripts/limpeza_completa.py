#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para fazer limpeza completa do arquivo proposta_routes.py
"""

import os
import re

def limpeza_completa():
    """Remove todo código CSS duplicado do arquivo"""
    
    arquivo = 'C:/ERP_JSP/app/proposta/proposta_routes.py'
    
    print(f"Fazendo limpeza completa de {arquivo}...")
    
    try:
        with open(arquivo, 'r', encoding='utf-8') as f:
            conteudo = f.read()
        
        # Encontrar onde termina a função gerar_pdf_proposta
        pos_funcao_pdf = conteudo.find('    except Exception as e:\n        return f"<h1>Erro ao gerar PDF</h1><p>Erro: {str(e)}</p>", 500')
        
        if pos_funcao_pdf == -1:
            print("❌ Não encontrou o final da função PDF")
            return
        
        pos_fim_pdf = pos_funcao_pdf + len('    except Exception as e:\n        return f"<h1>Erro ao gerar PDF</h1><p>Erro: {str(e)}</p>", 500')
        
        # Encontrar a próxima função válida que não seja CSS lixo
        # Procurar por qualquer def que não seja problemática
        resto_arquivo = conteudo[pos_fim_pdf:]
        
        # Encontrar a primeira linha que começa com 'def ' (função Python)
        linhas_resto = resto_arquivo.split('\n')
        pos_proxima_funcao = -1
        
        for i, linha in enumerate(linhas_resto):
            if linha.strip().startswith('def ') and not any(x in linha for x in ['{{', '}}', 'font-size', 'margin', 'padding']):
                pos_proxima_funcao = i
                break
        
        if pos_proxima_funcao == -1:
            # Tentar encontrar padrão de função válida manualmente
            patterns = [
                'def gerar_pdf_reportlab',
                'def gerar_html_para_impressao',
                '@proposta_bp.route'
            ]
            
            for pattern in patterns:
                pos = resto_arquivo.find(pattern)
                if pos != -1:
                    # Contar newlines até essa posição
                    pos_proxima_funcao = resto_arquivo[:pos].count('\n')
                    break
        
        if pos_proxima_funcao == -1:
            print("❌ Não foi possível encontrar próxima função válida")
            return
        
        # Reconstruir arquivo limpo
        parte_antes = conteudo[:pos_fim_pdf]
        parte_depois = '\n'.join(linhas_resto[pos_proxima_funcao:])
        
        conteudo_limpo = parte_antes + '\n\n' + parte_depois
        
        # Salvar arquivo limpo
        with open(arquivo, 'w', encoding='utf-8') as f:
            f.write(conteudo_limpo)
            
        print("✅ Limpeza completa realizada com sucesso!")
        print(f"Função PDF termina na posição {pos_fim_pdf}")
        print(f"Próxima função encontrada na linha {pos_proxima_funcao}")
        
    except Exception as e:
        print(f"❌ Erro: {e}")

if __name__ == "__main__":
    limpeza_completa()