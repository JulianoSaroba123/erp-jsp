# -*- coding: utf-8 -*-
"""
Diagnóstico de Anexos - Verificar caminhos e existência dos arquivos
"""

import os
import sys

# Adiciona o diretório raiz ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.app import create_app
from app.extensoes import db
from app.ordem_servico.ordem_servico_model import OrdemServicoAnexo, OrdemServico

app = create_app()

with app.app_context():
    print("=" * 80)
    print("🔍 DIAGNÓSTICO DE ANEXOS")
    print("=" * 80)
    
    # Busca todos os anexos
    anexos = OrdemServicoAnexo.query.all()
    
    if not anexos:
        print("⚠️  Nenhum anexo encontrado no banco de dados!")
    else:
        print(f"\n📊 Total de anexos no banco: {len(anexos)}\n")
        
        for i, anexo in enumerate(anexos, 1):
            ordem = OrdemServico.query.get(anexo.ordem_servico_id)
            print(f"\n{'─' * 80}")
            print(f"📄 Anexo #{i}: {anexo.nome_original}")
            print(f"   🆔 ID: {anexo.id}")
            print(f"   📋 OS: #{ordem.numero if ordem else 'N/A'}")
            print(f"   📝 Nome arquivo: {anexo.nome_arquivo}")
            print(f"   🎨 Tipo: {anexo.tipo_arquivo}")
            print(f"   📦 MIME: {anexo.mime_type}")
            print(f"   💾 Tamanho: {anexo.tamanho_formatado}")
            print(f"   📁 Caminho salvo: {anexo.caminho}")
            
            # Verifica se o arquivo existe
            if os.path.exists(anexo.caminho):
                print(f"   ✅ Arquivo EXISTE no caminho salvo")
                # Verifica se é realmente uma imagem
                if anexo.tipo_arquivo == 'image':
                    tamanho_real = os.path.getsize(anexo.caminho)
                    print(f"   📏 Tamanho real: {tamanho_real} bytes")
            else:
                print(f"   ❌ Arquivo NÃO EXISTE no caminho salvo!")
                
                # Tenta caminhos alternativos
                print(f"\n   🔍 Procurando em caminhos alternativos:")
                
                base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                possible_paths = [
                    os.path.join(base_dir, 'uploads', 'ordem_servico', 'anexos', anexo.nome_arquivo),
                    os.path.join(base_dir, 'app', 'static', 'uploads', 'ordem_servico', anexo.nome_arquivo),
                    os.path.join(os.getcwd(), 'uploads', 'ordem_servico', 'anexos', anexo.nome_arquivo),
                ]
                
                for caminho_teste in possible_paths:
                    if os.path.exists(caminho_teste):
                        print(f"      ✅ ENCONTRADO: {caminho_teste}")
                        print(f"         📏 Tamanho: {os.path.getsize(caminho_teste)} bytes")
                    else:
                        print(f"      ❌ Não existe: {caminho_teste}")
        
        print(f"\n{'=' * 80}")
        print(f"📊 Resumo:")
        print(f"   Total de anexos: {len(anexos)}")
        print(f"   Imagens: {sum(1 for a in anexos if a.tipo_arquivo == 'image')}")
        print(f"   Documentos: {sum(1 for a in anexos if a.tipo_arquivo == 'document')}")
        print("=" * 80)
