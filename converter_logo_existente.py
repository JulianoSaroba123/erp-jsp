"""
Script para converter logo existente em base64
Atualiza o campo logo_base64 a partir da logo atual
"""

import os
import sys
import base64
from io import BytesIO

# Adicionar o diretório raiz ao path
sys.path.insert(0, os.path.dirname(__file__))

from app.app import create_app
from app.extensoes import db
from app.configuracao.configuracao_model import Configuracao

try:
    from PIL import Image
except ImportError:
    print("❌ PIL/Pillow não está instalado!")
    print("   Execute: pip install Pillow")
    sys.exit(1)

def converter_logo_para_base64():
    """Converte a logo atual para base64 e salva no banco"""
    app = create_app()
    
    with app.app_context():
        print("=" * 70)
        print("🔄 CONVERSÃO DE LOGO PARA BASE64")
        print("=" * 70)
        
        # Buscar configuração
        config = Configuracao.get_solo()
        
        print(f"\n📋 Estado atual:")
        print(f"   Nome Fantasia: {config.nome_fantasia}")
        print(f"   Logo (caminho): {config.logo}")
        print(f"   Logo Base64: {'❌ VAZIO' if not config.logo_base64 else f'✅ PRESENTE ({len(config.logo_base64):,} caracteres)'}")
        
        if not config.logo:
            print("\n⚠️  AVISO: Nenhuma logo configurada!")
            print("   Vá em Configurações > Logotipo e faça upload de uma imagem")
            return
        
        # Tentar encontrar o arquivo
        possible_paths = [
            config.logo,
            os.path.join('uploads', 'configuracao', config.logo.split('/')[-1]),
            os.path.join('uploads', 'configuracao', config.logo.split('\\')[-1]),
            os.path.join(os.path.dirname(__file__), config.logo),
            os.path.join(os.path.dirname(__file__), 'uploads', 'configuracao', config.logo.split('/')[-1]),
        ]
        
        logo_path = None
        for path in possible_paths:
            if os.path.exists(path):
                logo_path = path
                break
        
        if not logo_path:
            print(f"\n❌ ERRO: Arquivo de logo não encontrado!")
            print(f"   Caminhos testados:")
            for path in possible_paths:
                print(f"      - {path}")
            print("\n💡 SOLUÇÃO: Faça upload de uma nova logo em Configurações")
            return
        
        print(f"\n✅ Arquivo encontrado: {logo_path}")
        tamanho_arquivo = os.path.getsize(logo_path)
        print(f"   Tamanho: {tamanho_arquivo:,} bytes")
        
        try:
            # Abrir e processar a imagem
            print("\n🔄 Convertendo para base64...")
            img = Image.open(logo_path)
            print(f"   Formato original: {img.format}")
            print(f"   Dimensões: {img.width}x{img.height} pixels")
            
            # Redimensionar se muito grande
            max_size = 800
            if img.width > max_size or img.height > max_size:
                print(f"   ⚠️  Imagem muito grande, redimensionando para máx {max_size}px...")
                img.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
                print(f"   Nova dimensão: {img.width}x{img.height} pixels")
            
            # Converter para base64
            buffer = BytesIO()
            img_format = img.format or 'PNG'
            img.save(buffer, format=img_format)
            img_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
            
            print(f"   ✅ Conversão concluída!")
            print(f"   Base64 gerado: {len(img_base64):,} caracteres")
            
            # Salvar no banco
            config.logo_base64 = img_base64
            db.session.commit()
            
            print(f"\n✅ SUCESSO! Logo convertida e salva no banco de dados")
            print(f"   Agora a logo aparecerá corretamente em:")
            print(f"      - Página de Configurações")
            print(f"      - PDFs de Ordens de Serviço")
            print(f"      - PDFs de Propostas")
            
        except Exception as e:
            print(f"\n❌ ERRO ao converter logo: {e}")
            import traceback
            traceback.print_exc()
            return
        
        print("\n" + "=" * 70)
        print("✅ PROCESSO CONCLUÍDO")
        print("=" * 70)
        print("\n💡 Próximo passo: Acesse http://localhost:5000/configuracao/")
        print("   A logo agora deve aparecer corretamente!\n")

if __name__ == '__main__':
    converter_logo_para_base64()
