"""
Script para testar upload de datasheet (PDFs e imagens) no módulo de energia solar
"""
import os
import sys

# Verificar se a pasta de uploads existe
upload_folder = os.path.join('app', 'static', 'uploads', 'datasheets')
print(f"📁 Pasta de uploads: {upload_folder}")

if os.path.exists(upload_folder):
    print(f"✅ Pasta existe!")
    arquivos = os.listdir(upload_folder)
    if arquivos:
        print(f"📄 Arquivos encontrados ({len(arquivos)}):")
        for arq in arquivos:
            caminho = os.path.join(upload_folder, arq)
            tamanho = os.path.getsize(caminho)
            print(f"  - {arq} ({tamanho:,} bytes)")
    else:
        print("📭 Pasta vazia")
else:
    print(f"❌ Pasta NÃO existe. Criando...")
    os.makedirs(upload_folder, exist_ok=True)
    print(f"✅ Pasta criada!")

# Verificar permissões
if os.access(upload_folder, os.W_OK):
    print(f"✅ Permissão de escrita OK")
else:
    print(f"❌ SEM permissão de escrita!")

print("\n" + "="*60)
print("📋 INSTRUÇÕES PARA TESTAR:")
print("="*60)
print("1. Execute: python run.py")
print("2. Acesse: http://localhost:5000/energia-solar/placas")
print("3. Clique em 'Nova Placa'")
print("4. Preencha os dados e na aba 'Upload Arquivo', escolha um PDF ou imagem")
print("5. Salve e verifique se o botão 'Ver Datasheet' aparece no card")
print("\n✅ Sistema pronto para receber uploads!")
