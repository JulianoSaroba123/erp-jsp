#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🧹 Limpeza Final - Últimos Arquivos Desnecessários
Remove os últimos vestígios de arquivos antigos e temporários
"""

import os
import shutil

def calcular_tamanho_arquivo(filepath):
    """Calcula tamanho do arquivo em bytes"""
    try:
        return os.path.getsize(filepath)
    except:
        return 0

def remover_arquivo_seguro(filepath, motivo=""):
    """Remove arquivo de forma segura com log"""
    try:
        if os.path.exists(filepath):
            tamanho = calcular_tamanho_arquivo(filepath)
            os.remove(filepath)
            print(f"  ✅ Removido: {os.path.basename(filepath)} ({tamanho} bytes)")
            return True, tamanho
    except Exception as e:
        print(f"  ❌ Erro: {filepath} - {str(e)}")
        return False, 0

def remover_pasta_segura(dirpath, motivo=""):
    """Remove pasta de forma segura"""
    try:
        if os.path.exists(dirpath) and os.path.isdir(dirpath):
            # Calcular tamanho total
            tamanho_total = 0
            for root, dirs, files in os.walk(dirpath):
                for file in files:
                    tamanho_total += calcular_tamanho_arquivo(os.path.join(root, file))
            
            shutil.rmtree(dirpath)
            print(f"  ✅ Pasta removida: {dirpath} ({tamanho_total} bytes)")
            return True, tamanho_total
    except Exception as e:
        print(f"  ❌ Erro pasta: {dirpath} - {str(e)}")
        return False, 0

def limpeza_final():
    """Remove últimos arquivos desnecessários"""
    print("🧹 LIMPEZA FINAL - ÚLTIMOS ARQUIVOS DESNECESSÁRIOS")
    print("=" * 60)
    
    total_removidos = 0
    espaco_liberado = 0
    
    # 1. ARQUIVOS DE CRIAÇÃO/EXEMPLO (já executados)
    print("📝 Removendo arquivos de criação e exemplo...")
    arquivos_criacao = [
        "create_test_ordem.py",
        "create_test_order.py", 
        "criar_admin.py",
        "criar_ordem_com_novos_campos.py",
        "criar_os_exemplo.py",
        "criar_os_teste_js.py",
        "criar_propostas_exemplo.py",
        "criar_sistema_auth.py",
        "criar_tabelas_novo_os.py",
        "criar_tabela_fornecedores_completa.py",
        "criar_template_pdf.py",
        "criar_todas_tabelas_ordem_servico.py",
        "scripts/criar_dados_exemplo.py",
        "scripts/criar_tabelas_proposta.py",
        "scripts/criar_todas_tabelas.py"
    ]
    
    for arquivo in arquivos_criacao:
        if os.path.exists(arquivo):
            sucesso, tamanho = remover_arquivo_seguro(arquivo, "Arquivo de criação/exemplo")
            if sucesso:
                total_removidos += 1
                espaco_liberado += tamanho
    
    # 2. UTILITÁRIOS DIVERSOS
    print("\n🔧 Removendo utilitários diversos...")
    utilitarios = [
        "ativar_cliente.py",
        "checkup_final_os.py", 
        "configurar_banco_correto.py",
        "configurar_logo.py",
        "diagnose_buttons.py",
        "find_proposta_db.py",
        "gerar_pdf_novo.py",
        "inserir_dados_config.py",
        "list_all_clients.py",
        "list_db_tables.py",
        "move_item_to_service.py",
        "resetar_senha_admin.py",
        "restaurar_dados_completos.py",
        "rotas_extras.py"
    ]
    
    for arquivo in utilitarios:
        if os.path.exists(arquivo):
            sucesso, tamanho = remover_arquivo_seguro(arquivo, "Utilitário")
            if sucesso:
                total_removidos += 1
                espaco_liberado += tamanho
    
    # 3. ARQUIVOS HTML/JS TEMPORÁRIOS
    print("\n🌐 Removendo arquivos temporários web...")
    temporarios_web = [
        "debug_pdf_content.html",
        "fix_form_complete.html", 
        "pdf_html_proposta_1.html",
        "fix_calculos.js"  # Se não está sendo usado
    ]
    
    for arquivo in temporarios_web:
        if os.path.exists(arquivo):
            sucesso, tamanho = remover_arquivo_seguro(arquivo, "Temporário web")
            if sucesso:
                total_removidos += 1
                espaco_liberado += tamanho
    
    # 4. EXECUTÁVEL ANTIGO
    print("\n💿 Removendo executável antigo...")
    if os.path.exists("ERP_JSP_PERFEITO.exe"):
        sucesso, tamanho = remover_arquivo_seguro("ERP_JSP_PERFEITO.exe", "Executável antigo")
        if sucesso:
            total_removidos += 1
            espaco_liberado += tamanho
    
    # 5. PASTA FINAL_WORKING (se vazia ou desnecessária)
    print("\n📁 Verificando pasta final_working...")
    if os.path.exists("final_working"):
        try:
            # Verificar se tem conteúdo importante
            items = os.listdir("final_working")
            if not items or all(item.startswith('.') for item in items):
                sucesso, tamanho = remover_pasta_segura("final_working", "Pasta vazia/temporária")
                if sucesso:
                    espaco_liberado += tamanho
        except:
            pass
    
    # 6. CACHE PYTHON
    print("\n🗑️ Limpando cache Python...")
    if os.path.exists("__pycache__"):
        sucesso, tamanho = remover_pasta_segura("__pycache__", "Cache Python")
        if sucesso:
            espaco_liberado += tamanho
    
    # 7. SCRIPTS DE LIMPEZA (após usar)
    print("\n🧹 Removendo scripts de limpeza...")
    scripts_limpeza = [
        "limpador_automatico.py",
        "segunda_limpeza.py",
        "limpeza_avancada_direta.py"  # Se existir
    ]
    
    for arquivo in scripts_limpeza:
        if os.path.exists(arquivo) and arquivo != "limpeza_final.py":  # Não remover a si mesmo
            sucesso, tamanho = remover_arquivo_seguro(arquivo, "Script de limpeza")
            if sucesso:
                total_removidos += 1
                espaco_liberado += tamanho
    
    # 8. VERIFICAR LOGS ANTIGOS (manter estrutura mas limpar conteúdo antigo se muito grande)
    print("\n📄 Verificando logs...")
    if os.path.exists("logs"):
        try:
            for log_file in os.listdir("logs"):
                log_path = os.path.join("logs", log_file)
                if os.path.isfile(log_path):
                    tamanho = calcular_tamanho_arquivo(log_path)
                    # Se log muito grande (>1MB), truncar mas manter arquivo
                    if tamanho > 1024 * 1024:
                        with open(log_path, 'w') as f:
                            f.write(f"# Log truncado em limpeza final\n")
                        print(f"  📝 Log truncado: {log_file} ({tamanho} -> pequeno)")
                        espaco_liberado += tamanho - 50
        except:
            pass
    
    # RELATÓRIO FINAL
    print("\n" + "=" * 60)
    print("📊 RELATÓRIO DA LIMPEZA FINAL")
    print("=" * 60)
    print(f"📁 Arquivos removidos: {total_removidos}")
    print(f"💾 Espaço liberado: {espaco_liberado / 1024:.2f} KB")
    print("✅ LIMPEZA FINAL CONCLUÍDA!")
    print("\n🎯 PROJETO AGORA ESTÁ TOTALMENTE LIMPO E OTIMIZADO!")
    
    return total_removidos, espaco_liberado

if __name__ == "__main__":
    try:
        total, espaco = limpeza_final()
        print(f"\n🎉 LIMPEZA FINAL: {total} arquivos removidos!")
        print(f"💾 Espaço final liberado: {espaco/1024:.2f} KB")
        print("\n🚀 WORKSPACE 100% OTIMIZADO!")
    except Exception as e:
        print(f"\n❌ ERRO: {str(e)}")