"""
Script para testar o upload de logo na configuração
Verifica se a logo está sendo salva corretamente em ambos os campos
"""

import os
import sys

# Adicionar o diretório raiz ao path
sys.path.insert(0, os.path.dirname(__file__))

from app.app import create_app
from app.extensoes import db
from app.configuracao.configuracao_model import Configuracao

def testar_logo():
    app = create_app()
    
    with app.app_context():
        print("=" * 60)
        print("🔍 TESTE DE LOGO - CONFIGURAÇÃO")
        print("=" * 60)
        
        # Buscar configuração
        config = Configuracao.get_solo()
        
        print(f"\n📋 Dados atuais da logo:")
        print(f"   ID: {config.id}")
        print(f"   Nome Fantasia: {config.nome_fantasia}")
        print(f"   Logo (caminho): {config.logo}")
        
        if config.logo_base64:
            tamanho_base64 = len(config.logo_base64)
            print(f"   Logo Base64: {'❌ VAZIO' if not config.logo_base64 else f'✅ PRESENTE ({tamanho_base64:,} caracteres)'}")
            
            # Mostra os primeiros 100 caracteres
            if config.logo_base64:
                print(f"   Primeiros 100 caracteres: {config.logo_base64[:100]}...")
        else:
            print(f"   Logo Base64: ❌ VAZIO")
        
        print(f"\n   Exibir logo em PDFs: {'✅ SIM' if config.exibir_logo_em_pdfs else '❌ NÃO'}")
        print(f"   Exibir rodapé padrão: {'✅ SIM' if config.exibir_rodape_padrao else '❌ NÃO'}")
        
        # Verificar se o arquivo existe
        if config.logo:
            if os.path.exists(config.logo):
                tamanho_arquivo = os.path.getsize(config.logo)
                print(f"\n✅ Arquivo existe: {config.logo}")
                print(f"   Tamanho: {tamanho_arquivo:,} bytes")
            else:
                print(f"\n❌ Arquivo NÃO existe: {config.logo}")
        
        print("\n" + "=" * 60)
        print("✅ TESTE CONCLUÍDO")
        print("=" * 60)
        
        print("\n📝 INSTRUÇÕES PARA FAZER UPLOAD:")
        print("   1. Acesse: http://localhost:5000/configuracao/")
        print("   2. Clique no campo 'Logotipo'")
        print("   3. Selecione uma imagem (PNG, JPG, JPEG, GIF)")
        print("   4. Clique em 'Salvar Configurações'")
        print("   5. Execute este script novamente para verificar")
        print("\n💡 DICA: Após o upload, a logo será:")
        print("   - Salva no arquivo (campo 'logo')")
        print("   - Convertida e salva em base64 (campo 'logo_base64')")
        print("   - PDFs e sistema usarão o campo base64 prioritariamente")
        print()

if __name__ == '__main__':
    testar_logo()
