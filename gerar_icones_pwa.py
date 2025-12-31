#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gerador de Ícones PWA para ERP JSP
===================================

Gera todos os ícones necessários para o PWA a partir de uma imagem base.
Requer: Pillow (PIL)

Uso:
    python gerar_icones_pwa.py [caminho_do_logo.png]

Se não fornecer um logo, usa uma imagem placeholder com as cores do JSP.
"""

import os
import sys
from PIL import Image, ImageDraw, ImageFont

def criar_logo_placeholder(size=1024):
    """
    Cria um logo placeholder com as cores JSP Ciano se não houver logo.
    
    Args:
        size: Tamanho do logo quadrado
    Returns:
        Image: Imagem PIL do logo
    """
    # Cria imagem com gradiente
    img = Image.new('RGB', (size, size), color='#0e7490')
    draw = ImageDraw.Draw(img)
    
    # Desenha um círculo externo
    circle_margin = size // 8
    draw.ellipse(
        [circle_margin, circle_margin, size - circle_margin, size - circle_margin],
        fill='#06b6d4',
        outline='#cffafe',
        width=size // 40
    )
    
    # Desenha um círculo interno
    inner_margin = size // 4
    draw.ellipse(
        [inner_margin, inner_margin, size - inner_margin, size - inner_margin],
        fill='#0891b2',
        outline='#a5f3fc',
        width=size // 50
    )
    
    # Tenta adicionar texto
    try:
        # Tenta carregar uma fonte, senão usa a padrão
        try:
            font = ImageFont.truetype("arial.ttf", size // 6)
        except:
            font = ImageFont.load_default()
        
        text = "JSP"
        
        # Calcula posição centralizada
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        x = (size - text_width) // 2
        y = (size - text_height) // 2 - size // 20
        
        # Desenha o texto
        draw.text((x, y), text, fill='white', font=font)
        
    except Exception as e:
        print(f"⚠️ Aviso: Não foi possível adicionar texto ao logo: {e}")
    
    return img


def gerar_icones(logo_path=None):
    """
    Gera todos os ícones PWA necessários.
    
    Args:
        logo_path: Caminho para o logo original (opcional)
    """
    # Tamanhos necessários para PWA
    sizes = [72, 96, 128, 144, 152, 192, 384, 512]
    
    # Diretório de saída
    icons_dir = os.path.join('app', 'static', 'icons')
    os.makedirs(icons_dir, exist_ok=True)
    
    # Carrega ou cria o logo
    if logo_path and os.path.exists(logo_path):
        print(f"📂 Carregando logo de: {logo_path}")
        try:
            original = Image.open(logo_path)
            
            # Converte para RGBA se necessário
            if original.mode != 'RGBA':
                original = original.convert('RGBA')
            
            # Se não for quadrado, adiciona padding
            if original.size[0] != original.size[1]:
                print("⚠️ Logo não é quadrado, adicionando padding...")
                max_size = max(original.size)
                square = Image.new('RGBA', (max_size, max_size), (255, 255, 255, 0))
                offset = ((max_size - original.size[0]) // 2, (max_size - original.size[1]) // 2)
                square.paste(original, offset)
                original = square
                
        except Exception as e:
            print(f"❌ Erro ao carregar logo: {e}")
            print("📝 Criando logo placeholder...")
            original = criar_logo_placeholder()
    else:
        print("📝 Nenhum logo fornecido. Criando logo placeholder com cores JSP...")
        original = criar_logo_placeholder()
    
    print(f"\n🎨 Gerando ícones PWA...")
    print(f"📁 Diretório: {icons_dir}\n")
    
    # Gera cada tamanho
    for size in sizes:
        try:
            # Redimensiona com boa qualidade
            if hasattr(Image, 'Resampling'):
                # Pillow >= 9.1.0
                resample = Image.Resampling.LANCZOS
            else:
                # Pillow < 9.1.0
                resample = Image.LANCZOS
            
            img = original.resize((size, size), resample)
            
            # Converte para RGB se for salvar como PNG sem transparência
            # ou mantém RGBA para preservar transparência
            if img.mode == 'RGBA':
                # Cria background branco para versões sem transparência
                background = Image.new('RGB', (size, size), (255, 255, 255))
                background.paste(img, mask=img.split()[3])  # 3 é o canal alpha
                img_rgb = background
            else:
                img_rgb = img.convert('RGB')
            
            # Salva o ícone
            output_path = os.path.join(icons_dir, f'icon-{size}.png')
            img_rgb.save(output_path, 'PNG', optimize=True)
            
            # Também salva versão com transparência
            if original.mode == 'RGBA':
                output_alpha = os.path.join(icons_dir, f'icon-{size}-alpha.png')
                img.save(output_alpha, 'PNG', optimize=True)
            
            print(f"✅ Ícone {size}x{size} criado: {output_path}")
            
        except Exception as e:
            print(f"❌ Erro ao criar ícone {size}x{size}: {e}")
    
    # Cria também um favicon.ico
    try:
        favicon_sizes = [(16, 16), (32, 32), (48, 48)]
        favicon_images = []
        
        for size in favicon_sizes:
            img = original.resize(size, resample)
            if img.mode == 'RGBA':
                background = Image.new('RGB', size, (255, 255, 255))
                background.paste(img, mask=img.split()[3])
                img = background
            else:
                img = img.convert('RGB')
            favicon_images.append(img)
        
        favicon_path = os.path.join(icons_dir, 'favicon.ico')
        favicon_images[0].save(
            favicon_path,
            format='ICO',
            sizes=[(16, 16), (32, 32), (48, 48)],
            append_images=favicon_images[1:]
        )
        print(f"\n✅ Favicon criado: {favicon_path}")
        
    except Exception as e:
        print(f"\n⚠️ Aviso: Não foi possível criar favicon.ico: {e}")
    
    print(f"\n🎉 Todos os ícones foram gerados com sucesso!")
    print(f"📂 Localização: {os.path.abspath(icons_dir)}")
    print(f"\n💡 Próximos passos:")
    print(f"   1. Verifique os ícones gerados em: {icons_dir}")
    print(f"   2. Execute o app e teste a instalação do PWA")
    print(f"   3. Use Lighthouse para auditar o PWA")


def main():
    """Função principal."""
    print("="*60)
    print("🚀 Gerador de Ícones PWA - ERP JSP")
    print("="*60 + "\n")
    
    # Verifica se PIL/Pillow está instalado
    try:
        import PIL
        print(f"✅ Pillow {PIL.__version__} detectado\n")
    except ImportError:
        print("❌ Pillow não está instalado!")
        print("📦 Instale com: pip install Pillow")
        sys.exit(1)
    
    # Pega o caminho do logo dos argumentos
    logo_path = None
    if len(sys.argv) > 1:
        logo_path = sys.argv[1]
        if not os.path.exists(logo_path):
            print(f"❌ Arquivo não encontrado: {logo_path}")
            print("📝 Continuando com logo placeholder...\n")
            logo_path = None
    else:
        print("ℹ️ Uso: python gerar_icones_pwa.py [caminho_do_logo.png]")
        print("📝 Nenhum logo fornecido, usando placeholder...\n")
    
    # Gera os ícones
    gerar_icones(logo_path)


if __name__ == '__main__':
    main()
