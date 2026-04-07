"""
Script para corrigir logo_base64 que não tem o prefixo data URI.
Adiciona o prefixo 'data:image/...;base64,' necessário para exibição.
"""

from app import create_app
from app.extensoes import db
from app.configuracao.configuracao_model import Configuracao

def corrigir_logo():
    app = create_app()
    
    with app.app_context():
        config = Configuracao.get_solo()
        
        if not config.logo_base64:
            print("❌ Nenhuma logo encontrada no banco de dados")
            return
        
        # Verificar se já tem o prefixo
        if config.logo_base64.startswith('data:image'):
            print("✅ Logo já está no formato correto!")
            print(f"   Prefixo: {config.logo_base64[:50]}...")
            return
        
        print(f"🔧 Corrigindo logo base64...")
        print(f"   Tamanho atual: {len(config.logo_base64)} caracteres")
        
        # Detectar formato da imagem pelo início do base64
        # PNG: iVBOR
        # JPEG: /9j/
        # GIF: R0lGOD
        
        mime_type = 'image/png'  # padrão
        
        if config.logo_base64.startswith('/9j/'):
            mime_type = 'image/jpeg'
            print("   Formato detectado: JPEG")
        elif config.logo_base64.startswith('iVBOR'):
            mime_type = 'image/png'
            print("   Formato detectado: PNG")
        elif config.logo_base64.startswith('R0lGOD'):
            mime_type = 'image/gif'
            print("   Formato detectado: GIF")
        else:
            print("   Formato não detectado, usando PNG como padrão")
        
        # Adicionar prefixo
        config.logo_base64 = f"data:{mime_type};base64,{config.logo_base64}"
        
        # Salvar
        db.session.commit()
        
        print(f"✅ Logo corrigida com sucesso!")
        print(f"   Novo prefixo: {config.logo_base64[:50]}...")
        print(f"   Tamanho final: {len(config.logo_base64)} caracteres")
        print(f"\n💡 Agora a logo deve aparecer no sidebar e nos PDFs!")

if __name__ == '__main__':
    corrigir_logo()
