"""
Script para inicializar configuração com logo padrão
Adiciona a logo JSP padrão no banco de dados
"""

import os
import sys

# Adicionar o diretório raiz ao path
sys.path.insert(0, os.path.dirname(__file__))

from app.app import create_app
from app.extensoes import db
from app.configuracao.configuracao_model import Configuracao

def inicializar_logo_padrao():
    """Inicializa a configuração com a logo padrão do JSP"""
    app = create_app()
    
    with app.app_context():
        print("=" * 70)
        print("🎨 INICIALIZAÇÃO DE LOGO PADRÃO JSP")
        print("=" * 70)
        
        # Buscar configuração
        config = Configuracao.get_solo()
        
        print(f"\n📋 Estado atual:")
        print(f"   Nome Fantasia: {config.nome_fantasia}")
        print(f"   Logo (caminho): {config.logo or '❌ Vazio'}")
        print(f"   Logo Base64: {'✅ Presente' if config.logo_base64 else '❌ Vazio'}")
        
        if config.logo_base64:
            print(f"\n⚠️  Logo já existe no sistema!")
            print(f"   Deseja substituir pela logo padrão JSP? (s/N): ", end='')
            resposta = input().strip().lower()
            if resposta != 's':
                print("   ❌ Operação cancelada")
                return
        
        print(f"\n🔄 Adicionando logo padrão JSP...")
        
        # Logo JSP padrão em base64 (mesma do painel_routes.py)
        logo_jsp_base64 = "/9j/4AAQSkZJRgABAQEBLAEsAAD/4QC8RXhpZgAASUkqAAgAAAAGABIBAwABAAAAAQAAABoBBQABAAAAVgAAABsBBQABAAAAXgAAACgBAwABAAAAAgAAABMCAwABAAAAAQAAAGmHBAABAAAAZgAAAAAAAAAsAQAAAQAAACwBAAABAAAABgAAkAcABAAAADAyMTABkQcABAAAAAECAwAAoAcABAAAADAxMDABoAMAAQAAAP//AAACoAMAAQAAALEAAAADoAMAAQAAALEAAAAAAAAA/+EOamh0dHA6Ly9ucy5hZG9iZS5jb20veGFwLzEuMC8APD94cGFja2V0IGJlZ2luPSfvu78nIGlkPSdXNU0wTXBDZWhpSHpyZVN6TlRjemtjOWQnPz4KPHg6eG1wbWV0YSB4bWxuczp4PSdhZG9iZTpuczptZXRhLyc+CjxyZGY6UkRGIHhtbG5zOnJkZj0naHR0cDovL3d3dy53My5vcmcvMTk5OS8wMi8yMi1yZGYtc3ludGF4LW5zIyc+CgogPHJkZjpEZXNjcmlwdGlvbiByZGY6YWJvdXQ9JycKICB4bWxuczpBdHRyaWI9J2h0dHA6Ly9ucy5hdHRyaWJ1dGlvbi5jb20vYWRzLzEuMC8nPgogIDxBdHRyaWI6QWRzPgogICA8cmRmOlNlcT4KICAgIDxyZGY6bGkgcmRmOnBhcnNlVHlwZT0nUmVzb3VyY2UnPgogICAgIDxBdHRyaWI6Q3JlYXRlZD4yMDI1LTA5LTA5PC9BdHRyaWI6Q3JlYXRlZD4KICAgICA8QXR0cmliOkV4dElkPjM3OTQzMTVlLTg3OTMtNDAyMS1iOWRjLWE0Mzc3MDhiOWRhZDwvQXR0cmliOkV4dElkPgogICAgIDxBdHRyaWI6RmJJZD41MjUyNjU5MTQxNzk1ODA8L0F0dHJpYjpGYklkPgogICAgIDxBdHRyaWI6VG91Y2hUeXBlPjI8L0F0dHJpYjpUb3VjaFR5cGU+CiAgICA8L3JkZjpsaT4KICAgPC9yZGY6U2VxPgogIDwvQXR0cmliOkFkcz4KIDwvcmRmOkRlc2NyaXB0aW9uPgoKIDxyZGY6RGVzY3JpcHRpb24gcmRmOmFib3V0PScnCiAgeG1sbnM6ZGM9J2h0dHA6Ly9wdXJsLm9yZy9kYy9lbGVtZW50cy8xLjEvJz4KICA8ZGM6dGl0bGU+CiAgIDxyZGY6QWx0PgogICAgPHJkZjpsaSB4bWw6bGFuZz0neC1kZWZhdWx0Jz5TZW0gbm9tZSAoMzUgeCAzNSBtbSkgKDE1IHggMTUgbW0pIC0gMTwvcmRmOmxpPgogICA8L3JkZjpBbHQ+CiAgPC9kYzp0aXRsZT4KIDwvcmRmOkRlc2NyaXB0aW9uPgoKIDxyZGY6RGVzY3JpcHRpb24gcmRmOmFib3V0PScnCiAgeG1sbnM6cGRmPSdodHRwOi8vbnMuYWRvYmUuY29tL3BkZi8xLjMvJz4KICA8cGRmOkF1dGhvcj5KdWxpYW5vIFNhcm9iYSBQZXJlaXJhPC9wZGY6QXV0aG9yPgogPC9yZGY6RGVzY3JpcHRpb24+CgogPHJkZjpEZXNjcmlwdGlvbiByZGY6YWJvdXQ9JycKICB4bWxuczp4bXA9J2h0dHA6Ly9ucy5hZG9iZS5jb20veGFwLzEuMC8nPgogIDx4bXA6Q3JlYXRvclRvb2w+Q2FudmEgKFJlbmRlcmVyKSBkb2M9REFHeWcxalZkckkgdXNlcj1VQURuYjRJODM3VSBicmFuZD1FTMOJVFJJQ0EgU0FST0JBICZhbXA7IFNPTEFSIHRlbXBsYXRlPTwveG1wOkNyZWF0b3JUb29sPgogPC9yZGY6RGVzY3JpcHRpb24+CjwvcmRmOlJERj4KPC94OnhtcG1ldGE+CiAgICAg..."
        
        # Atualizar configuração
        config.logo_base64 = logo_jsp_base64
        config.nome_fantasia = config.nome_fantasia or "JSP Elétrica Industrial & Solar"
        
        db.session.commit()
        
        print(f"✅ Logo padrão JSP adicionada!")
        print(f"   Tamanho: {len(logo_jsp_base64):,} caracteres")
        print(f"   Nome Fantasia: {config.nome_fantasia}")
        
        print("\n" + "=" * 70)
        print("✅ CONFIGURAÇÃO INICIALIZADA")
        print("=" * 70)
        print(f"\n💡 Próximos passos:")
        print(f"   1. Acesse: http://localhost:5000/configuracao/")
        print(f"   2. A logo JSP padrão agora aparece")
        print(f"   3. Se quiser, faça upload de sua própria logo")
        print(f"   4. Complete os demais dados da empresa\n")

if __name__ == '__main__':
    inicializar_logo_padrao()
